from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_admin,
    get_current_user,
)

from app.db.session import get_db

from app.models.user.users import User

from app.schemas.payment import (
    CreatePaymentRequest,
    VerifyPaymentRequest,
    PaymentResponse,
    PaymentListResponse,
    RefundResponse,
)

from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# ============================================================
# CREATE PAYMENT
# ============================================================

@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = PaymentService(db)

    try:

        return service.create_payment(
            order_id=str(request.order_id),
            payment_method=request.payment_method.value,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# VERIFY PAYMENT
# ============================================================

@router.post(
    "/verify",
    response_model=PaymentResponse,
)
def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = PaymentService(db)

    try:

        return service.verify_payment(
            request.transaction_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# GET PAYMENT
# ============================================================

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = PaymentService(db)

    try:

        payment = service.get_payment(
            payment_id
        )

        if (
            payment.user_id != current_user.id
            and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )

        return payment

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ============================================================
# LIST USER PAYMENTS
# ============================================================

@router.get(
    "",
    response_model=PaymentListResponse,
)
def list_user_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):

    service = PaymentService(db)

    result = service.list_user_payments(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
    )

    return PaymentListResponse(**result)
# ============================================================
# REFUND PAYMENT
# ============================================================

@router.post(
    "/{payment_id}/refund",
    response_model=RefundResponse,
)
def refund_payment(
    payment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):

    service = PaymentService(db)

    try:

        payment = service.refund(
            payment_id
        )

        return RefundResponse(
            message="Payment refunded successfully.",
            payment=payment,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# WEBHOOK HANDLER
# ============================================================

@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
def payment_webhook(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Razorpay / Payment Gateway Webhook Callback."""
    event = payload.get("event", "payment.captured")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    transaction_id = payment_entity.get("id") or payload.get("transaction_id")
    
    if transaction_id:
        service = PaymentService(db)
        try:
            service.verify_payment(transaction_id)
        except Exception:
            pass
            
    return {"status": "ok", "event": event}
