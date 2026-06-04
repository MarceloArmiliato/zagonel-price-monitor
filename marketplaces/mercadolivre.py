import httpx
import traceback

async def search_mercadolivre(product: str) -> dict:
    try:
        url = "https://api.mercadolibre.com/sites/MLB/search"
        params = {
            "q": product,
            "limit": 50,
            "sort": "relevance"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "Referer": "https://www.mercadolivre.com.br/"
        }

        print(f"[Mercado Livre] Searching for: {product}")

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            response = await client.get(url, params=params)
            print(f"[Mercado Livre] Status: {response.status_code}")

            if response.status_code == 403:
                print("[Mercado Livre] API blocked. Trying alternative endpoint...")
                alt_url = f"https://api.mercadolibre.com/sites/MLB/search?q={product}&limit=50"
                response = await client.get(alt_url)
                print(f"[Mercado Livre] Alt Status: {response.status_code}")

            data = response.json()

        if "results" not in data:
            print(f"[Mercado Livre] No results. Response: {str(data)[:500]}")
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
