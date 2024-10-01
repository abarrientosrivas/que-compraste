from API import schemas
from typing import List

def calculate_purchase_total(purchase: schemas.PurchaseBase, items: List[schemas.PurchaseItemBase]) -> float | None:    
    if purchase.total is not None:
        return purchase.total
    if purchase.subtotal is not None:
        discount = purchase.discount or 0
        tips = purchase.tips or 0
        return purchase.subtotal - discount - tips
    if items:
        total_from_items = 0
        empty_flag = True
        for item in items:
            if item.total is not None:
                empty_flag = False
                total_from_items += item.total
            elif item.value is not None:
                empty_flag = False
                quantity_mod = item.quantity or 1
                total_from_items += item.value * quantity_mod
        if not empty_flag:
            return total_from_items
    return None

def detect_product_code(code_str: str):
    pass