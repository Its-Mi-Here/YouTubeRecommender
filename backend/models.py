from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base

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