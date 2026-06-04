import httpx
import json
import re

async def search_shopee(product: str, crawl4ai_url: str = "http://localhost:11235") -> dict:
    """
    Search Shopee using Crawl4AI to crawl the search page.
    Shopee is a SPA (React) so we need browser rendering.
    """
    try:
        search_url = f"https://shopee.com.br/search?keyword={product.replace(' ', '+')}"

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
            return {"marketplace": "Shopee", "offers": []}

        markdown = data.get("markdown", "")
        html = data.get("html", "")

        # Try to extract product data from Shopee's HTML/markdown
        offers = parse_shopee_results(html, markdown)

        return {
            "marketplace": "Shopee",
            "offers": offers
        }

    except Exception as e:
        print(f"[Shopee] Error: {e}")
        return {"marketplace": "Shopee", "offers": []}


def parse_shopee_results(html: str, markdown: str) -> list:
    """
    Parse Shopee search results from crawled HTML.
    Shopee renders products via JavaScript, so results depend on
    whether the crawler waited for JS execution.

    This parser attempts multiple strategies:
    1. Look for JSON data embedded in script tags
    2. Parse visible product cards from HTML
    """
    offers = []

    # Strategy 1: Try to find product data in embedded JSON (SSR data)
    try:
        # Shopee sometimes embeds search results in script tags
        json_matches = re.findall(r'"itemBasic":\s*({[^}]+})', html)
        for match in json_matches:
            try:
                item = json.loads(match)
                name = item.get("name", "")
                price = item.get("price", 0) / 100000  # Shopee stores price * 100000
                shop_name = item.get("shopName", "Vendedor Shopee")
                item_id = item.get("itemid", "")
                shop_id = item.get("shopid", "")

                if price > 0:
                    link = f"https://shopee.com.br/product/{shop_id}/{item_id}"
                    offers.append({
                        "seller": shop_name,
                        "price": float(price),
                        "link": link,
                        "title": name
                    })
            except (json.JSONDecodeError, TypeError):
                continue
    except Exception:
        pass

    # Strategy 2: Try to extract from rendered HTML price patterns
    try:
        # Look for price patterns like "R$ 149,90" or "R$149.90"
        price_pattern = r'R\$\s*(\d{1,6}[.,]\d{2})'
        prices_found = re.findall(price_pattern, html)

        # If we found prices but no offers from Strategy 1
        if prices_found and not offers:
            for i, price_str in enumerate(prices_found[:20]):  # Limit to 20
                price = float(price_str.replace('.', '').replace(',', '.'))
                if 10 < price < 50000:  # Reasonable price range
                    offers.append({
                        "seller": f"Vendedor Shopee #{i+1}",
                        "price": price,
                        "link": f"https://shopee.com.br/search?keyword=",
                        "title": f"Produto Shopee #{i+1}"
                    })
    except Exception:
        pass

    return offers
