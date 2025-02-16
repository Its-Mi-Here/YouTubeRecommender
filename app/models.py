from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, DateTime, Float
from sqlalchemy.orm import relationship
import datetime as _dt
# import passlib.hash as _hash

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

    # items = relationship("Item", back_populates="owner")


class Subscriptions(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    category_1_GPT = Column(String)
    category_2_GPT = Column(String)

    # owner = relationship("User", back_populates="items")
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