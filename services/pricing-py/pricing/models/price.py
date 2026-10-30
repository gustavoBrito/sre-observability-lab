from pydantic import BaseModel


class Stock(BaseModel):
    """Read model coming from the inventory repository."""

    sku: str
    units: int


class PriceQuote(BaseModel):
    """The outward API shape - what the BFF (and the user) see."""

    sku: str
    price_usd: float
    units: int
