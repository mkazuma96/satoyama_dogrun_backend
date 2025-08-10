# backend/db_control/models.py

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Date,
    Time,
    Enum,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


# ── ENUM 定義 ─────────────────────────────────────────

class EntryAction(enum.Enum):
    entry = "entry"
    exit = "exit"

class EventStatus(enum.Enum):
    reception = "受付中"
    preparing = "準備中"
    closed = "終了"


# ── テーブル定義 ───────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(String(36), primary_key=True)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    last_name     = Column(String(50))
    first_name    = Column(String(50))
    age           = Column(Integer)
    gender        = Column(String(10))
    zip_code      = Column(String(10))
    prefecture    = Column(String(20))
    city          = Column(String(50))
    address       = Column(String(255))
    building      = Column(String(255))
    phone_number  = Column(String(20))
    avatar_url    = Column(String(255))
    created_at    = Column(DateTime)
    updated_at    = Column(DateTime)


class Terms(Base):
    __tablename__ = "terms"
    id         = Column(String(36), primary_key=True)
    content    = Column(Text, nullable=False)
    updated_at = Column(DateTime)


class TermsAcceptance(Base):
    __tablename__ = "terms_acceptances"
    id          = Column(String(36), primary_key=True)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    term_id     = Column(String(36), ForeignKey("terms.id"), nullable=False)
    accepted_at = Column(DateTime)


class Dog(Base):
    __tablename__ = "dogs"
    id           = Column(String(36), primary_key=True)
    owner_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    name         = Column(String(50), nullable=False)
    breed        = Column(String(50))
    birthday_at  = Column(Date, nullable=False)
    gender       = Column(String(10))
    personality  = Column(Text)
    likes        = Column(Text)
    avatar_url   = Column(String(255))
    created_at   = Column(DateTime)
    updated_at   = Column(DateTime)


class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"
    id             = Column(String(36), primary_key=True)
    dog_id         = Column(String(36), ForeignKey("dogs.id"), nullable=False)
    vaccine_type   = Column(String(100))
    administered_at= Column(Date)
    next_due_at    = Column(Date)
    image_url      = Column(String(255))
    created_at     = Column(DateTime)
    updated_at     = Column(DateTime)


class EntryLog(Base):
    __tablename__ = "entry_logs"
    id          = Column(String(36), primary_key=True)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    action      = Column(Enum(EntryAction), nullable=False)
    occurred_at = Column(DateTime)


class Event(Base):
    __tablename__ = "events"
    id           = Column(String(36), primary_key=True)
    title        = Column(String(100), nullable=False)
    description  = Column(Text)
    event_date   = Column(Date)
    start_time   = Column(Time)
    end_time     = Column(Time)
    location     = Column(String(255))
    capacity     = Column(Integer)
    fee          = Column(Integer)
    status       = Column(Enum(EventStatus), default=EventStatus.reception)
    created_at   = Column(DateTime)
    updated_at   = Column(DateTime)


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    id      = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_id= Column(String(36), ForeignKey("events.id"), nullable=False)
    dog_id  = Column(String(36), ForeignKey("dogs.id"))


class Announcement(Base):
    __tablename__ = "announcements"
    id          = Column(String(36), primary_key=True)
    title       = Column(String(100), nullable=False)
    content     = Column(Text)
    category    = Column(String(50))
    posted_at   = Column(DateTime)
    updated_at  = Column(DateTime)


class Post(Base):
    __tablename__ = "posts"
    id          = Column(String(36), primary_key=True)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    content     = Column(Text)
    created_at  = Column(DateTime)
    updated_at  = Column(DateTime)


class PostImage(Base):
    __tablename__ = "post_images"
    id          = Column(String(36), primary_key=True)
    post_id     = Column(String(36), ForeignKey("posts.id"), nullable=False)
    image_url   = Column(String(255))


class Hashtag(Base):
    __tablename__ = "hashtags"
    id          = Column(String(36), primary_key=True)
    tag         = Column(String(50), unique=True, nullable=False)


class PostHashtag(Base):
    __tablename__ = "post_hashtags"
    id           = Column(String(36), primary_key=True)
    post_id      = Column(String(36), ForeignKey("posts.id"), nullable=False)
    hashtag_id   = Column(String(36), ForeignKey("hashtags.id"), nullable=False)


class Comment(Base):
    __tablename__ = "comments"
    id          = Column(String(36), primary_key=True)
    post_id     = Column(String(36), ForeignKey("posts.id"), nullable=False)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    content     = Column(Text)
    created_at  = Column(DateTime)


class Like(Base):
    __tablename__ = "likes"
    id          = Column(String(36), primary_key=True)
    post_id     = Column(String(36), ForeignKey("posts.id"), nullable=False)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id          = Column(String(36), primary_key=True)
    post_id     = Column(String(36), ForeignKey("posts.id"), nullable=False)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime)
