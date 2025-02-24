import uuid
from sqlalchemy import Integer, Column, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
import datetime as _dt
from app.database import Base

from datetime import datetime

CACHE_EXPIRATION_TIME = 3600  # 1 hour expiration time


class Onlyuser(Base):
    __tablename__ = "onlyusers"
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Store UUID as string
    global_user = Column(String, unique=True)  # User's email
    name = Column(String)
    etag = Column(String)
    last_accessed = Column(DateTime, default=_dt.datetime.now)
    last_downloaded = Column(DateTime, default=_dt.datetime.now)

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, ForeignKey("onlyusers.user_id"), primary_key=True)
    subscription = Column(String, primary_key=True)

class Subscriptions(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    category_1_GPT = Column(String)
    category_2_GPT = Column(String)

class Videos(Base):
    __tablename__ = "videos"
    id = Column(String, primary_key=True)
    channel_id = Column(String)
    title = Column(String, index=True)
    description = Column(String, index=True)

class Preferences(Base):
    __tablename__ = "preference"
    user_id = Column(String, primary_key=True)
    preference = Column(String, primary_key=True)

class ComputedPreferences(Base):
    __tablename__ = "computed_preference"
    user_id = Column(String, primary_key=True)
    preference = Column(String, primary_key=True)
    weight = Column(Float)

class FriendRequest(Base):
    __tablename__ = "friend_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    sender_id = Column(String, ForeignKey('onlyusers.user_id'))
    receiver_id = Column(String, ForeignKey('onlyusers.user_id'))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_dt.datetime.now)

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user1_id = Column(String, ForeignKey('onlyusers.user_id'))
    user2_id = Column(String, ForeignKey('onlyusers.user_id'))
    created_at = Column(DateTime, default=_dt.datetime.now)

class CachedRecommendations(Base):
    __tablename__ = "cached_recommendations_new"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique ID
    user_id = Column(String, index=True)  # Store user ID
    recommendation = Column(Text)  # Store one recommendation at a time
    timestamp = Column(DateTime, default=datetime.utcnow)  # Timestamp
