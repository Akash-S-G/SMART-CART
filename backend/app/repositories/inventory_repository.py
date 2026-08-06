from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.products.inventory import Inventory
from app.models.products.inventory_transaction import (
    InventoryTransaction,
    InventoryTransactionType,
)

class InventoryRepository:

    def __init__(self, db: Session):
        self.db = db


    def create(
        self,
        inventory: Inventory,
    ) -> Inventory:

        self.db.add(inventory)

        self.db.commit()

        self.db.refresh(inventory)

        return inventory
    
    def get_by_product(
    self,
        product_id: str,
        ) -> Inventory | None:

        stmt = (
            select(Inventory)
            .where(
                Inventory.product_id == product_id     )
        )

        return self.db.scalar(stmt)

    def get_by_id(self,inventory_id: str,) -> Inventory | None:

        return self.db.get(
        Inventory,
        inventory_id,
    )
     

    def has_stock(
        self,
        product_id: str,
        quantity: int,
    ) -> bool:

        inventory = self.get_by_product(
            product_id
        )

        if inventory is None:
            return False

        return inventory.quantity >= quantity


    def reduce_stock(
        self,
        product_id: str,
        quantity: int,
    ) -> Inventory:

        inventory = self.get_by_product(
            product_id
        )

        if inventory is None:
            raise ValueError(
                "Inventory not found."
            )

        if inventory.quantity < quantity:
            raise ValueError(
                "Insufficient inventory."
            )

        before = inventory.quantity

        inventory.quantity -= quantity

        self.db.commit()

        self.db.refresh(inventory)

        self.record_transaction(
            inventory_id=inventory.id,
            product_id=product_id,
            transaction_type=InventoryTransactionType.SALE,
            quantity_change=-quantity,
            quantity_before=before,
            quantity_after=inventory.quantity,
        )

        return inventory


    def increase_stock(
        self,
        product_id: str,
        quantity: int,
    ) -> Inventory:

        inventory = self.get_by_product(
            product_id
        )

        if inventory is None:
            raise ValueError(
                "Inventory not found."
            )

        before = inventory.quantity

        inventory.quantity += quantity

        self.db.commit()

        self.db.refresh(inventory)

        self.record_transaction(
            inventory_id=inventory.id,
            product_id=product_id,
            transaction_type=InventoryTransactionType.RESTOCK,
            quantity_change=quantity,
            quantity_before=before,
            quantity_after=inventory.quantity,
        )

        return inventory

    def update(
        self,
        inventory: Inventory,
    ) -> Inventory:

        self.db.commit()

        self.db.refresh(inventory)

        return inventory


    def delete(
        self,
        inventory: Inventory,
    ) -> None:

        self.db.delete(inventory)

        self.db.commit()


    def record_transaction(
        self,
        inventory_id: str,
        product_id: str,
        transaction_type: InventoryTransactionType,
        quantity_change: int,
        quantity_before: int,
        quantity_after: int,
    ) -> InventoryTransaction:

        transaction = InventoryTransaction(
            inventory_id=inventory_id,
            product_id=product_id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            created_at=datetime.now(
                timezone.utc
            ),
        )

        self.db.add(transaction)

        self.db.commit()

        self.db.refresh(transaction)

        return transaction

    def get_transactions(
        self,
        product_id: str,
    ):

        stmt = (
            select(InventoryTransaction)
            .where(
                InventoryTransaction.product_id
                == product_id
            )
            .order_by(
                InventoryTransaction.created_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )