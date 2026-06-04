import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from marketplaces.mercadolivre import search_mercadolivre
from marketplaces.shopee import search_shopee

app = FastAPI(title="Zagonel Price Monitor")

class SearchRequest(BaseModel):
    product: str
    min_price: Optional[float] = None
    crawl4ai_url: Optional[str] = "http://localhost:11235"

class Offer(BaseModel):
    seller: str
    price: float
    link: str
    below_min: bool = False

class MarketplaceResult(BaseModel):
    marketplace: str
    offers: list[Offer]
    average: float
    total_offers: int

class SearchResponse(BaseModel):
    product: str
    min_price: Optional[float]
    results: list[MarketplaceResult]
    general_average: float
    total_offers: int
    total_below_min: int

@app.get("/")
async def home():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/search")
async def search(request: SearchRequest):
    all_results = []

    # Run searches in parallel
    tasks = [
        search_mercadolivre(request.product, request.crawl4ai_url),
        search_shopee(request.product, request.crawl4ai_url),
    ]

    marketplace_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_prices = []
    total_below_min = 0

    for result in marketplace_results:
        if isinstance(result, Exception):
            print(f"[Server] Task error: {result}")
            continue
        if result and result["offers"]:
            offers = []
            prices = []
            for offer in result["offers"]:
                below_min = False
                if request.min_price and offer["price"] < request.min_price:
                    below_min = True
                    total_below_min += 1

                offers.append(Offer(
                    seller=offer["seller"],
                    price=offer["price"],
                    link=offer["link"],
                    below_min=below_min
                ))
                prices.append(offer["price"])

            avg = round(sum(prices) / len(prices), 2) if prices else 0
            all_prices.extend(prices)

            all_results.append(MarketplaceResult(
                marketplace=result["marketplace"],
                offers=offers,
                average=avg,
                total_offers=len(offers)
            ))

    general_avg = round(sum(all_prices) / len(all_prices), 2) if all_prices else 0

    return SearchResponse(
        product=request.product,
        min_price=request.min_price,
        results=all_results,
        general_average=general_avg,
        total_offers=len(all_prices),
        total_below_min=total_below_min
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
