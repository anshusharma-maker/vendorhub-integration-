from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from common.db import db, MONGODB_DB, client

load_dotenv()


team_coll = db["team"]
user_coll = db["user"]
teampref_coll = db["teampref"]
anycabinets_coll = db["anycabinets"]
usercases_coll = db["usercases"]
api_logs_coll = db["api_logs"]
alerts_coll = db["alerts"]


now = datetime.now(timezone.utc)

team = team_coll.find_one({"name": "Skyline Realty"})

if not team:
    result = team_coll.insert_one({
        "name": "Skyline Realty",
        "created_at": datetime.now(timezone.utc)
    })
    team_id = result.inserted_id
else:
    team_id = team["_id"]

print("created team:", team_id)


users = [
    {
        "team": team_id,
        "name": "Admin",
        "email": "integration.admin@skyline.test"
    },
    {
        "team": team_id,
        "name": "Snigdha",
        "email": "snig.user@skyline.test"
    },
    {
        "team": team_id,
        "name": "Anshu",
        "email": "Ans.user@skyline.test"
    }
]

for user in users:
    user_coll.update_one(
        {
            "team": team_id,
            "email": user["email"]
        },
        {
            "$set": {
                "team": team_id,
                "name": user["name"],
                "email": user["email"]
            }
        },
        upsert=True
    )


print("users created")


supplier_form = {
    "key": "supplier",
    "fieldGroups": [
        {
            "key": "vendor_details_1001",
            "displayName": "Vendor Details"
        }
    ],
    "fields": [
        {
            "group": "vendor_details_1001",
            "key": "vendor_id_2001",
            "displayName": "Vendor ID",
            "type": "string"
        },
        {
            "group": "vendor_details_1001",
            "key": "vendor_name_2002",
            "displayName": "Vendor Name",
            "type": "string"
        },
        {
            "group": "vendor_details_1001",
            "key": "vendor_status_2003",
            "displayName": "Vendor Status",
            "type": "enum",
            "options": [
                {
                    "id": 1,
                    "value": "Active"
                },
                {
                    "id": 2,
                    "value": "Inactive"
                }
            ]
        },
        {
            "group": "vendor_details_1001",
            "key": "email_2004",
            "displayName": "Email",
            "type": "string"
        }
    ]
}


dan_form = {
    "key": "dan_request",

    "fieldGroups": [
        {
            "key": "dan_details_3001",
            "displayName": "DAN Details"
        }
    ],

    "fields": [
        {
            "group": "dan_details_3001",
            "key": "vendor_id_3002",
            "displayName": "Vendor ID",
            "type": "string"
        },
        {
            "group": "dan_details_3001",
            "key": "amount_3003",
            "displayName": "Amount",
            "type": "currency"
        },
        {
            "group": "dan_details_3001",
            "key": "cost_centre_3004",
            "displayName": "Cost Centre",
            "type": "enum",
            "options": [
                {
                    "id": "1",
                    "value": "Projects"
                },
                {
                    "id": "2",
                    "value": "Legal"
                },
                {
                    "id": "3",
                    "value": "Facilities"
                }
            ]
        },
        {
            "group": "dan_details_3001",
            "key": "dan_date_3005",
            "displayName": "DAN Date",
            "type": "date"
        },
        {
            "group": "dan_details_3001",
            "key": "description_3006",
            "displayName": "Description",
            "type": "string"
        },
        {
            "group": "dan_details_3001",
            "key": "dan_number_3007",
            "displayName": "DAN Number",
            "type": "string"
        },
        {
            "group": "dan_details_3001",
            "key": "dan_status_3008",
            "displayName": "DAN Status",
            "type": "enum",
            "options": [
                {
                    "id": "1",
                    "value": "Draft"
                },
                {
                    "id": "2",
                    "value": "Submitted"
                },
                {
                    "id": "3",
                    "value": "DAN Created"
                },
                {
                    "id": "4",
                    "value": "Failed"
                }
            ]
        }
    ]
}


teampref = {
    "team": team_id,

    "anyCabinet": [
        supplier_form,
        dan_form
    ],

    "account_integration_config": {
        "vendor_sync": {
            "token_url": "http://localhost:9000/token",
            "api_url": "http://localhost:9000/vendors",
            "client_id": "pv-client",
            "client_secret": "pv-secret",

            "response_map": {
                "vendor_id": {
                    "storage_key": "vendor_details_1001_vendor_id_2001",
                    "field_type": "string"
                },
                "vendor_name": {
                    "storage_key": "vendor_details_1001_vendor_name_2002",
                    "field_type": "string"
                },
                "email_address": {
                    "storage_key": "vendor_details_1001_email_2004",
                    "field_type": "string"
                },
                "enabled_flag": {
                    "storage_key": "vendor_details_1001_vendor_status_2003",
                    "field_type": "enum",
                    "value_map": {
                        "Y": "Active",
                        "N": "Inactive"
                    }
                }
            }
        },

        "dan_push": {
            "token_url": "http://localhost:9000/token",

            "api_url": "http://localhost:9000/dan",

            "client_id": "pv-client",

            "client_secret": "pv-secret",

            "status_field":
                "dan_details_3001_dan_status_3008",

            "status_success_id": "3",

            "status_failed_id": "4",

            "dan_number_field":
                "dan_details_3001_dan_number_3007",

            "payload_map": {

                "PV_REFERENCE": {
                    "source": "record_id"
                },

                "VENDOR_ID": {
                    "storage_key":
                        "dan_details_3001_vendor_id_3002",
                    "field_type": "string"
                },

                "AMOUNT": {
                    "storage_key":
                        "dan_details_3001_amount_3003",
                    "field_type": "currency"
                },

                "COST_CENTRE": {
                    "storage_key":
                        "dan_details_3001_cost_centre_3004",
                    "field_type": "enum"
                },

                "DAN_DATE": {
                    "storage_key":
                        "dan_details_3001_dan_date_3005",
                    "field_type": "date"
                },

                "DESCRIPTION": {
                    "storage_key":
                        "dan_details_3001_description_3006",
                    "field_type": "string"
                }
            }
        },
        "unit_push": {
            "token_url": "http://localhost:9000/token",

            "api_url": "http://localhost:9000/units",

            "client_id": "pv-client",

            "client_secret": "pv-secret",

            "units_table_field": "units_table",

            "payload_map": {
                "UNIT_NO": "units_unit_no",
                "PROJECT_NAME": "units_project_name",
                "CITY": "units_city"
        }
}
    }
}


