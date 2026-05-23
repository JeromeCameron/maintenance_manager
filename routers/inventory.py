from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

import crud.inventory as inventory
from schema.database import get_session
from schema.models import EquipmentPart, Part, PartCategory, PartSupplier, StockLevel, StockTransaction

part_category_router = APIRouter(prefix="/api/inventory/part-categories", tags=["PartCategory"])
part_router = APIRouter(prefix="/api/inventory/parts", tags=["Part"])
equipment_part_router = APIRouter(prefix="/api/inventory/equipment-parts", tags=["EquipmentPart"])
part_supplier_router = APIRouter(prefix="/api/inventory/part-suppliers", tags=["PartSupplier"])
stock_level_router = APIRouter(prefix="/api/inventory/stock-levels", tags=["StockLevel"])
stock_transaction_router = APIRouter(prefix="/api/inventory/stock-transactions", tags=["StockTransaction"])


# ------------------------------------------------------------------
# Part Category endpoints


@part_category_router.get("", status_code=status.HTTP_200_OK, response_model=list[PartCategory])
async def get_part_categories(session: Session = Depends(get_session)):
    return inventory.get_part_categories(session)


@part_category_router.get("/{category_id}", status_code=status.HTTP_200_OK, response_model=PartCategory)
async def get_part_category(category_id: int, session: Session = Depends(get_session)):
    category = inventory.get_part_category(session, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part category not found")
    return category


@part_category_router.post("", status_code=status.HTTP_201_CREATED, response_model=PartCategory)
async def add_part_category(category: PartCategory, session: Session = Depends(get_session)):
    return inventory.add_part_category(session, category)


@part_category_router.put("/{category_id}", status_code=status.HTTP_200_OK, response_model=PartCategory)
async def update_part_category(
    category_id: int, data: PartCategory, session: Session = Depends(get_session)
):
    category = inventory.update_part_category(session, category_id, data)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part category not found")
    return category


@part_category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part_category(category_id: int, session: Session = Depends(get_session)):
    deleted = inventory.delete_part_category(session, category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part category not found")


# ------------------------------------------------------------------
# Part endpoints


@part_router.get("", status_code=status.HTTP_200_OK, response_model=list[Part])
async def get_parts(session: Session = Depends(get_session)):
    return inventory.get_parts(session)


@part_router.get("/{part_no}", status_code=status.HTTP_200_OK, response_model=Part)
async def get_part(part_no: str, session: Session = Depends(get_session)):
    part = inventory.get_part(session, part_no)
    if not part:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found")
    return part


@part_router.post("", status_code=status.HTTP_201_CREATED, response_model=Part)
async def add_part(part: Part, session: Session = Depends(get_session)):
    return inventory.add_part(session, part)


@part_router.put("/{part_no}", status_code=status.HTTP_200_OK, response_model=Part)
async def update_part(part_no: str, data: Part, session: Session = Depends(get_session)):
    part = inventory.update_part(session, part_no, data)
    if part is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found")
    return part


@part_router.delete("/{part_no}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(part_no: str, session: Session = Depends(get_session)):
    deleted = inventory.delete_part(session, part_no)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found")


# ------------------------------------------------------------------
# Equipment Part endpoints


@equipment_part_router.get("", status_code=status.HTTP_200_OK, response_model=list[EquipmentPart])
async def get_equipment_parts(session: Session = Depends(get_session)):
    return inventory.get_equipment_parts(session)


@equipment_part_router.get("/{equipment_part_id}", status_code=status.HTTP_200_OK, response_model=EquipmentPart)
async def get_equipment_part(equipment_part_id: int, session: Session = Depends(get_session)):
    ep = inventory.get_equipment_part(session, equipment_part_id)
    if not ep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment part not found")
    return ep


@equipment_part_router.post("", status_code=status.HTTP_201_CREATED, response_model=EquipmentPart)
async def add_equipment_part(equipment_part: EquipmentPart, session: Session = Depends(get_session)):
    return inventory.add_equipment_part(session, equipment_part)


@equipment_part_router.put("/{equipment_part_id}", status_code=status.HTTP_200_OK, response_model=EquipmentPart)
async def update_equipment_part(
    equipment_part_id: int, data: EquipmentPart, session: Session = Depends(get_session)
):
    ep = inventory.update_equipment_part(session, equipment_part_id, data)
    if ep is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment part not found")
    return ep


@equipment_part_router.delete("/{equipment_part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_part(equipment_part_id: int, session: Session = Depends(get_session)):
    deleted = inventory.delete_equipment_part(session, equipment_part_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment part not found")


# ------------------------------------------------------------------
# Part Supplier endpoints


@part_supplier_router.get("", status_code=status.HTTP_200_OK, response_model=list[PartSupplier])
async def get_part_suppliers(session: Session = Depends(get_session)):
    return inventory.get_part_suppliers(session)


@part_supplier_router.get("/{part_supplier_id}", status_code=status.HTTP_200_OK, response_model=PartSupplier)
async def get_part_supplier(part_supplier_id: int, session: Session = Depends(get_session)):
    ps = inventory.get_part_supplier(session, part_supplier_id)
    if not ps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part supplier not found")
    return ps


@part_supplier_router.post("", status_code=status.HTTP_201_CREATED, response_model=PartSupplier)
async def add_part_supplier(part_supplier: PartSupplier, session: Session = Depends(get_session)):
    return inventory.add_part_supplier(session, part_supplier)


@part_supplier_router.put("/{part_supplier_id}", status_code=status.HTTP_200_OK, response_model=PartSupplier)
async def update_part_supplier(
    part_supplier_id: int, data: PartSupplier, session: Session = Depends(get_session)
):
    ps = inventory.update_part_supplier(session, part_supplier_id, data)
    if ps is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part supplier not found")
    return ps


@part_supplier_router.delete("/{part_supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part_supplier(part_supplier_id: int, session: Session = Depends(get_session)):
    deleted = inventory.delete_part_supplier(session, part_supplier_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part supplier not found")


# ------------------------------------------------------------------
# Stock Level endpoints


@stock_level_router.get("", status_code=status.HTTP_200_OK, response_model=list[StockLevel])
async def get_stock_levels(session: Session = Depends(get_session)):
    return inventory.get_stock_levels(session)


@stock_level_router.get("/{stock_level_id}", status_code=status.HTTP_200_OK, response_model=StockLevel)
async def get_stock_level(stock_level_id: int, session: Session = Depends(get_session)):
    sl = inventory.get_stock_level(session, stock_level_id)
    if not sl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock level not found")
    return sl


@stock_level_router.post("", status_code=status.HTTP_201_CREATED, response_model=StockLevel)
async def add_stock_level(stock_level: StockLevel, session: Session = Depends(get_session)):
    return inventory.add_stock_level(session, stock_level)


@stock_level_router.put("/{stock_level_id}", status_code=status.HTTP_200_OK, response_model=StockLevel)
async def update_stock_level(
    stock_level_id: int, data: StockLevel, session: Session = Depends(get_session)
):
    sl = inventory.update_stock_level(session, stock_level_id, data)
    if sl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock level not found")
    return sl


@stock_level_router.delete("/{stock_level_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_level(stock_level_id: int, session: Session = Depends(get_session)):
    deleted = inventory.delete_stock_level(session, stock_level_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock level not found")


# ------------------------------------------------------------------
# Stock Transaction endpoints


@stock_transaction_router.get("", status_code=status.HTTP_200_OK, response_model=list[StockTransaction])
async def get_stock_transactions(session: Session = Depends(get_session)):
    return inventory.get_stock_transactions(session)


@stock_transaction_router.get("/{transaction_id}", status_code=status.HTTP_200_OK, response_model=StockTransaction)
async def get_stock_transaction(transaction_id: int, session: Session = Depends(get_session)):
    tx = inventory.get_stock_transaction(session, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transaction not found")
    return tx


@stock_transaction_router.post("", status_code=status.HTTP_201_CREATED, response_model=StockTransaction)
async def add_stock_transaction(transaction: StockTransaction, session: Session = Depends(get_session)):
    return inventory.add_stock_transaction(session, transaction)


@stock_transaction_router.put("/{transaction_id}", status_code=status.HTTP_200_OK, response_model=StockTransaction)
async def update_stock_transaction(
    transaction_id: int, data: StockTransaction, session: Session = Depends(get_session)
):
    tx = inventory.update_stock_transaction(session, transaction_id, data)
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transaction not found")
    return tx


@stock_transaction_router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_transaction(transaction_id: int, session: Session = Depends(get_session)):
    deleted = inventory.delete_stock_transaction(session, transaction_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transaction not found")


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
