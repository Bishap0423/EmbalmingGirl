from embalming_game import load_card_catalog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Embalming Girl API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    ruleset: str
    card_types: int
    card_instances: int


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    cards = load_card_catalog()
    return HealthResponse(
        status="ok",
        ruleset="2020-06-30-project-ruling-1",
        card_types=len(cards),
        card_instances=sum(card.copies for card in cards),
    )
