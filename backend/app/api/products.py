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

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryResponse,
)

from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    try:

        product = service.create_product(request)

        return product

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
@router.get(
    "/categories",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
):
    from app.models.products.categories import Category
    return db.query(Category).all()


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    return service.list_products(
        skip=skip,
        limit=limit,
    )

@router.get(
    "/search/",
    response_model=list[ProductResponse],
)
def search_products(
    keyword: str,
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    return service.search_products(keyword)

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    try:

        return service.get_product(product_id)

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: str,
    request: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    try:

        return service.update_product(
            product_id,
            request,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    service.delete_product(product_id)


class RestockRequest(BaseModel):
    quantity: int

@router.post(
    "/{product_id}/restock",
    response_model=ProductResponse,
)
def restock_product(
    product_id: str,
    request: RestockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from app.models.products.inventory import Inventory
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        inv = Inventory(product_id=product_id, quantity=request.quantity)
        db.add(inv)
    else:
        inv.quantity += request.quantity
    db.commit()
    service = ProductService(db)
    return service.get_product(product_id)



