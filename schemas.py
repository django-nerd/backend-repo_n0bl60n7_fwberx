"""
Database Schemas for SongScribe.AI

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., User -> "user").

These schemas are used for validation in API endpoints and for the database viewer.
"""
from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# -----------------------------
# Core domain schemas
# -----------------------------

class User(BaseModel):
    name: Optional[str] = Field(None, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: Optional[str] = Field(None, description="BCrypt or similar hash")
    role: Literal["user", "admin"] = Field("user", description="Role for access control")
    is_active: bool = Field(True, description="Whether user is active")

class License(BaseModel):
    tier: Literal["personal", "standard", "business", "exclusive"]
    rights_summary: Optional[str] = None
    document_url: Optional[str] = None

class File(BaseModel):
    order_id: Optional[str] = Field(None, description="Related order id")
    kind: Literal["mp3", "wav", "preview", "license_pdf", "upload"]
    url: str
    duration_seconds: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

class Revision(BaseModel):
    order_id: str
    user_id: Optional[str] = None
    notes: str
    status: Literal["requested", "in_progress", "completed", "rejected"] = "requested"
    created_at: Optional[datetime] = None

class Order(BaseModel):
    user_id: Optional[str] = None
    email: EmailStr
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
    price_cents: int = 0
    currency: Literal["USD", "NGN", "EUR", "GBP"] = "USD"
    status: Literal["new", "processing", "completed", "revision"] = "new"
    audio_urls: Optional[List[str]] = None
    revision_limit: int = 0
    revisions_used: int = 0

class DemoRequest(BaseModel):
    email: Optional[EmailStr] = None
    ip: Optional[str] = None
    purpose: Optional[str] = None
    styles: Optional[List[str]] = None
    style_text: Optional[str] = None
    moods: Optional[List[str]] = None
    instrumental_only: bool = False
    preview_url: Optional[str] = None
    created_at: Optional[datetime] = None

class Sample(BaseModel):
    title: str
    category: Literal["Love", "Birthday", "Kids", "Corporate", "Film", "Podcast", "Ads", "Other"] = "Other"
    description: Optional[str] = None
    audio_url: str
    thumbnail_url: Optional[str] = None

class Payment(BaseModel):
    order_id: str
    provider: Literal["stripe", "paystack"]
    amount_cents: int
    currency: Literal["USD", "NGN", "EUR", "GBP"] = "USD"
    status: Literal["pending", "succeeded", "failed"] = "pending"
    provider_reference: Optional[str] = None

# Expose minimal schema metadata for viewers
class SchemaInfo(BaseModel):
    name: str
    fields: Dict[str, str]

