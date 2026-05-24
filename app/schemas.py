from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models import OrderStatus


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Electronics")
    description: Optional[str] = Field(None, max_length=255)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, example="Wireless Headphones")
    sku: str = Field(..., min_length=1, max_length=50, example="WH-1000XM5")
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0, example=299.99)
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True


class InventoryCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=0, example=100)
    low_stock_threshold: int = Field(10, ge=0, example=10)

class InventoryUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    low_stock_threshold: int
    updated_at: Optional[datetime] = None
    is_low_stock: bool = False
    class Config:
        from_attributes = True

class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_quantity: int
    low_stock_threshold: int
    shortage: int


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, example=2)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float = 0.0
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: float
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True
