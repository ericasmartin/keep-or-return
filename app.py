import json
import os
import re
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
API_URL = "https://api.typesafe.ai/v1/systemone"


def scrape_product(url: str) -> dict:
    """Fetch a product page and extract text, price, and image."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"text": f"Could not fetch URL: {e}", "price": "", "image": ""}

    # Extract og:image or first product image
    image = ""
    og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not og_match:
        og_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:image["\']', html, re.IGNORECASE)
    if og_match:
        image = og_match.group(1)

    # Extract product title from og:title or <title>
    title = ""
    title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:title["\']', html, re.IGNORECASE)
    if not title_match:
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up common suffixes like "| Brand Name" or "- Brand"
        title = re.split(r'\s*[|–—]\s*', title)[0].strip()

    # Extract og:description for product details
    description = ""
    desc_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:description["\']', html, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()

    # Extract price
    price = ""
    price_match = re.search(r'<meta\s+(?:property|itemprop)=["\'](?:og:price:amount|product:price:amount|price)["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+(?:property|itemprop)=["\'](?:og:price:amount|product:price:amount|price)["\']', html, re.IGNORECASE)
    if price_match:
        price = price_match.group(1)
    else:
        price_text = re.search(r'[\$£€]\s*\d[\d,]*(?:\.\d{2})?', html)
        if price_text:
            price = price_text.group(0)

    # Strip scripts/styles for full text
    clean = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", clean)
    text = re.sub(r"\s+", " ", text).strip()

    return {"text": text[:3000], "price": price, "image": image, "title": title, "description": description}


def analyze(description: str, price: str = "") -> dict:
    state = f"Fashion item: {description}"
    if price:
        state += f"\nPrice: {price}"

    payload = {
        "state": state,
        "model": "jev-latest",
        "questions": {
            "cost_per_wear": {
                "type": "score",
                "instructions": "How often would someone realistically wear this item? Consider versatility across occasions, seasons, and outfit combinations. Higher means more wearable and better cost-per-wear value.",
                "criteria": [
                    "Rarely — special occasion only, maybe 1-2 times a year",
                    "Sometimes — specific situations, maybe monthly",
                    "Regularly — weekly rotation piece",
                    "Constantly — could wear multiple times a week across many contexts",
                ],
            },
            "trend_vs_timeless": {
                "type": "score",
                "instructions": "Is this item trendy and likely to feel dated soon, or is it a timeless piece that will still look good in 2+ years?",
                "criteria": [
                    "Very trendy — will look dated within a season",
                    "Somewhat trendy — riding a current wave",
                    "Classic with a modern twist",
                    "Timeless — would look good in any decade",
                ],
            },
            "material_quality": {
                "type": "score",
                "instructions": "Based on the described materials and construction, how is the quality and sustainability? Consider natural vs synthetic fibers, organic/sustainable sourcing, durability.",
                "criteria": [
                    "Poor — cheap synthetics, polyester, plastic-based, fast fashion quality",
                    "Below average — synthetic blends, basic construction",
                    "Good — decent materials, some natural fibers",
                    "Excellent — high-quality natural fibers, organic, sustainable, built to last",
                ],
            },
            "dopamine_vs_love": {
                "type": "score",
                "instructions": "Does this sound like an impulse purchase driven by momentary excitement, or a thoughtful addition that fills a real wardrobe need?",
                "criteria": [
                    "Pure dopamine — impulse buy, novelty-driven",
                    "Mostly excitement — fun but not needed",
                    "Considered — some thought went into this",
                    "Genuine love — fills a real gap, intentional purchase",
                ],
            },
            "closet_redundancy": {
                "type": "score",
                "instructions": "Based on the description, how likely is it that someone already owns something very similar? Consider how common/basic vs unique this item is.",
                "criteria": [
                    "Very unique — unlikely to already own anything like it",
                    "Somewhat distinct — might have something vaguely similar",
                    "Common — probably owns something similar already",
                    "Highly redundant — almost certainly a duplicate of something owned",
                ],
            },
            "verdict": {
                "type": "choice",
                "instructions": "Based on the overall assessment of cost-per-wear, trendiness, material quality, purchase intention, and redundancy — should this item be kept or returned?",
                "criteria": {
                    "keep": "Worth keeping — good value, quality, and fills a wardrobe need",
                    "return": "Should return — poor value, trendy, low quality, or redundant",
                    "sleep_on_it": "On the fence — not clearly a keep or return, think about it for a day",
                },
            },
        },
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {TYPESAFE_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        base = os.path.dirname(os.path.abspath(__file__))
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(os.path.join(base, "index.html"), "rb") as f:
                self.wfile.write(f.read())
        elif self.path.startswith("/fonts/") and self.path.endswith(".woff2"):
            font_path = os.path.join(base, self.path.lstrip("/"))
            if os.path.exists(font_path):
                self.send_response(200)
                self.send_header("Content-Type", "font/woff2")
                self.send_header("Cache-Control", "public, max-age=31536000")
                self.end_headers()
                with open(font_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/analyze":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            input_type = body.get("type", "description")
            url = body.get("url", "")
            notes = body.get("notes", "")
            description = body.get("description", "")
            price = ""
            image = ""

            if input_type == "link" and url:
                scraped = scrape_product(url)
                description = scraped["text"]
                price = scraped["price"]
                image = scraped["image"]

            if notes:
                description += f"\n\nUser notes: {notes}"

            if not description:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No description provided"}).encode())
                return

            try:
                result = analyze(description, price)
                result["scraped"] = {
                    "price": price,
                    "image": image,
                    "title": scraped.get("title", "") if input_type == "link" else "",
                    "description": scraped.get("description", "") if input_type == "link" else "",
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"  {args[0]}")


if __name__ == "__main__":
    port = 8899
    print(f"\n  Keep or Return? running at http://localhost:{port}\n")
    HTTPServer(("", port), Handler).serve_forever()
