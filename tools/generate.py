import csv, os, re, html
from datetime import datetime

SITE_NAME = "ChecklistVault"

BASE_URL = "https://tips-dev.github.io"   # IMPORTANT FIX

INPUT_CSV = "checklists_generated.csv"
OUT_DIR = "site"

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\- ]+", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-{2,}", "-", s)
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

<p>Updated {updated}</p>

</body>
</html>
"""

def main():

    rows = []

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r = {k.strip(): (v or "").strip() for k,v in r.items()}
            if not r.get("slug"):
                continue

            r["slug"] = slugify(r["slug"])
            r["category"] = slugify(r.get("category","general"))
            rows.append(r)

    ensure_dir(OUT_DIR)
    ensure_dir(os.path.join(OUT_DIR,"checklists"))

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    cats = {}

    for r in rows:
        cats.setdefault(r["category"], []).append(r)

    # CREATE PAGES

    for r in rows:

        slug = r["slug"]
        title = r["title"]
        category = r["category"]

        intro = r.get("intro","Printable checklist.")

        s1_title = r.get("section1_title","Essentials")
        s2_title = r.get("section2_title","Nice to Have")

        s1_items = split_items(r.get("section1_items",""))
        s2_items = split_items(r.get("section2_items",""))

        s1_list = "\n".join(f"<li>{esc(x)}</li>" for x in s1_items)
        s2_list = "\n".join(f"<li>{esc(x)}</li>" for x in s2_items)

        page_dir = os.path.join(OUT_DIR,"checklists",slug)
        ensure_dir(page_dir)

        page_path = os.path.join(page_dir,"index.html")

        url = f"{BASE_URL}/checklists/{slug}/"

        html_out = PAGE_TEMPLATE.format(
            title=esc(title),
            site=esc(SITE_NAME),
            meta_desc=esc(intro[:150]),
            canonical=url,
            intro=esc(intro),
            s1_title=esc(s1_title),
            s1_list=s1_list,
            s2_title=esc(s2_title),
            s2_list=s2_list,
            updated=updated
        )

        with open(page_path,"w",encoding="utf-8") as f:
            f.write(html_out)

    # CREATE INDEX PAGE

    links = []

    for r in rows:
        links.append(f'<li><a href="{BASE_URL}/checklists/{r["slug"]}/">{esc(r["title"])}</a></li>')

    index_html = f"""
<html>
<head>
<title>{SITE_NAME}</title>
</head>
<body>

<h1>{SITE_NAME}</h1>

<ul>
{''.join(links)}
</ul>

</body>
</html>
"""

    with open(os.path.join(OUT_DIR,"index.html"),"w",encoding="utf-8") as f:
        f.write(index_html)

    # ROBOTS

    with open(os.path.join(OUT_DIR,"robots.txt"),"w") as f:
        f.write(f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
""")

    # SITEMAP

    urls = []

    urls.append(BASE_URL + "/")

    for r in rows:
        urls.append(f"{BASE_URL}/checklists/{r['slug']}/")

    sitemap = []

    sitemap.append('<?xml version="1.0" encoding="UTF-8"?>')
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for u in urls:
        sitemap.append("<url>")
        sitemap.append(f"<loc>{u}</loc>")
        sitemap.append(f"<lastmod>{updated}</lastmod>")
        sitemap.append("</url>")

    sitemap.append("</urlset>")

    with open(os.path.join(OUT_DIR,"sitemap.xml"),"w") as f:
        f.write("\n".join(sitemap))

    print("Site generated successfully")

if __name__ == "__main__":
    main()
