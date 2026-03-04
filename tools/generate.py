import csv
import os
import re
import html
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

SITE_NAME = "ChecklistVault"

# IMPORTANT: must be absolute for sitemaps + canonical tags
BASE_URL = "https://tips-dev.github.io"

# IMPORTANT: use the generated CSV (variants)
INPUT_CSV = "checklists_generated.csv"

# Your workflow copies site/* to repo root
OUT_DIR = "site"


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\- ]+", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def esc(s: str) -> str:
    return html.escape(s or "")


def split_items(items: str):
    if not items:
        return []
    return [i.strip() for i in items.split("|") if i.strip()]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title} | {site}</title>
<meta name="description" content="{meta_desc}" />
<link rel="canonical" href="{canonical}" />
</head>
<body>

<header>
  <p><a href="{home_url}">{site}</a></p>
</header>

<main>
  <h1>{title}</h1>
  <p>{intro}</p>

  <h2>{s1_title}</h2>
  <ul>
  {s1_list}
  </ul>

  <h2>{s2_title}</h2>
  <ul>
  {s2_list}
  </ul>

  <p><small>Updated {updated}</small></p>
</main>

</body>
</html>
"""


def main():
    rows = []

    # Read CSV
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r = {k.strip(): (v or "").strip() for k, v in r.items()}

            if not r.get("slug") or not r.get("title"):
                continue

            r["slug"] = slugify(r["slug"])
            r["category"] = slugify(r.get("category", "general"))

            rows.append(r)

    if not rows:
        raise SystemExit(f"No rows found in {INPUT_CSV}")

    # Output folders
    ensure_dir(OUT_DIR)
    ensure_dir(os.path.join(OUT_DIR, "checklists"))

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    # Build pages
    for r in rows:
        slug = r["slug"]
        title = r["title"]
        intro = r.get("intro", "Printable checklist.")
        s1_title = r.get("section1_title", "Essentials") or "Essentials"
        s2_title = r.get("section2_title", "Nice to Have") or "Nice to Have"

        s1_items = split_items(r.get("section1_items", ""))
        s2_items = split_items(r.get("section2_items", ""))

        s1_list = "\n  ".join(f"<li>{esc(x)}</li>" for x in s1_items) if s1_items else "<li>(Add items)</li>"
        s2_list = "\n  ".join(f"<li>{esc(x)}</li>" for x in s2_items) if s2_items else "<li>(Add items)</li>"

        page_dir = os.path.join(OUT_DIR, "checklists", slug)
        ensure_dir(page_dir)

        page_path = os.path.join(page_dir, "index.html")

        canonical = f"{BASE_URL}/checklists/{slug}/"

        html_out = PAGE_TEMPLATE.format(
            title=esc(title),
            site=esc(SITE_NAME),
            meta_desc=esc(intro[:155]),
            canonical=canonical,
            intro=esc(intro),
            s1_title=esc(s1_title),
            s1_list=s1_list,
            s2_title=esc(s2_title),
            s2_list=s2_list,
            updated=updated,
            home_url=f"{BASE_URL}/",
        )

        with open(page_path, "w", encoding="utf-8") as f:
            f.write(html_out)

    # Index page (simple list)
    links = []
    for r in rows:
        links.append(f'<li><a href="{BASE_URL}/checklists/{r["slug"]}/">{esc(r["title"])}</a></li>')

    index_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{esc(SITE_NAME)}</title>
<meta name="description" content="Printable checklists for travel, home, moving, work, and more." />
<link rel="canonical" href="{BASE_URL}/" />
</head>
<body>
<h1>{esc(SITE_NAME)}</h1>
<p>Printable checklists for travel, home, moving, work, and more.</p>
<ul>
{''.join(links)}
</ul>
</body>
</html>
"""

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # robots.txt
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(
            "User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {BASE_URL}/sitemap.xml\n"
        )

    # ✅ VALID XML SITEMAP (this is the important fix)
    urls = [f"{BASE_URL}/"]
    for r in rows:
        urls.append(f"{BASE_URL}/checklists/{r['slug']}/")

    sitemap_lines = []
    sitemap_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    sitemap_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for u in urls:
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{xml_escape(u)}</loc>")
        sitemap_lines.append(f"    <lastmod>{updated}</lastmod>")
        sitemap_lines.append("  </url>")

    sitemap_lines.append("</urlset>")

    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))

    print(f"Generated {len(rows)} checklist pages")
    print("Wrote sitemap.xml as valid XML")


if __name__ == "__main__":
    main()
