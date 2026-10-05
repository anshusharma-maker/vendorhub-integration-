import os
import json
import pika
from dotenv import load_dotenv
from bson import ObjectId
from common.db import db
from common.api import get_token, call_api, log_api_call
from common.alerts import send_alert

load_dotenv()

def get_enum_label(teampref, form_key, storage_key, value):
    forms = teampref.get("anyCabinet", [])

    form = next(
        (form for form in forms if form.get("key") == form_key),
        None
    )

    if not form:
        raise Exception(f"Form not found: {form_key}")

    field = next(
        (
            field for field in form.get("fields", [])
            if storage_key.endswith(field.get("key", ""))
        ),
        None
    )

    if not field:
        raise Exception(f"Field not found for storage key: {storage_key}")

    for option in field.get("options", []):
        if str(option.get("id")) == str(value):
            return option.get("value")

    raise Exception(
        f"Enum option not found for field {storage_key}: {value}"
    )

def process_message(channel, method, properties, body):
    print("Message received:", body)

    message = json.loads(body)

    action_id = ObjectId(message["id"])

    actions_coll = db["actions"]
    anycabinets_coll = db["anycabinets"]
    teampref_coll = db["teampref"]

    action = actions_coll.find_one({
        "_id": action_id
    })

    if not action:
        print("Action not found:", action_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    print("Action found:", action["_id"])

    dan_id = action["resourceId"]

    dan = anycabinets_coll.find_one({
        "_id": dan_id,
        "type": "dan_request",
        "deleted": {"$ne": True}
    })

    if not dan:
        print("DAN not found:", dan_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    print("DAN found:", dan["_id"])

    teampref = teampref_coll.find_one({
        "team": dan["team"]
    })

    if not teampref:
        print("Team preferences not found:", dan["team"])
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    config = teampref["account_integration_config"]["dan_push"]


    status_field = config["status_field"]
    status_success_id = config["status_success_id"]


    current_status = dan.get("fields", {}).get(status_field)

    if current_status == status_success_id:
        print("DAN already sent:", dan["_id"])
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    payload = {}

    payload_map = config["payload_map"]

    for target_field, mapping in payload_map.items():

        if mapping.get("source") == "record_id":
            payload[target_field] = str(dan["_id"])
            continue

        storage_key = mapping["storage_key"]
        field_type = mapping["field_type"]

        value = dan.get("fields", {}).get(storage_key)

        if field_type == "string":
            payload[target_field] = value

        elif field_type == "currency":
            if value is None:
                payload[target_field] = None
            else:
                payload[target_field] = int(value.split("_")[1])

        elif field_type == "enum":
            payload[target_field] = get_enum_label(
                teampref,
                "dan_request",
                storage_key,
                value
            )

        elif field_type == "date":
            payload[target_field] = value.strftime("%d-%b-%Y")

    print("Payload:", payload)

    token = get_token(
    config["token_url"],
    config["client_id"],
    config["client_secret"]
    )

    print("VendorHub token received")

    response = call_api(
    "POST",
    config["api_url"],
    token,
    body=payload,
    retry=False
    )

    response_data = response.json()


    log_api_call(
        config["api_url"],
        response.request.headers,
        payload,
        response.status_code,
        response_data
    )

    print("VendorHub response:", response.status_code, response_data)

    if response.status_code == 200 and response_data.get("status") == "SUCCESS":
        dan_number_field = config["dan_number_field"]

        anycabinets_coll.update_one(
            {"_id": dan_id},
            {
                "$set": {
                    f"fields.{dan_number_field}": response_data["id"],
                    f"fields.{status_field}": status_success_id
                }
            }
        )
    

        print("DAN created successfully:", response_data["id"])
    
    else:
        error_message = response_data.get("message", "VendorHub request failed")

        dan_failed_id = config["status_failed_id"]

        anycabinets_coll.update_one(
            {"_id": dan_id},
            {
                "$set": {
                    f"fields.{status_field}": dan_failed_id,
                    "vendorhub_error": error_message
                }
            }
        )

        send_alert(
            f"DAN {dan_id} failed to create in VendorHub: {error_message}"
        )

        print("DAN creation failed:", error_message)

    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    host = os.getenv("RABBITMQ_HOST")
    port = int(os.getenv("RABBITMQ_PORT"))

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port
        )
    )

    channel = connection.channel()

    channel.queue_declare(
        queue="dan_push",
        durable=True
    )

    channel.basic_consume(
        queue="dan_push",
        on_message_callback=process_message,
        auto_ack=False
    )

    print("DAN consumer started. Waiting for messages...")

    channel.start_consuming()


if __name__ == "__main__":
    main()