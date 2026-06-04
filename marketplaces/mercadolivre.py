import httpx
import re
import traceback

async def search_mercadolivre(product: str, crawl4ai_url: str = "http://localhost:11235") -> dict:
    try:
        search_url = f"https://lista.mercadolivre.com.br/{product.replace(' ', '-')}"

        print(f"[Mercado Livre] Crawling: {search_url}")

        payload = {
            "url": search_url
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{crawl4ai_url}/crawl",
                json=payload
            )
            data = response.json()

        if not data.get("success"):
            print(f"[Mercado Livre] Crawl failed: {data.get('error')}")
            return {"marketplace": "Mercado Livre", "offers": []}

        html = data.get("html", "")
        print(f"[Mercado Livre] HTML length: {len(html)}")

        offers = parse_ml_results(html)
        print(f"[Mercado Livre] Found {len(offers)} offers")

        return {
            "marketplace": "Mercado Livre",
            "offers": offers
        }

    except Exception as e:
        print(f"[Mercado Livre] ERROR: {e}")
        print(f"[Mercado Livre] TRACEBACK: {traceback.format_exc()}")
        return {"marketplace": "Mercado Livre", "offers": []}


def parse_ml_results(html: str) -> list:
    offers = []

    try:
        # Strategy 1: Extract from structured data (JSON-LD)
        import json
        json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for match in json_ld_matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        offer_item = item.get("item", {})
                        name = offer_item.get("name", "")
                        url = offer_item.get("url", "")
                        offers_data = offer_item.get("offers", {})
                        price = offers_data.get("lowPrice") or offers_data.get("price", 0)

                        if price and float(price) > 0:
                            offers.append({
                                "seller": "Vendedor ML",
                                "price": float(price),
                                "link": url,
                                "title": name
                            })
            except (json.JSONDecodeError, TypeError):
                continue

        if offers:
            return offers

        # Strategy 2: Parse from HTML patterns
        # ML uses data attributes and specific classes for product cards
        price_blocks = re.findall(
            r'<a[^>]*href="(https://[^"]*mercadolivre[^"]*)"[^>]*>.*?'
            r'(?:aria-label|title)="([^"]*)".*?'
            r'(?:class="[^"]*price[^"]*"[^>]*>.*?)?'
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            html, re.DOTALL
        )

        for link, title, price_str in price_blocks:
            try:
                price = float(price_str.replace('.', '').replace(',', '.'))
                if 10 < price < 50000:
                    offers.append({
                        "seller": "Vendedor ML",
                        "price": price,
                        "link": link,
                        "title": title[:100]
                    })
            except ValueError:
                continue

        if offers:
            return offers

        # Strategy 3: Find all prices and links separately
        links = re.findall(r'href="(https://(?:produto\.mercadolivre|www\.mercadolivre)[^"]*)"', html)
        prices = re.findall(r'(\d{1,3}(?:\.\d{3})*),(\d{2})', html)

        for i, (link, (reais, centavos)) in enumerate(zip(links, prices)):
            try:
                price = float(f"{reais.replace('.', '')}.{centavos}")
                if 10 < price < 50000:
                    offers.append({
                        "seller": f"Vendedor ML #{i+1}",
                        "price": price,
                        "link": link,
                        "title": f"Produto ML #{i+1}"
                    })
            except ValueError:
                continue

    except Exception as e:
        print(f"[Mercado Livre] Parse error: {e}")

    return offers
