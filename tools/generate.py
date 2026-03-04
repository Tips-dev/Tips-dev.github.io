import os
import csv
from datetime import date

BASE_URL = "https://tips-dev.github.io"
INPUT_FILE = "checklists_generated.csv"
OUTPUT_DIR = "site"
URLS_PER_SITEMAP = 1000

today = date.today().isoformat()

os.makedirs(OUTPUT_DIR, exist_ok=True)

urls = []

with open(INPUT_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        slug = row["slug"]
        url = f"{BASE_URL}/checklists/{slug}/"
        urls.append(url)

# split URLs into chunks
chunks = [urls[i:i+URLS_PER_SITEMAP] for i in range(0, len(urls), URLS_PER_SITEMAP)]

sitemap_files = []

for i, chunk in enumerate(chunks, start=1):
    filename = f"sitemap-pages-{i}.xml"
    filepath = os.path.join(OUTPUT_DIR, filename)

    sitemap_files.append(filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        for url in chunk:
            f.write("  <url>\n")
            f.write(f"    <loc>{url}</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")

        f.write("</urlset>")

# create sitemap index
index_path = os.path.join(OUTPUT_DIR, "sitemap.xml")

with open(index_path, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

    for file in sitemap_files:
        f.write("  <sitemap>\n")
        f.write(f"    <loc>{BASE_URL}/{file}</loc>\n")
        f.write("  </sitemap>\n")

    f.write("</sitemapindex>")
