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

    from app.core.config import settings
    if settings.AI_SERVICE_URL:
        try:
            import httpx
            import time
            t0 = time.perf_counter()
            target_url = settings.AI_SERVICE_URL.rstrip('/')
            if not target_url.endswith('.modal.run') and not target_url.endswith('/predict'):
                target_url = f"{target_url}/predict"

            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    target_url,
                    files={"file": (file.filename, contents, file.content_type)}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_dets = data.get("detections", [])
                    service = DetectionService(db)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    return service.process_remote_detections(
                        remote_dets,
                        image_width=data.get("imageWidth", 640),
                        image_height=data.get("imageHeight", 480),
                        inference_time_ms=latency_ms,
                    )
        except Exception as err:
            from app.core.logging import logger
            logger.warning(f"External AI microservice call to {settings.AI_SERVICE_URL} failed ({err}). Using local engine fallback.")

    image = preprocessor.load_bytes(contents)
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

    from app.core.config import settings
    service = DetectionService(db)

    if settings.AI_SERVICE_URL:
        try:
            import httpx
            import time
            t0 = time.perf_counter()
            target_url = settings.AI_SERVICE_URL.rstrip('/')
            if not target_url.endswith('.modal.run') and not target_url.endswith('/predict'):
                target_url = f"{target_url}/predict"

            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    target_url,
                    files={"file": (file.filename, contents, file.content_type)}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_dets = data.get("detections", [])
                    latency_ms = (time.perf_counter() - t0) * 1000
                    response = service.process_remote_detections(
                        remote_dets,
                        image_width=data.get("imageWidth", 640),
                        image_height=data.get("imageHeight", 480),
                        inference_time_ms=latency_ms,
                    )
                    for item in response.detections:
                        if item.matched_product:
                            try:
                                service.cart.add_product(
                                    user_id=str(current_user.id),
                                    product_id=str(item.matched_product.id),
                                    quantity=1,
                                )
                            except Exception:
                                pass
                    return response
        except Exception as err:
            from app.core.logging import logger
            logger.warning(f"External AI microservice call to {settings.AI_SERVICE_URL} failed ({err}). Using local engine fallback.")

    image = preprocessor.load_bytes(
        contents
    )

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


from pydantic import BaseModel

class RecipeRequest(BaseModel):
    prompt: str
    max_ingredients: int = 6

class RecipeResponse(BaseModel):
    title: str
    prompt: str
    ingredients: list[str]
    steps: list[str]
    products: list[dict]
    source: str

@router.post("/recipe", response_model=RecipeResponse)
def recipe_copilot(
    req: RecipeRequest,
    db: Session = Depends(get_db),
):
    """Recipe Copilot — flan-t5-small (80M) recipe-only LLM + RAG over 1005 products."""
    from app.ai.recipe_service import generate_recipe, match_products

    result = generate_recipe(req.prompt)
    # RAG: match ingredients to products
    products = match_products(result["ingredients"][: req.max_ingredients], db)
    return RecipeResponse(
        title=result["title"],
        prompt=req.prompt,
        ingredients=result["ingredients"],
        steps=result["steps"],
        products=products,
        source=result.get("source", "unknown"),
    )