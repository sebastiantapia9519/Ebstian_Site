"""Database models for Ebstian's personal content.

ST Monitor configuration intentionally remains in sites.json for now.
These models are reserved for the new public content and its future admin UI.
"""
from datetime import datetime, timezone

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class Artist(TimestampMixin, db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    country = db.Column(db.String(80))
    genre = db.Column(db.String(100))
    spotify_url = db.Column(db.String(500))
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Album(TimestampMixin, db.Model):
    __tablename__ = "albums"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id", ondelete="SET NULL"), index=True)
    title = db.Column(db.String(180), nullable=False)
    release_year = db.Column(db.Integer)
    cover_url = db.Column(db.String(1000))
    spotify_url = db.Column(db.String(500))
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    artist = db.relationship("Artist", backref=db.backref("albums", lazy="select"))


class Collection(TimestampMixin, db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(1000))
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)


class CollectionItem(TimestampMixin, db.Model):
    __tablename__ = "collection_items"

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = db.Column(db.String(40), nullable=False, default="link")
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1000))
    image_url = db.Column(db.String(1000))
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    collection = db.relationship("Collection", backref=db.backref("items", lazy="select", cascade="all, delete-orphan"))


class RandomEntry(TimestampMixin, db.Model):
    __tablename__ = "random_entries"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180))
    content = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(1000))
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)


class Experiment(TimestampMixin, db.Model):
    __tablename__ = "experiments"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1000))
    status = db.Column(db.String(40), nullable=False, default="draft")
    position = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)


class SiteSetting(TimestampMixin, db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    value = db.Column(db.Text)
