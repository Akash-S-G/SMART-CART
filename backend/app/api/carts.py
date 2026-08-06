from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user

from app.db.session import get_db

from app.models.user.users import User

from app.schemas.cart import (
    AddToCartRequest,
    UpdateCartRequest,
    CartResponse,
    MessageResponse,
)

from app.services.cart_service import CartService


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)

@router.get(
    "",
    response_model=CartResponse,
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = CartService(db)

    return service.get_cart(
        str(current_user.id)
    )


@router.post(
    "/items",
    response_model=CartResponse,
)
def add_product(
    request: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = CartService(db)

    try:

        return service.add_product(
            user_id=str(current_user.id),
            product_id=request.product_id,
            quantity=request.quantity,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    


@router.patch(
    "/items/{product_id}",
    response_model=CartResponse,
)
def update_quantity(
    product_id: str,
    request: UpdateCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = CartService(db)

    return service.update_quantity(
        user_id=str(current_user.id),
        product_id=product_id,
        quantity=request.quantity,
    )

@router.delete(
    "/items/{product_id}",
    response_model=CartResponse,
)
def remove_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = CartService(db)

    return service.remove_product(
        str(current_user.id),
        product_id,
    )

@router.delete(
    "",
    response_model=MessageResponse,
)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = CartService(db)

    service.clear_cart(
        str(current_user.id)
    )

    return MessageResponse(
        message="Cart cleared."
    )