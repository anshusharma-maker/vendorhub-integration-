def table_to_rows(table):
    if not table:
        return []

    rows = []
    row_count = len(table[0].get("value", []))

    for i in range(row_count):
        row = {}

        for column in table:
            key = column.get("key")
            values = column.get("value", [])

            if key:
                row[key] = values[i] if i < len(values) else None

        rows.append(row)

    return rows
