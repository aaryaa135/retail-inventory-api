from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus


class CategoryBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, json_schema_extra={"example": "Electronics"}
    )
    description: str | None = Field(None, max_length=255)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=200, json_schema_extra={"example": "Wireless Headphones"}
    )
    sku: str = Field(..., min_length=1, max_length=50, json_schema_extra={"example": "WH-1000XM5"})
    description: str | None = Field(None, max_length=500)
    price: float = Field(..., gt=0, json_schema_extra={"example": 299.99})
    category_id: int | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    category_id: int | None = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    category: CategoryResponse | None = None
    model_config = ConfigDict(from_attributes=True)


class InventoryCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=0, json_schema_extra={"example": 100})
    low_stock_threshold: int = Field(10, ge=0, json_schema_extra={"example": 10})


class InventoryUpdate(BaseModel):
    quantity: int | None = Field(None, ge=0)
    low_stock_threshold: int | None = Field(None, ge=0)


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    low_stock_threshold: int
    updated_at: datetime | None = None
    is_low_stock: bool = False
    model_config = ConfigDict(from_attributes=True)


class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_quantity: int
    low_stock_threshold: int
    shortage: int


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, json_schema_extra={"example": 2})


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: float
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
