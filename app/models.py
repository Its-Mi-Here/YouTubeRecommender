from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, DateTime, Float
from sqlalchemy.orm import relationship
import datetime as _dt
from app.database import Base

class Onlyuser(Base):
    __tablename__ = "onlyusers"
    user_id = Column(String, primary_key=True)
    global_user = Column(String)
    name = Column(String)
    last_accessed = Column(DateTime, default=_dt.datetime.now)
    last_downloaded = Column(DateTime, default=_dt.datetime.now)

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
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
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, ForeignKey('onlyusers.user_id'))  # Ensure this matches your user table
    receiver_id = Column(String, ForeignKey('onlyusers.user_id'))  # Ensure this matches your user table
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=_dt.datetime.now)

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(String, ForeignKey('onlyusers.user_id'))
    user2_id = Column(String, ForeignKey('onlyusers.user_id'))
    created_at = Column(DateTime, default=_dt.datetime.now)