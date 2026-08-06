import pytest
from core.context import RecognitionContext, Detection
from recognition.pipeline import RecognitionPipeline
from recognition.aggregators import ConfidenceAggregator
from recognition.unknown_queue import UnknownProductQueue
from providers.mock_providers import MockBarcode, MockOCR, MockEmbedder, MockRetriever
from registry.mock_client import MockRegistryClient

class MockImage:
    pass

def test_happy_path_aggregation():
    # Setup dependencies
    barcode = MockBarcode()
    ocr = MockOCR()
    embedder = MockEmbedder()
    retriever = MockRetriever()
    registry = MockRegistryClient()
    aggregator = ConfidenceAggregator()
    unknown_queue = UnknownProductQueue("storage/test_unknown")
    
    pipeline = RecognitionPipeline(
        barcode_reader=barcode,
        ocr=ocr,
        embedder=embedder,
        retriever=retriever,
        registry=registry,
        aggregator=aggregator,
        unknown_queue=unknown_queue,
        confidence_threshold=0.85
    )
    
    # Create mock context
    ctx = RecognitionContext(
        image=MockImage(),
        detection=Detection(bbox=[0,0,10,10], confidence=0.9, class_name="product"),
        camera_id="cam_1"
    )
    
    # Run pipeline
    result = pipeline.process(ctx)
    
    # Verify
    assert result is not None
    assert result.product_id == "12345"
    assert result.source == "aggregated"
    
    # Check that aggregation boosted the score (Barcode 1.0 * 1.0 + OCR 0.9 * 0.95 * 0.15 + Embedding 0.88 * 0.1)
    # Expected: 1.0 + (0.855 * 0.15) + 0.088 = 1.0 + 0.12825 + 0.088 = 1.21625
    assert result.score > 1.2

def test_unknown_queue_routing():
    # Setup dependencies with a strict threshold
    barcode = MockBarcode()
    ocr = MockOCR()
    embedder = MockEmbedder()
    retriever = MockRetriever()
    registry = MockRegistryClient()
    aggregator = ConfidenceAggregator()
    unknown_queue = UnknownProductQueue("storage/test_unknown")
    
    pipeline = RecognitionPipeline(
        barcode_reader=barcode,
        ocr=ocr,
        embedder=embedder,
        retriever=retriever,
        registry=registry,
        aggregator=aggregator,
        unknown_queue=unknown_queue,
        confidence_threshold=5.0  # Impossible threshold
    )
    
    class BadImage(MockImage):
        barcode = "000"
        ocr_text = "UNKNOWN"
        
    ctx = RecognitionContext(
        image=BadImage(),
        detection=Detection(bbox=[0,0,10,10], confidence=0.9, class_name="product"),
        camera_id="cam_1"
    )
    
    result = pipeline.process(ctx)
    
    # Should be rejected to unknown queue
    assert result is None
