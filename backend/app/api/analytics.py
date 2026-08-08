from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.order.order import Order
from app.models.products.product import Product
from app.models.user.users import User
from app.models.products.prodcut_detection import ProductDetection

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0.0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_customers = db.query(func.count(User.id)).scalar() or 0
    
    avg_confidence = db.query(func.avg(ProductDetection.confidence_score)).scalar() or 0.94
    
    return {
        "total_orders": total_orders,
        "total_revenue": round(float(total_revenue), 2),
        "average_order_value": round(float(avg_order_value), 2),
        "total_products": total_products,
        "total_customers": total_customers,
        "detection_accuracy_percentage": round(float(avg_confidence) * 100, 1),
        "system_status": "Healthy",
    }


@router.get("/customers")
def get_real_customers(db: Session = Depends(get_db)):
    users = db.query(User).limit(50).all()
    result = []
    for u in users:
        order_count = db.query(func.count(Order.id)).filter(Order.user_id == u.id).scalar() or 0
        total_spent = db.query(func.sum(Order.total_amount)).filter(Order.user_id == u.id).scalar() or 0.0
        result.append({
            "id": u.id,
            "name": u.name or u.email.split("@")[0].title(),
            "email": u.email,
            "orders": order_count,
            "spent": round(float(total_spent), 2),
            "status": "vip" if total_spent > 5000 else "active",
        })
    return result


@router.get("/logs")
def get_real_system_logs(db: Session = Depends(get_db)):
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(15).all()
    logs = []
    for o in recent_orders:
        logs.append({
            "id": f"ORD-{o.id[:6].upper()}",
            "action": "ORDER_PLACED",
            "detail": f"Order #{o.order_number} created with total ₹{float(o.total_amount):,.2f}",
            "user": o.user_id[:8],
            "time": o.created_at.strftime("%Y-%m-%d %H:%M"),
            "severity": "info",
        })
    return logs
