import httpx
import traceback

async def search_mercadolivre(product: str) -> dict:
    """
    Search Mercado Livre using their public API.
    No authentication required for basic searches.
    """
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search"
        params = {
            "q": product,
            "limit": 50,
            "sort": "relevance"
        }

        print(f"[Mercado Livre] Searching for: {product}")
        print(f"[Mercado Livre] URL: {url}?q={product}&limit=50")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            print(f"[Mercado Livre] Status: {response.status_code}")

            data = response.json()

        if "results" not in data:
            print(f"[Mercado Livre] No results key. Response: {str(data)[:500]}")
            return {"marketplace": "Mercado Livre", "offers": []}

        print(f"[Mercado Livre] Found {len(data['results'])} results")

        offers = []
        for item in data["results"]:
            seller_name = item.get("seller", {}).get("nickname", "Desconhecido")
            price = item.get("price", 0)
            link = item.get("permalink", "")
            title = item.get("title", "")

            if not price or price <= 0:
                continue

            offers.append({
                "seller": seller_name,
                "price": float(price),
                "link": link,
                "title": title
            })

        print(f"[Mercado Livre] Returning {len(offers)} offers")
        return {
            "marketplace": "Mercado Livre",
            "offers": offers
        }

    except Exception as e:
        print(f"[Mercado Livre] ERROR: {e}")
        print(f"[Mercado Livre] TRACEBACK: {traceback.format_exc()}")
        return {"marketplace": "Mercado Livre", "offers": []}
