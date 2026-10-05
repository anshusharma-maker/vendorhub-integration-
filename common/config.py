from common.db import db

teampref_coll = db["teampref"]
def get_mapping_config(team_id,name):
    team=teampref_coll.find_one({"team":team_id})

    if not team :
        raise ValueError({f"no teampref found for team : {team_id}"})
    
    config=team.get("account_integration_config",{}).get(name)

    if not config:
        raise ValueError({f"No integration config {name} found for team {team_id}"})

    return config



def get_dropdown_options(team_id, form_key):
    team_pref = teampref_coll.find_one({"team": team_id})

    if not team_pref:
        raise ValueError(f"No teampref found for team: {team_id}")

    forms = team_pref.get("anyCabinet", [])

    form = next(
        (form for form in forms if form.get("key") == form_key),
        None
    )

    if not form:
        raise ValueError(
            f"No form '{form_key}' found for team: {team_id}"
        )

    dropdown_options = {}

    for field_group in form.get("fieldGroups", []):
        for field in field_group.get("fields", []):
            if field.get("type") != "enum":
                continue

            group = field.get("group")
            key = field.get("key")

            if not group or not key:
                continue

            storage_key = f"{group}_{key}"

            options = {}

            for option in field.get("options", []):
                option_id = option.get("id")
                option_value = option.get("value")

                if option_id is not None and option_value is not None:
                    options[str(option_id)] = option_value

            dropdown_options[storage_key] = options

    return dropdown_options
