import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from database.db import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False) # e.g. "openfoodfacts", "blinkit"
    website_url = Column(String, nullable=True)
    license = Column(String, nullable=True)

    products = relationship("Product", back_populates="source")
    images = relationship("Image", back_populates="source")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_brand = Column(String, nullable=True)
    canonical_name = Column(String, nullable=False)
    variant = Column(String, nullable=True) # e.g. "70g" or "Pack of 4"
    barcode = Column(String, index=True, nullable=True)
    category = Column(String, nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    raw_metadata = Column(JSON, nullable=True) # stores raw scraped JSON properties
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    source = relationship("Source", back_populates="products")
    images = relationship("Image", back_populates="product")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    raw_url = Column(String, nullable=True)
    local_path = Column(String, index=True, nullable=False) # relative path in storage/
    sha256 = Column(String, index=True, nullable=False)
    phash = Column(String, index=True, nullable=True)
    quality_score = Column(Float, nullable=True)
    quality_metadata = Column(JSON, nullable=True) # e.g., resolution, blur value
    status = Column(String, default="active") # "active", "rejected", "duplicate"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="images")
    source = relationship("Source", back_populates="images")
    annotations = relationship("Annotation", back_populates="image")
    dataset_links = relationship("DatasetVersionImage", back_populates="image")

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    annotator_plugin = Column(String, nullable=False) # e.g. "grounding_dino", "florence2"
    model_version = Column(String, nullable=True) # version/weights of the annotator model
    bbox = Column(JSON, nullable=False) # bounding box coordinates [x_center, y_center, w, h] normalized
    confidence = Column(Float, nullable=True)
    format = Column(String, default="yolo") # "yolo", "coco", "voc"
    status = Column(String, default="pending") # "pending", "approved", "rejected"
    validator_comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    image = relationship("Image", back_populates="annotations")
    dataset_links = relationship("DatasetVersionImage", back_populates="annotation")

class DatasetVersionImage(Base):
    """Bridge table associating an Image & specific Annotation with a Dataset Version."""
    __tablename__ = "dataset_version_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    annotation_id = Column(Integer, ForeignKey("annotations.id"), nullable=False)
    split = Column(String, nullable=False) # "train", "valid", "test"

    dataset_version = relationship("DatasetVersion", back_populates="image_links")
    image = relationship("Image", back_populates="dataset_links")
    annotation = relationship("Annotation", back_populates="dataset_links")

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_name = Column(String, unique=True, nullable=False) # e.g., "v1.0.0"
    config_used = Column(JSON, nullable=True) # parameters used to generate split
    stats = Column(JSON, nullable=True) # image/annotation count, class distributions
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    image_links = relationship("DatasetVersionImage", back_populates="dataset_version")
    training_runs = relationship("TrainingRun", back_populates="dataset_version")

class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id"), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    hyperparameters = Column(JSON, nullable=True) # e.g. learning rate, epochs
    metrics = Column(JSON, nullable=True) # mAP50, mAP50-95, precision, recall, F1
    logs_path = Column(String, nullable=True)

    dataset_version = relationship("DatasetVersion", back_populates="training_runs")
    models = relationship("ModelVersion", back_populates="training_run")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    training_run_id = Column(Integer, ForeignKey("training_runs.id"), nullable=False)
    version_name = Column(String, unique=True, nullable=False) # e.g., "yolo-v1.0.0"
    model_path = Column(String, nullable=False) # local file path under storage/models/
    status = Column(String, default="experimental") # "experimental", "production"
    deployment_ready = Column(Integer, default=0) # 0 = false, 1 = true
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    training_run = relationship("TrainingRun", back_populates="models")