teampref_coll.update_one(
    {
        "team": team_id
    },
    {
        "$set": teampref
    },
    upsert=True
)

print("Team preferences ready")


dan_records = [
    {
        "seed_key": "dan-001",
        "vendor_id": "V001",
        "amount": "aed_12500",
        "cost_centre": "1",
        "dan_date": now,
        "description": "Office renovation payment"
    },
    {
        "seed_key": "dan-002",
        "vendor_id": "V002",
        "amount": "aed_85000",
        "cost_centre": "2",
        "dan_date": now,
        "description": "Legal Consultancy payment"
    },
    {
        "seed_key": "dan-003",
        "vendor_id": "V003",
        "amount": "aed_45000",
        "cost_centre": "3",
        "dan_date": now,
        "description": "Facilities maintenance"
    },
    {
        "seed_key": "dan-004",
        "vendor_id": "V004",
        "amount": "aed_175000",
        "cost_centre": "1",
        "dan_date": now,
        "description": "Construction project payment"
    },
    {
        "seed_key": "dan-005",
        "vendor_id": "V005",
        "amount": "aed_62000",
        "cost_centre": "2",
        "dan_date": now,
        "description": "property legal services"
    },
]


for dan in dan_records:

    document = {
        "team": team_id,
        "type": "dan_request",

        "fields": {
            "dan_details_3001_vendor_id_3002": dan["vendor_id"],
            "dan_details_3001_amount_3003": dan["amount"],
            "dan_details_3001_cost_centre_3004": dan["cost_centre"],
            "dan_details_3001_dan_date_3005": dan["dan_date"],
            "dan_details_3001_description_3006": dan["description"],

            # Empty initially.
            # VendorHub will provide this later.
            "dan_details_3001_dan_number_3007": "",

            # "Draft" = dropdown ID "1"
            "dan_details_3001_dan_status_3008": "1"
        },

        "createdAt": now,
        "updatedAt": now,
        "deleted": False,
        "seed_key": dan["seed_key"]
    }

    anycabinets_coll.update_one(
        {
            "team": team_id,
            "type": "dan_request",
            "seed_key": dan["seed_key"]
        },
        {
            "$set": document
        },
        upsert=True
    )


print("DAN requests ready")


case_records = [
    {
        "seed_key": "case-001",
        "case_name": "Skyline v ABC Holdings",
        "units": [
            {
                "key": "units_unit_no",
                "value": ["T1-1204", "T1-1205", "T1-1206"]
            },
            {
                "key": "units_project_name",
                "value": [
                    "ABC Tower",
                    "ABC Tower",
                    "ABC Tower"
                ]
            },
            {
                "key": "units_city",
                "value": [
                    "Dubai",
                    "Dubai",
                    "Dubai"
                ]
            }
        ]
    },
    {
        "seed_key": "case-002",
        "case_name": "Skyline v Gulf Properties",
        "units": [
            {
                "key": "units_unit_no",
                "value": ["T2-2101", "T2-2102", "T2-2103"]
            },
            {
                "key": "units_project_name",
                "value": [
                    "Gulf Heights",
                    "Gulf Heights",
                    "Gulf Heights"
                ]
            },
            {
                "key": "units_city",
                "value": [
                    "Dubai",
                    "Abu Dhabi",
                    "Dubai"
                ]
            }
        ]
    },
    {
        "seed_key": "case-003",
        "case_name": "Skyline v Desert Estates",
        "units": [
            {
                "key": "units_unit_no",
                "value": ["T3-3010", "T3-3011"]
            },
            {
                "key": "units_project_name",
                "value": [
                    "Desert Estates",
                    "Desert Estates"
                ]
            },
            {
                "key": "units_city",
                "value": [
                    "Sharjah",
                    "Sharjah"
                ]
            }
        ]
    }
]

for case in case_records:
    document = {
    "team": team_id,

    "caseName": case["case_name"],

    "customFields": {
        "units_table": case["units"]
    },

    "createdAt": now,
    "updatedAt": now,
    "deleted": False,

    "seed_key": case["seed_key"]
}

    usercases_coll.update_one(
        {
            "team": team_id,
            "seed_key": case["seed_key"]
        },
        {
            "$set": document
        },
        upsert=True
    )


print("Legal cases ready")


print()
print("Seed completed successfully.")
print(f"Database: {MONGODB_DB}")
print("Team: Skyline Realty")
print("Users: 3")
print("DAN requests: 5")
print("Legal cases: 3")


client.close()

