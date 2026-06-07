from sqlalchemy import Column, Integer, String, DateTime, Float, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    positions = relationship("Position", back_populates="client")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    currency = Column(String, nullable=False)        # waluta bazowa tickera np. USD, PLN
    purchase_price = Column(Float, nullable=False)   # cena zakupu w walucie bazowej
    purchase_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="open")  # "open" | "closed"
    sell_price = Column(Float, nullable=True)        # NULL jesli open
    sell_date = Column(Date, nullable=True)          # NULL jesli open
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="positions")


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, unique=True)  # np. "AAPL", "CDR.WA", "USD/PLN"
    price = Column(Float, nullable=False)                 # cena w walucie bazowej lub kurs do PLN
    currency = Column(String, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
