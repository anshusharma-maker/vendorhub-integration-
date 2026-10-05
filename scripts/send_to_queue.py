import os
import json
import argparse
from datetime import datetime, timezone

import pika
from dotenv import load_dotenv
from bson import ObjectId

from common.db import db


load_dotenv()


def main():

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--dan")
    group.add_argument("--case")

    parser.add_argument("--user", required=True)

    args = parser.parse_args()

    user_id = ObjectId(args.user)

    user_coll = db["user"]
    actions_coll = db["actions"]

    if args.dan:

        resource_id = ObjectId(args.dan)

        anycabinets_coll = db["anycabinets"]

        dan = anycabinets_coll.find_one({
            "_id": resource_id,
            "type": "dan_request",
            "deleted": {"$ne": True}
        })

        if not dan:
            raise Exception("DAN not found")

        team_id = dan["team"]

        queue_name = "dan_push"

        teampref_coll = db["teampref"]

        teampref = teampref_coll.find_one({
            "team": team_id
        })

        if not teampref:
            raise Exception("Team preferences not found")

        config = teampref["account_integration_config"]["dan_push"]

        status_field = config["status_field"]


        dan_form = next(
            (
                form
                for form in teampref.get("anyCabinet", [])
                if form.get("key") == "dan_request"
            ),
            None
        )

        if not dan_form:
            raise Exception("DAN request form not found")

        status_field_config = next(
            (
                field
                for field in dan_form.get("fields", [])
                if f"{field.get('group')}_{field.get('key')}" == status_field
            ),
            None
        )

        if not status_field_config:
            raise Exception("DAN status field not found")


        submitted_option = next(
            (
                option
                for option in status_field_config.get("options", [])
                if option.get("value") == "Submitted"
            ),
            None
        )

        if not submitted_option:
            raise Exception("Submitted status option not found")

        submitted_status_id = str(submitted_option["id"])

        action = {
            "team": team_id,
            "resourceId": resource_id,
            "event": "submitted",
            "triggeredBy": user_id,
            "createdAt": datetime.now(timezone.utc)
        }

        result = actions_coll.insert_one(action)

        action_id = result.inserted_id

        print("Action created:", action_id)

        # status_field = "dan_details_3001_dan_status_3008"

        anycabinets_coll.update_one(
            {"_id": resource_id},
            {
                "$set": {
                    f"fields.{status_field}": submitted_status_id,
                    "updatedAt": datetime.now(timezone.utc)
                }
            }
        )

        print("DAN status changed to Submitted")


    else:

        resource_id = ObjectId(args.case)

        usercases_coll = db["usercases"]

        case = usercases_coll.find_one({
            "_id": resource_id,
            "deleted": {"$ne": True}
        })

        if not case:
            raise Exception("Case not found")

        team_id = case["team"]

        queue_name = "unit_push"

        action = {
            "team": team_id,
            "resourceId": resource_id,
            "event": "unit_push",
            "triggeredBy": user_id,
            "createdAt": datetime.now(timezone.utc)
        }

        result = actions_coll.insert_one(action)

        action_id = result.inserted_id

        print("Action created:", action_id)


    user = user_coll.find_one({
        "_id": user_id,
        "team": team_id
    })

    if not user:
        raise Exception("User not found")


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
        queue=queue_name,
        durable=True
    )

    message = {
        "id": str(action_id)
    }

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    connection.close()

    print(f"Message published to {queue_name}:")
    print(message)


if __name__ == "__main__":
    main()

