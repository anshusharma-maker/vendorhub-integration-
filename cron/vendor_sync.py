import os
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from common.db import db
from common.api import get_token, call_api

import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


load_dotenv()

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

logger = logging.getLogger(__name__)


def run_vendor_sync():

    teampref_coll = db["teampref"]
    anycabinets_coll = db["anycabinets"]

    
    admin_email = os.getenv("INTEGRATION_ADMIN_EMAIL")

    user_coll = db["user"]

    admin_user = user_coll.find_one({
        "email": admin_email
    })

    if not admin_user:
        raise Exception("Admin user not found")

    team_id = admin_user["team"]

    team_pref = teampref_coll.find_one({
        "team": team_id
    })

    if not team_pref:
        raise Exception("Team preferences not found")


    vendor_sync = team_pref.get(
        "account_integration_config", {}
    ).get("vendor_sync")

    if not vendor_sync:
        raise Exception("Vendor sync configuration not found")

    response_map = vendor_sync.get("response_map", {})

    any_cabinet = team_pref.get("anyCabinet", [])

    supplier_form = None

    for form in any_cabinet:
        if form.get("key") == "supplier":
            supplier_form = form
            break

    if not supplier_form:
        raise Exception("Supplier form not found")


    dropdown_options = {}

    for field in supplier_form.get("fields", []):

        group_key = field.get("group")
        field_key = field.get("key")

        if not group_key or not field_key:
            continue

        storage_key = f"{group_key}_{field_key}"

        if field.get("type") == "enum":
            options = {}

            for option in field.get("options", []):
                option_id = option.get("id")
                option_value = option.get("value")

                if option_id is not None and option_value:
                    options[str(option_id)] = option_value

            dropdown_options[storage_key] = options


    dropdown_values = {}

    for storage_key, options in dropdown_options.items():
        dropdown_values[storage_key] = {
            value: option_id
            for option_id, value in options.items()
        }


    print("Dropdown values:")
    print(dropdown_values)


    token = get_token(
        vendor_sync["token_url"],
        vendor_sync["client_id"],
        vendor_sync["client_secret"]
    )


    created = 0
    updated = 0
    skipped = 0
    failed = 0

    offset = 0
    limit = 50


    vendor_id_config = response_map.get("vendor_id")

    if not vendor_id_config:
        raise Exception("vendor_id mapping not found")

    vendor_id_storage_key = vendor_id_config["storage_key"]


    while True:

        url = f"{vendor_sync['api_url']}?offset={offset}&limit={limit}"

        response = call_api(
            "GET",
            url,
            token
        )

        data = response.json()
        vendors = data.get("items", [])


        for vendor in vendors:

            vendor_id = vendor.get("vendor_id")

            if not vendor_id:
                logger.warning(
                    "Skipping vendor because vendor_id is missing"
                )
                skipped += 1
                continue


            fields = {}


            for source_key, config in response_map.items():

                storage_key = config["storage_key"]
                field_type = config["field_type"]

                value = vendor.get(source_key)


                if field_type == "string":

                    if value is None:
                        value = ""
                    else:
                        value = value.strip()

                    fields[storage_key] = value


                elif field_type == "enum":

                    value_map = config.get("value_map", {})

                    mapped_value = value_map.get(value)

                    if mapped_value is None:
                        logger.warning(
                            "Unknown enum value '%s' for vendor %s",
                            value,
                            vendor_id
                        )
                        continue

                    option_id = dropdown_values.get(
                        storage_key,
                        {}
                    ).get(mapped_value)

                    if option_id is None:
                        logger.warning(
                            "Dropdown option '%s' not found for %s",
                            mapped_value,
                            storage_key
                        )
                        continue

                    fields[storage_key] = option_id


            try:

                existing = anycabinets_coll.find_one({
                    "team": team_id,
                    "deleted": {"$ne": True},
                    f"fields.{vendor_id_storage_key}": vendor_id
                })


                if existing:

                    update_data = {
                        f"fields.{key}": value
                        for key, value in fields.items()
                    }

                    update_data["updatedAt"] = datetime.now(timezone.utc)

                    anycabinets_coll.update_one(
                        {"_id": existing["_id"]},
                        {"$set": update_data}
                    )

                    updated += 1


                else:

                    anycabinets_coll.insert_one({
                        "team": team_id,
                        "type": "supplier",
                        "deleted": False,
                        "fields": fields,
                        "createdAt": datetime.now(timezone.utc),
                        "updatedAt": datetime.now(timezone.utc)
                    })

                    created += 1


            except Exception as e:

                failed += 1

                logger.exception(
                    "Failed to sync vendor %s: %s",
                    vendor_id,
                    e
                )


        if not data.get("hasMore"):
            break

        offset += limit


    logger.info(
        "Done. created=%s updated=%s skipped=%s failed=%s",
        created,
        updated,
        skipped,
        failed
    )


def main():

    if "--run-now" in sys.argv:
        run_vendor_sync()
        return

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        run_vendor_sync,
        CronTrigger(
            hour=0,
            minute=30,
            timezone="Asia/Kolkata"
        ),
        id="vendor_sync",
        replace_existing=True
    )

    logger.info(
        "Vendor sync scheduler started. Running daily at 00:30 IST."
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Vendor sync scheduler stopped.")


if __name__ == "__main__":
    main()