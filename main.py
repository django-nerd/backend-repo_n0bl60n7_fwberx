import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timedelta, timezone

from database import db, create_document, get_documents
from schemas import User, Order, DemoRequest, File as FileDoc, License, Revision, Payment

app = FastAPI(title="SongScribe.AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"name": "SongScribe.AI API", "status": "ok"}


@app.get("/test")
def test_database():
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            resp["database"] = "✅ Available"
            resp["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            resp["database_name"] = os.getenv("DATABASE_NAME") or ""
            try:
                resp["collections"] = db.list_collection_names()
                resp["database"] = "✅ Connected & Working"
                resp["connection_status"] = "Connected"
            except Exception as e:
                resp["database"] = f"⚠️ Connected but Error: {str(e)[:60]}"
        else:
            resp["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:80]}"
    return resp


# -----------------------------
# Config endpoints (stub values)
# -----------------------------
DEFAULT_PRICING = {
    "personal": {"price_cents": 1999, "revisions": 1},
    "standard": {"price_cents": 3999, "revisions": 2},
    "business": {"price_cents": 14900, "revisions": 3},
    "exclusive": {"price_cents": 49900, "revisions": 5},
}
EXPRESS_FEES = {"express": 900, "super_express": 1900}
LIMITS = {"free_demo_per_day": 1, "demo_duration_seconds": 30}
FEATURE_TOGGLES = {"free_demo_enabled": True}


@app.get("/config")
def get_config():
    return {
        "pricing": DEFAULT_PRICING,
        "express_fees": EXPRESS_FEES,
        "limits": LIMITS,
        "features": FEATURE_TOGGLES,
    }


# -----------------------------
# Auth (lightweight stubs)
# -----------------------------
class AuthRequest(BaseModel):
    email: str
    name: Optional[str] = None


@app.post("/auth/login")
def auth_login(payload: AuthRequest):
    # Very light stub: upsert user by email
    existing = get_documents("user", {"email": payload.email}, limit=1)
    if existing:
        user_id = str(existing[0]["_id"])
    else:
        user_id = create_document("user", User(email=payload.email, name=payload.name or ""))
    return {"user_id": user_id, "email": payload.email}


# -----------------------------
# Demo generation flow
# -----------------------------
class DemoPayload(BaseModel):
    email: Optional[str] = None
    purpose: Optional[str] = None
    styles: Optional[List[str]] = None
    style_text: Optional[str] = None
    moods: Optional[List[str]] = None
    instrumental_only: bool = False


@app.post("/demo/create")
def create_demo(payload: DemoPayload):
    if not FEATURE_TOGGLES.get("free_demo_enabled", False):
        raise HTTPException(status_code=403, detail="Free demo is disabled")

    # Rate limit per email/ip per day (simple check)
    filter_q = {}
    if payload.email:
        filter_q["email"] = payload.email
    today = datetime.now(timezone.utc).date()
    demos = get_documents("demorequest", filter_q)
    demos_today = [d for d in demos if d.get("created_at") and str(d["created_at"]).startswith(str(today))]
    if len(demos_today) >= LIMITS["free_demo_per_day"]:
        raise HTTPException(status_code=429, detail="Demo limit reached for today")

    # Stub AI generation call: return a placeholder preview url
    preview_url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_7c9ec0.mp3?filename=preview.mp3"

    demo_id = create_document(
        "demorequest",
        DemoRequest(
            email=payload.email,
            purpose=payload.purpose,
            styles=payload.styles,
            style_text=payload.style_text,
            moods=payload.moods,
            instrumental_only=payload.instrumental_only,
            preview_url=preview_url,
            created_at=datetime.now(timezone.utc),
        ),
    )
    return {"id": demo_id, "preview_url": preview_url, "duration": LIMITS["demo_duration_seconds"]}


# -----------------------------
# Order creation and generation
# -----------------------------
class OrderPayload(BaseModel):
    email: str
    purpose: str
    for_whom: Optional[str] = None
    styles: List[str] = []
    style_text: Optional[str] = None
    moods: List[str] = []
    vocals: Literal["full", "instrumental", "vocals_only"] = "full"
    vocal_pref: Optional[Literal["male", "female", "none"]] = "none"
    lyrics_mode: Literal["write_for_me", "paste_lyrics", "generate_from_story"] = "write_for_me"
    user_lyrics: Optional[str] = None
    key_phrases: Optional[List[str]] = None
    names_to_include: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    story: Optional[str] = None
    special_elements: Optional[List[str]] = None
    length: Literal["full", "jingle", "extended", "cinematic"] = "full"
    upload_url: Optional[str] = None
    delivery_speed: Literal["standard", "express", "super_express"] = "standard"
    license_tier: Literal["personal", "standard", "business", "exclusive"] = "personal"


@app.post("/orders/create")
def create_order(payload: OrderPayload):
    pricing = DEFAULT_PRICING[payload.license_tier]["price_cents"]
    fee = EXPRESS_FEES.get(payload.delivery_speed, 0)
    revision_limit = DEFAULT_PRICING[payload.license_tier]["revisions"]

    order = Order(
        email=payload.email,
        purpose=payload.purpose,
        for_whom=payload.for_whom,
        styles=payload.styles,
        style_text=payload.style_text,
        moods=payload.moods,
        vocals=payload.vocals,
        vocal_pref=payload.vocal_pref,
        lyrics_mode=payload.lyrics_mode,
        user_lyrics=payload.user_lyrics,
        key_phrases=payload.key_phrases,
        names_to_include=payload.names_to_include,
        languages=payload.languages,
        story=payload.story,
        special_elements=payload.special_elements,
        length=payload.length,
        upload_url=payload.upload_url,
        delivery_speed=payload.delivery_speed,
        license_tier=payload.license_tier,
        price_cents=pricing + fee,
        revision_limit=revision_limit,
        revisions_used=0,
    )
    order_id = create_document("order", order)

    # Stub: pretend we called AI API and got two versions
    audio_urls = [
        "https://cdn.pixabay.com/download/audio/2021/11/18/audio_11c2.mp3?filename=track1.mp3",
        "https://cdn.pixabay.com/download/audio/2021/11/18/audio_22a1.mp3?filename=track2.mp3",
    ]
    db["order"].update_one({"_id": db["order"].find_one({"_id": db["order"].find_one({"_id": db["order"].find_one})})}, {"$set": {"audio_urls": audio_urls, "status": "completed"}})
    # Simpler and correct update by id after insert
    from bson import ObjectId
    db["order"].update_one({"_id": ObjectId(order_id)}, {"$set": {"audio_urls": audio_urls, "status": "completed"}})

    return {"order_id": order_id, "audio_urls": audio_urls}


@app.get("/orders")
def list_orders(email: Optional[str] = None):
    query = {"email": email} if email else {}
    docs = get_documents("order", query)
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify
    return {"orders": docs}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    from bson import ObjectId
    doc = db["order"].find_one({"_id": ObjectId(order_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    doc["_id"] = str(doc["_id"])  # stringify
    return doc


# -----------------------------
# Samples and contact
# -----------------------------
class ContactMessage(BaseModel):
    name: str
    email: str
    message: str


@app.post("/contact")
def contact(msg: ContactMessage):
    create_document("contact", msg.model_dump())
    return {"ok": True}


class SamplePayload(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    audio_url: str


@app.get("/samples")
def samples_list():
    docs = get_documents("sample")
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify
    return {"samples": docs}


@app.post("/samples")
def samples_create(payload: SamplePayload):
    _id = create_document("sample", payload.model_dump())
    return {"id": _id}


# -----------------------------
# Webhook stubs (Stripe / Paystack)
# -----------------------------
@app.post("/webhooks/stripe")
def stripe_webhook(event: Dict[str, Any]):
    # In production, verify signature header
    create_document("webhook", {"provider": "stripe", "event": event})
    return {"received": True}


@app.post("/webhooks/paystack")
def paystack_webhook(event: Dict[str, Any]):
    create_document("webhook", {"provider": "paystack", "event": event})
    return {"received": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
