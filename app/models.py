# import uuid
# from sqlalchemy import Column, String, DateTime, Float, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# import datetime as _dt
# from app.database import Base

# class Onlyuser(Base):
#     __tablename__ = "onlyusers"
#     user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # UUID as primary key
#     global_user = Column(String, unique=True)  # User's email
#     name = Column(String)
#     last_accessed = Column(DateTime, default=_dt.datetime.now)
#     last_downloaded = Column(DateTime, default=_dt.datetime.now)

# class User(Base):
#     __tablename__ = "users"
#     user_id = Column(UUID(as_uuid=True), ForeignKey("onlyusers.user_id"), primary_key=True)
#     subscription = Column(String, primary_key=True)

# class Subscriptions(Base):
#     __tablename__ = "subscriptions"
#     id = Column(String, primary_key=True)
#     title = Column(String, index=True)
#     description = Column(String, index=True)
#     category_1_GPT = Column(String)
#     category_2_GPT = Column(String)

# class Videos(Base):
#     __tablename__ = "videos"
#     id = Column(String, primary_key=True)
#     channel_id = Column(String)
#     title = Column(String, index=True)
#     description = Column(String, index=True)

# class Preferences(Base):
#     __tablename__ = "preference"
#     user_id = Column(String, primary_key=True)
#     preference = Column(String, primary_key=True)

# class ComputedPreferences(Base):
#     __tablename__ = "computed_preference"
#     user_id = Column(String, primary_key=True)
#     preference = Column(String, primary_key=True)
#     weight = Column(Float)

# class FriendRequest(Base):
#     __tablename__ = "friend_requests"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
#     sender_id = Column(UUID(as_uuid=True), ForeignKey('onlyusers.user_id'))
#     receiver_id = Column(UUID(as_uuid=True), ForeignKey('onlyusers.user_id'))
#     status = Column(String, default="pending")
#     created_at = Column(DateTime, default=_dt.datetime.now)

# class Friendship(Base):
#     __tablename__ = "friendships"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
#     user1_id = Column(UUID(as_uuid=True), ForeignKey('onlyusers.user_id'))
#     user2_id = Column(UUID(as_uuid=True), ForeignKey('onlyusers.user_id'))
#     created_at = Column(DateTime, default=_dt.datetime.now)


import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
import datetime as _dt
from app.database import Base

class Onlyuser(Base):
    __tablename__ = "onlyusers"
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Store UUID as string
    global_user = Column(String, unique=True)  # User's email
    name = Column(String)
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
