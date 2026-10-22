from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.database import (
    get_nearby_pharmacies,
    get_medicines_for_patient,
    create_medicine_order,
    get_patient_orders,
    get_order_by_id,
    advance_order_status
)

router = APIRouter(prefix="/api/pharmacy", tags=["Pharmacy & Medicine Delivery"])

class OrderItem(BaseModel):
    medicine_id: Optional[str] = None
    name: str
    dosage: Optional[str] = ""
    price: float
    quantity: int = 1
    total: float

class CreateOrderRequest(BaseModel):
    patient_id: str
    patient_name: Optional[str] = "Patient"
    pharmacy_id: str
    pharmacy_name: str
    items: List[OrderItem]
    subtotal: float
    delivery_fee: float = 0.0
    total_amount: float
    delivery_address: str
    phone: str
    payment_method: str = "Cash on Delivery"
    delivery_type: str = "express"
    estimated_delivery_mins: int = 25

@router.get("/nearby")
def list_nearby_pharmacies() -> List[Dict[str, Any]]:
    """Return verified neighborhood medical shops with proximity, ratings, and open status"""
    return get_nearby_pharmacies()

@router.get("/medicines")
def list_patient_medicines(patient_id: str = Query("P0001")) -> Dict[str, Any]:
    """Return prescribed medicines matched to patient previous clinical history and diagnosis"""
    return get_medicines_for_patient(patient_id)

@router.post("/order")
def place_medicine_order(payload: CreateOrderRequest) -> Dict[str, Any]:
    """Place a new prescription / medicine delivery order with a nearby pharmacy"""
    order_dict = payload.model_dump()
    created = create_medicine_order(order_dict)
    return {
        "success": True,
        "message": f"Order {created['order_id']} placed successfully with {payload.pharmacy_name}",
        "order": created
    }

@router.get("/orders")
def get_orders_for_patient(patient_id: str = Query("P0001")) -> List[Dict[str, Any]]:
    """Get all past and active delivery orders for a given patient"""
    return get_patient_orders(patient_id)

@router.get("/orders/{order_id}")
def get_order_status(order_id: str) -> Dict[str, Any]:
    """Get live tracking status and receipt for a medicine delivery order"""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return order

@router.post("/orders/{order_id}/advance")
def advance_delivery_progress(order_id: str, status: Optional[str] = None) -> Dict[str, Any]:
    """Simulate delivery milestone progression (demo tool for evaluation)"""
    updated = advance_order_status(order_id, next_status=status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return {
        "success": True,
        "status": updated["status"],
        "order": updated
    }
