from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.ai.model_loader import model_loader
from app.ai.preprocessing import preprocessor
from app.ai.detection_service import DetectionService

from app.ai.schemas import (
    AIHealthResponse,
    DetectionResponse,
)

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user.users import User

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

@router.post(
    "/detect",
    response_model=DetectionResponse,
)
async def detect_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image.",
        )

    contents = await file.read()

    image = preprocessor.load_bytes(
        contents
    )

    service = DetectionService(db)

    return service.detect(image)



@router.post(
    "/detect-and-add",
    response_model=DetectionResponse,
)
async def detect_and_add(
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    if not file.content_type.startswith(
        "image/"
    ):
        raise HTTPException(
            status_code=400,
            detail="File must be an image.",
        )

    contents = await file.read()

    image = preprocessor.load_bytes(
        contents
    )

    service = DetectionService(db)

    return service.detect_and_add(
        image=image,
        user_id=str(current_user.id),
    )

@router.get(
    "/health",
    response_model=AIHealthResponse,
)
def health():

    return AIHealthResponse(

        model_loaded=model_loader.is_loaded(),

        device="cpu",

        model_name="YOLO11n",
    )