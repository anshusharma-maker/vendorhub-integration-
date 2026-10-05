import os
import json
import pika
from dotenv import load_dotenv
from bson import ObjectId

from common.db import db
from common.api import get_token, call_api, log_api_call
from common.alerts import send_alert
from common.tables import table_to_rows


load_dotenv()


def process_message(channel, method, properties, body):

    print("Message received:", body)

    message = json.loads(body)

    action_id = ObjectId(message["id"])

    actions_coll = db["actions"]
    usercases_coll = db["usercases"]
    teampref_coll = db["teampref"]


    action = actions_coll.find_one({
        "_id": action_id
    })

    if not action:
        print("Action not found:", action_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    print("Action found:", action["_id"])

    case_id = action["resourceId"]


    case = usercases_coll.find_one({
        "_id": case_id,
        "deleted": {"$ne": True}
    })

    if not case:
        print("Case not found:", case_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    print("Case found:", case["_id"])

    teampref = teampref_coll.find_one({
        "team": case["team"]
    })

    if not teampref:
        print("Team preferences not found:", case["team"])
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    config = teampref["account_integration_config"]["unit_push"]


    table_field = config["units_table_field"]

    table = case.get("customFields", {}).get(table_field)

    if not table:
        print("Units table not found:", table_field)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    rows = table_to_rows(table)

    print("Unit rows:", rows)

    token = get_token(
        config["token_url"],
        config["client_id"],
        config["client_secret"]
    )

    print("VendorHub token received")

    sent = 0
    failed = []

    payload_map = config["payload_map"]


    for line_no, row in enumerate(rows, start=1):

        payload = {}

        for target_field, column_key in payload_map.items():
            payload[target_field] = row.get(column_key)

        payload["CASE_ID"] = str(case["_id"])
        payload["LINE_NO"] = line_no

        print(f"Sending line {line_no}:")
        print("Payload:", payload)

        try:

            response = call_api(
                "POST",
                config["api_url"],
                token,
                body=payload,
                retry=True
            )

            try:
                response_data = response.json()
            except ValueError:
                response_data = {
                    "message": response.text
                }

            log_api_call(
                config["api_url"],
                response.request.headers,
                payload,
                response.status_code,
                response_data
            )

            print(
                "VendorHub response:",
                response.status_code,
                response_data
            )

            if (
                response.status_code == 200
                and response_data.get("status") == "SUCCESS"
            ):
                sent += 1
                print(f"Line {line_no} sent successfully")

            else:
                failed.append(line_no)
                print(f"Line {line_no} failed")

        except Exception as e:

            failed.append(line_no)

            print(
                f"Line {line_no} failed with exception:",
                str(e)
            )

    print(
        f"Unit push completed: sent={sent} failed={len(failed)}"
    )

    if failed:
        send_alert(
            f"Unit push failed for case {case_id}. "
            f"Failed line numbers: {failed}"
        )

    channel.basic_ack(
        delivery_tag=method.delivery_tag
    )


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
        queue="unit_push",
        durable=True
    )

    channel.basic_consume(
        queue="unit_push",
        on_message_callback=process_message,
        auto_ack=False
    )

    print("UNIT consumer started. Waiting for messages...")

    channel.start_consuming()


if __name__ == "__main__":
    main()

