import csv, re

BASE_CSV = "checklists.csv"
OUT_CSV  = "checklists_generated.csv"

# Safe, high-intent modifiers that people actually search with
VARIANTS = [
    ("printable", "Printable"),
    ("pdf", "PDF"),
    ("free-printable", "Free Printable"),
    ("for-beginners", "For Beginners"),
    ("simple", "Simple"),
    ("ultimate", "Ultimate"),
    ("template", "Template"),
    ("packing-list", "Packing List"),
]

# Keep it clean + avoid duplicates automatically
def clean_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def vary_intro(intro: str, suffix: str) -> str:
    intro = (intro or "").strip()
    if not intro:
        intro = "Printable checklist."
    # Light variation so pages aren't identical
    if suffix == "printable":
        return intro + " Print-friendly format."
    if suffix == "pdf":
        return intro + " Easy to save and share."
    if suffix == "free-printable":
        return intro + " Free printable version."
    if suffix == "for-beginners":
        return intro + " Beginner-friendly basics."
    if suffix == "packing-list":
        return intro + " Focused on what to pack."
    if suffix == "template":
        return intro + " Use as a starting template."
    return intro

def main():
    with open(BASE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        base_rows = [{k.strip(): (v or "").strip() for k, v in r.items()} for r in reader]

    if not base_rows:
        raise SystemExit("No rows found in checklists.csv")

    fieldnames = list(base_rows[0].keys())

    seen = set()
    out_rows = []

    # Add base rows first
    for r in base_rows:
        r["slug"] = clean_slug(r.get("slug", ""))
        if not r["slug"] or not r.get("title"):
            continue
        if r["slug"] in seen:
            continue
        seen.add(r["slug"])
        out_rows.append(r)

    # Add variant rows
    for r in base_rows:
        base_slug = clean_slug(r.get("slug", ""))
        if not base_slug:
            continue

        for suffix, title_suffix in VARIANTS:
            new_slug = clean_slug(f"{base_slug}-{suffix}")
            if new_slug in seen:
                continue

            nr = dict(r)
            nr["slug"] = new_slug

            base_title = (r.get("title") or "").strip()
            # Avoid titles like "(Printable) Printable" — keep it clean
            if "printable" in base_title.lower() and suffix in ("printable", "free-printable"):
                nr["title"] = base_title
            else:
                nr["title"] = f"{base_title} {title_suffix}".strip()

            nr["intro"] = vary_intro(r.get("intro", ""), suffix)

            # Optional: tweak section titles for a little uniqueness
            if suffix == "packing-list" and nr.get("section1_title"):
                nr["section1_title"] = "Packing Essentials"

            seen.add(new_slug)
            out_rows.append(nr)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Base rows: {len(base_rows)}")
    print(f"Generated rows: {len(out_rows)}")
    print(f"Wrote: {OUT_CSV}")

if __name__ == "__main__":
    main()
