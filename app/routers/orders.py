from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.OrderResponse, status_code=201)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    order_items = []
    total_amount = 0.0

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == item.product_id).first()
        if not inv:
            raise HTTPException(status_code=400, detail=f"No inventory for '{product.name}'")
        if inv.quantity < item.quantity:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient stock for '{product.name}': requested {item.quantity}, available {inv.quantity}"
            )
        subtotal = product.price * item.quantity
        total_amount += subtotal
        order_items.append((product, inv, item.quantity, subtotal))

    db_order = models.Order(total_amount=total_amount, status=models.OrderStatus.CONFIRMED)
    db.add(db_order)
    db.flush()

    for product, inv, quantity, subtotal in order_items:
        db.add(models.OrderItem(order_id=db_order.id, product_id=product.id, quantity=quantity, unit_price=product.price))
        inv.quantity -= quantity

    db.commit()
    db.refresh(db_order)

    return schemas.OrderResponse(
        id=db_order.id, status=db_order.status, total_amount=db_order.total_amount,
        items=[schemas.OrderItemResponse(id=i.id, product_id=i.product_id, quantity=i.quantity,
               unit_price=i.unit_price, subtotal=i.unit_price * i.quantity) for i in db_order.items],
        created_at=db_order.created_at, updated_at=db_order.updated_at
    )


@router.get("/", response_model=List[schemas.OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    return [schemas.OrderResponse(
        id=o.id, status=o.status, total_amount=o.total_amount,
        items=[schemas.OrderItemResponse(id=i.id, product_id=i.product_id, quantity=i.quantity,
               unit_price=i.unit_price, subtotal=i.unit_price * i.quantity) for i in o.items],
        created_at=o.created_at, updated_at=o.updated_at
    ) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return schemas.OrderResponse(
        id=order.id, status=order.status, total_amount=order.total_amount,
        items=[schemas.OrderItemResponse(id=i.id, product_id=i.product_id, quantity=i.quantity,
               unit_price=i.unit_price, subtotal=i.unit_price * i.quantity) for i in order.items],
        created_at=order.created_at, updated_at=order.updated_at
    )


@router.patch("/{order_id}/cancel", response_model=schemas.OrderResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == models.OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Order is already cancelled")
    for item in order.items:
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == item.product_id).first()
        if inv:
            inv.quantity += item.quantity
    order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return schemas.OrderResponse(
        id=order.id, status=order.status, total_amount=order.total_amount,
        items=[schemas.OrderItemResponse(id=i.id, product_id=i.product_id, quantity=i.quantity,
               unit_price=i.unit_price, subtotal=i.unit_price * i.quantity) for i in order.items],
        created_at=order.created_at, updated_at=order.updated_at
    )
