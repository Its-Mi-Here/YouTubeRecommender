from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, DateTime
from sqlalchemy.orm import relationship
import datetime as _dt
# import passlib.hash as _hash

from app.database import Base

class Onlyuser(Base):
    __tablename__ = "onlyusers"
    user_id = Column(String, primary_key=True)
    last_accessed = Column(DateTime, default=_dt.datetime.now)
    name = Column(String)
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

    # owner = relationship("User", back_populates="items")