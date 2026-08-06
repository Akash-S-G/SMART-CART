import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.logging import logger

class CloudinaryService:
    def __init__(self):
        self.is_configured = False
        # Read from environment variables
        cloud_name = settings.CLOUDINARY_CLOUD_NAME
        api_key = settings.CLOUDINARY_API_KEY
        api_secret = settings.CLOUDINARY_API_SECRET

        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            self.is_configured = True
            logger.info("Cloudinary configured successfully.")
        else:
            logger.warning("Cloudinary environment variables not fully set. Falling back to local static paths.")

    def upload_image(self, file_content: bytes, folder: str = "products") -> str | None:
        """
        Uploads image bytes to Cloudinary. Returns the secure URL.
        """
        if not self.is_configured:
            return None
        try:
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=f"smartcart/{folder}",
                resource_type="image"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return None

    def upload_url(self, image_url: str, folder: str = "products") -> str | None:
        """
        Uploads an image URL directly to Cloudinary. Returns the secure URL.
        """
        if not self.is_configured:
            return None
        try:
            upload_result = cloudinary.uploader.upload(
                image_url,
                folder=f"smartcart/{folder}",
                resource_type="image"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary URL upload failed: {e}")
            return None

cloudinary_service = CloudinaryService()
