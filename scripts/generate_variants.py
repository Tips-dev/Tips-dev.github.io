import csv

variants = [
    ("printable", "Printable"),
    ("pdf", "PDF"),
    ("for-beginners", "For Beginners"),
    ("packing", "Packing"),
]

rows = []

with open("checklists.csv", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        rows.append(row)

new_rows = []

for row in rows:
    for slug_suffix, title_suffix in variants:
        new_slug = f"{row['slug']}-{slug_suffix}"
        new_title = f"{row['title']} {title_suffix}"

        new_row = row.copy()
        new_row["slug"] = new_slug
        new_row["title"] = new_title

        new_rows.append(new_row)

with open("generated_checklists.csv", "w", newline="", encoding="utf-8") as file:
    fieldnames = rows[0].keys()
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(rows + new_rows)

print("Generated", len(new_rows), "new rows")
