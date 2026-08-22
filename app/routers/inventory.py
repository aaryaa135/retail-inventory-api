from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.InventoryResponse, status_code=201)
def create_inventory(inv: schemas.InventoryCreate, db: Session = Depends(get_db)):
    if not db.query(models.Product).filter(models.Product.id == inv.product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")
    if db.query(models.Inventory).filter(models.Inventory.product_id == inv.product_id).first():
        raise HTTPException(
            status_code=409, detail="Inventory already exists for this product. Use PUT to update."
        )
    db_inv = models.Inventory(**inv.model_dump())
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    response = schemas.InventoryResponse.model_validate(db_inv)
    response.is_low_stock = db_inv.quantity <= db_inv.low_stock_threshold
    return response


@router.get("/low-stock", response_model=list[schemas.LowStockAlert])
def get_low_stock_alerts(
    threshold_override: int | None = Query(None), db: Session = Depends(get_db)
):
    records = (
        db.query(models.Inventory, models.Product)
        .join(models.Product, models.Inventory.product_id == models.Product.id)
        .all()
    )
    alerts = []
    for inv, product in records:
        threshold = (
            threshold_override if threshold_override is not None else inv.low_stock_threshold
        )
        if inv.quantity <= threshold:
            alerts.append(
                schemas.LowStockAlert(
                    product_id=product.id,
                    product_name=product.name,
                    sku=product.sku,
                    current_quantity=inv.quantity,
                    low_stock_threshold=threshold,
                    shortage=max(0, threshold - inv.quantity),
                )
            )
    return sorted(alerts, key=lambda x: x.current_quantity)


@router.get("/", response_model=list[schemas.InventoryResponse])
def list_inventory(db: Session = Depends(get_db)):
    records = db.query(models.Inventory).all()
    result = []
    for r in records:
        item = schemas.InventoryResponse.model_validate(r)
        item.is_low_stock = r.quantity <= r.low_stock_threshold
        result.append(item)
    return result


@router.get("/{product_id}", response_model=schemas.InventoryResponse)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found for this product")
    response = schemas.InventoryResponse.model_validate(inv)
    response.is_low_stock = inv.quantity <= inv.low_stock_threshold
    return response


@router.put("/{product_id}", response_model=schemas.InventoryResponse)
def update_inventory(
    product_id: int, updates: schemas.InventoryUpdate, db: Session = Depends(get_db)
):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    db.commit()
    db.refresh(inv)
    response = schemas.InventoryResponse.model_validate(inv)
    response.is_low_stock = inv.quantity <= inv.low_stock_threshold
    return response
