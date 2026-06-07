from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import date
from typing import Optional
from enum import Enum


class CurrencyEnum(str, Enum):
    PLN = "PLN"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str

    @field_validator("name")
    @classmethod
    def name_min_length(cls, v: str) -> str:
        v = v.strip()
        parts = [p for p in v.split() if p]
        if len(parts) < 2:
            raise ValueError("Podaj imię i nazwisko (dwa słowa).")
        if any(len(p) < 3 for p in parts):
            raise ValueError("Imię i nazwisko muszą mieć minimum 3 litery każde.")
        if not all(any(c.isalpha() for c in p) for p in parts):
            raise ValueError("Imię i nazwisko muszą zawierać litery.")
        return v

    @field_validator("phone")
    @classmethod
    def phone_min_length(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 9:
            raise ValueError("Numer telefonu musi zawierać minimum 6 cyfr.")
        return v.strip()


class PositionCreate(BaseModel):
    ticker: str
    quantity: float
    currency: CurrencyEnum
    purchase_price: float
    purchase_date: date

    @field_validator("ticker")
    @classmethod
    def ticker_format(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 1:
            raise ValueError("Ticker nie może być pusty.")
        if len(v) > 20:
            raise ValueError("Ticker jest za długi (max 20 znaków).")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Liczba akcji musi być większa od 0.")
        return v

    @field_validator("purchase_price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Cena zakupu musi być większa od 0.")
        return v

    @field_validator("purchase_date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Data zakupu nie może być z przyszłości.")
        return v
