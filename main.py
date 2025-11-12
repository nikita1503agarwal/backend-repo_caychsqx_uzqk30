from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import User, Product

app = FastAPI(title="Poker API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeaderboardEntry(BaseModel):
    username: str
    chips: int = Field(ge=0)


class PurchaseRequest(BaseModel):
    username: str
    package_id: str


@app.get("/")
async def root():
    return {"status": "ok", "service": "poker-api"}


@app.get("/test")
async def test_db():
    try:
        # Attempt a simple stats call
        colls = await _list_collections()
        return {"ok": True, "collections": colls}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _list_collections():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db.list_collection_names()


# Leaderboard (read-only demo using DB if available)
@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard():
    try:
        docs = get_documents("leaderboard", {}, limit=50)
        out = [LeaderboardEntry(username=d.get("username", "Player"), chips=int(d.get("chips", 0))) for d in docs]
        if not out:
            # fallback demo data
            out = [
                LeaderboardEntry(username="Nova", chips=125000),
                LeaderboardEntry(username="Blaze", chips=98000),
                LeaderboardEntry(username="Astra", chips=76500),
                LeaderboardEntry(username="Echo", chips=65420),
                LeaderboardEntry(username="Sol", chips=50210),
            ]
        return out
    except Exception:
        return [
            LeaderboardEntry(username="Nova", chips=125000),
            LeaderboardEntry(username="Blaze", chips=98000),
            LeaderboardEntry(username="Astra", chips=76500),
            LeaderboardEntry(username="Echo", chips=65420),
            LeaderboardEntry(username="Sol", chips=50210),
        ]


# Store packages
STORE_PACKAGES = [
    {"id": "starter", "label": "+10k", "chips": 10000, "price": 2.99},
    {"id": "boost", "label": "+50k", "chips": 50000, "price": 9.99},
    {"id": "pro", "label": "+250k", "chips": 250000, "price": 29.99},
]


@app.get("/store")
async def get_store():
    return {"packages": STORE_PACKAGES}


@app.post("/purchase")
async def purchase(req: PurchaseRequest):
    # Note: Payment integration not implemented. Record intent for demo.
    try:
        doc_id = create_document("purchase", req.model_dump())
        return {"ok": True, "id": doc_id}
    except Exception as e:
        # still return ok in demo mode
        return {"ok": True, "id": None, "note": "demo-mode", "error": str(e)}


# Simple user profile endpoints (demo)
class Profile(BaseModel):
    username: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    chips: int = 10000


@app.get("/profile/{username}", response_model=Profile)
async def get_profile(username: str):
    try:
        docs = get_documents("profile", {"username": username}, limit=1)
        if docs:
            d = docs[0]
            return Profile(
                username=d.get("username", username),
                avatar=d.get("avatar"),
                bio=d.get("bio"),
                chips=int(d.get("chips", 10000)),
            )
    except Exception:
        pass
    return Profile(username=username)


# Settings echo (for demo)
class SettingsPayload(BaseModel):
    sound: bool
    animations: bool
    brightness: int = Field(50, ge=0, le=100)


@app.post("/settings")
async def update_settings(payload: SettingsPayload):
    return {"saved": True, **payload.model_dump()}
