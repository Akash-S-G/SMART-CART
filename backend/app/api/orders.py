from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.dependencies import (
    get_current_admin,
    get_current_user,
)
from app.db.session import get_db
from app.models.user.users import User

from app.schemas.order import (
    CheckoutResponse,
    OrderListResponse,
    OrderResponse,
    UpdateOrderStatusRequest,
    CancelOrderResponse,
)

from app.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


# =====================================================
# Checkout
# =====================================================

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:

        order = service.checkout(
            user_id=str(current_user.id)
        )

        return CheckoutResponse(order=order)

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# =====================================================
# List Orders
# =====================================================

@router.get(
    "",
    response_model=OrderListResponse,
)
def list_orders(
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    result = service.list_orders(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
    )

    return OrderListResponse(**result)


# =====================================================
# Get Order
# =====================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:

        return service.get_order(
            user_id=str(current_user.id),
            order_id=order_id,
            is_admin=current_user.role == "admin",
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# =====================================================
# Cancel Order
# =====================================================

@router.patch(
    "/{order_id}/cancel",
    response_model=CancelOrderResponse,
)
def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:

        service.cancel_order(
            user_id=str(current_user.id),
            order_id=order_id,
            is_admin=current_user.role == "admin",
        )

        return CancelOrderResponse(
            message="Order cancelled successfully."
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


class UpdateOrderStatusRequest(BaseModel):
    status: str

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from app.models.order.order import Order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    status_upper = request.status.upper()
    order.status = status_upper
    db.commit()
    service = OrderService(db)
    return service.get_order(user_id=str(current_user.id), order_id=order_id, is_admin=True)


# =====================================================
# Update Status (Admin)
# =====================================================

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
def update_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):

    service = OrderService(db)

    try:

        return service.update_status(
            order_id=order_id,
            status=request.status,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )