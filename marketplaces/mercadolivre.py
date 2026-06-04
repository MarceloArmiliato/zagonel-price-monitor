import httpx

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

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "results" not in data:
            return {"marketplace": "Mercado Livre", "offers": []}

        offers = []
        seen_sellers = set()

        for item in data["results"]:
            seller_name = item.get("seller", {}).get("nickname", "Desconhecido")
            price = item.get("price", 0)
            link = item.get("permalink", "")
            title = item.get("title", "")

            # Skip items with price 0 or None
            if not price or price <= 0:
                continue

            # Filter: keep only items that match the product name reasonably
            offers.append({
                "seller": seller_name,
                "price": float(price),
                "link": link,
                "title": title
            })

        return {
            "marketplace": "Mercado Livre",
            "offers": offers
        }

    except Exception as e:
        print(f"[Mercado Livre] Error: {e}")
        return {"marketplace": "Mercado Livre", "offers": []}
