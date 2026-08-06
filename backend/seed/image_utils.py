"""Image downloading, validation, normalization and deduplication.

All images are stored locally under backend/static/products/ and served via the
FastAPI /static mount (added in main.py). Each product gets a folder named by
sku; inside it we keep `thumbnail.jpg` plus `gallery_1.jpg`, `gallery_2.jpg`...

Deduplication uses an average (perceptual) hash on the normalised thumbnail so
visually identical images are not saved twice.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import config as cfg

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False


def normalized_ext() -> str:
    return ".jpg"


def _average_hash(img: Image.Image, bits: int = cfg.DEDUP_HASH_BITS) -> str:
    """Compute an average (perceptual) hash of a PIL image."""
    img = img.convert("L").resize((bits, bits), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    return "".join("1" if p > avg else "0" for p in pixels)


class ImageStore:
    """Downloads, validates, normalises and stores images on local disk."""

    def __init__(self, http, progress=None, stats=None):
        self.http = http
        self.progress = progress
        self.stats = stats
        self.imgs_root: Path = cfg.IMAGES_ROOT
        self.imgs_root.mkdir(parents=True, exist_ok=True)
        # global cache of perceptual hashes -> first saved rel url
        self._seen_hashes: dict[str, str] = {}

    # ---- public ---------------------------------------------------------- #
    def store_product_images(self, sku: str, urls: list[str]) -> dict:
        """Download + store images for one product.

        Returns dict with keys:
          thumbnail (str|None), gallery (list[str]),
          downloaded (int), failed (int), deduped (int)
        URLs are de-duplicated (same URL string) before download.
        """
        folder = self.imgs_root / sku
        folder.mkdir(parents=True, exist_ok=True)

        seen_urls: set[str] = set()
        ordered: list[str] = []
        for u in urls:
            if not u:
                continue
            if u in seen_urls:
                continue
            seen_urls.add(u)
            ordered.append(u)

        thumb_rel: str | None = None
        gallery_rel: list[str] = []
        downloaded = 0
        failed = 0
        deduped = 0

        idx = 0
        for url in ordered:
            idx += 1
            ok, rel, reason = self._store_one(folder, sku, url, idx)
            if ok:
                downloaded += 1
                if thumb_rel is None:
                    thumb_rel = rel
                else:
                    gallery_rel.append(rel)  # type: ignore[arg-type]
            elif reason == "duplicate":
                deduped += 1
            else:
                failed += 1
            if self.stats is not None:
                if ok:
                    self.stats.images_downloaded += 1
                    self.stats.images_validated += 1
                elif reason == "duplicate":
                    self.stats.images_deduped += 1
                else:
                    self.stats.images_failed += 1
            if self.progress is not None:
                self.progress.image(idx, len(ordered), ok, reason if not ok else "")

        return {
            "thumbnail": thumb_rel,
            "gallery": gallery_rel,
            "downloaded": downloaded,
            "failed": failed,
            "deduped": deduped,
        }

    # ---- internal -------------------------------------------------------- #
    def _store_one(self, folder: Path, sku: str, url: str, idx: int):
        resp = self.http.get_bytes(url)
        if not resp.ok:
            return False, None, f"http {resp.status}"
        data = resp.body
        if len(data) < cfg.MIN_IMAGE_BYTES:
            return False, None, "too small"
        if not _HAS_PIL:
            # Fallback: save raw bytes without validation.
            dest = folder / f"gallery_{idx}{normalized_ext()}"
            dest.write_bytes(data)
            return True, self._rel(sku, dest), ""

        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except Exception:  # noqa: BLE001
            return False, None, "not an image"

        w, h = img.size
        if w < cfg.MIN_IMAGE_DIM or h < cfg.MIN_IMAGE_DIM:
            return False, None, "tiny dims"

        # Normalize: longest edge -> TARGET_THUMB, RGB, JPEG.
        img = img.convert("RGB")
        long_edge = max(w, h)
        if long_edge > cfg.TARGET_THUMB:
            scale = cfg.TARGET_THUMB / float(long_edge)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        try:
            ah = _average_hash(img)
        except Exception:  # noqa: BLE001
            ah = hashlib.md5(data).hexdigest()

        if ah in self._seen_hashes:
            return False, None, "duplicate"

        # name file: thumbnail is always gallery_1 for first valid, etc.
        fname = f"gallery_{idx}{normalized_ext()}"
        dest = folder / fname
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88, optimize=True)
        img_bytes = buf.getvalue()
        dest.write_bytes(img_bytes)

        # Upload to Cloudinary if credentials are provided in env
        from app.services.cloudinary_service import cloudinary_service
        if cloudinary_service.is_configured:
            cloud_url = cloudinary_service.upload_image(img_bytes, folder=f"products/{sku}")
            if cloud_url:
                self._seen_hashes[ah] = cloud_url
                if self.stats is not None:
                    self.stats.images_validated += 1
                return True, cloud_url, ""

        rel = self._rel(sku, dest)
        self._seen_hashes[ah] = rel
        if self.stats is not None:
            self.stats.images_validated += 1
        return True, rel, ""

    def _rel(self, sku: str, dest: Path) -> str:
        rel = f"{sku}/{dest.name}"
        base = cfg.ENV_STATIC_BASE_URL.rstrip("/")
        return f"{base}/{rel}"
