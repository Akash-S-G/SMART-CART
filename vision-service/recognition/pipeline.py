from typing import Optional, List
from core.context import RecognitionContext
from core.models import ProductCandidate
from interfaces.barcode import BarcodeInterface
from interfaces.ocr import OCRInterface
from interfaces.embedder import EmbedderInterface
from interfaces.retriever import RetrieverInterface
from registry.client import ProductRegistryClient
from recognition.aggregators import ConfidenceAggregator
from recognition.unknown_queue import UnknownProductQueue

class RecognitionPipeline:
    def __init__(
        self,
        barcode_reader: BarcodeInterface,
        ocr: OCRInterface,
        embedder: EmbedderInterface,
        retriever: RetrieverInterface,
        registry: ProductRegistryClient,
        aggregator: ConfidenceAggregator,
        unknown_queue: UnknownProductQueue,
        confidence_threshold: float = 0.85
    ):
        self.barcode = barcode_reader
        self.ocr = ocr
        self.embedder = embedder
        self.retriever = retriever
        self.registry = registry
        self.aggregator = aggregator
        self.unknown_queue = unknown_queue
        self.threshold = confidence_threshold

    def process(self, context: RecognitionContext) -> Optional[ProductCandidate]:
        candidates: List[ProductCandidate] = []
        
        # 1. Barcode signal
        bc_str = self.barcode.decode(context.image)
        if bc_str:
            bc_cand = self.registry.lookup_barcode(bc_str)
            if bc_cand:
                candidates.append(bc_cand)
                
        # 2. OCR signal
        text, text_conf = self.ocr.extract(context.image)
        if text and text_conf > 0.5:
            ocr_cands = self.registry.search_keywords(text)
            for c in ocr_cands:
                # Modulate registry score by OCR read confidence
                c.score *= text_conf 
                candidates.append(c)
                
        # 3. Embedding signal
        vec = self.embedder.encode(context.image)
        if vec is not None:
            raw_retrieved = self.retriever.search(vec)
            embed_cands = self.registry.search_embedding(raw_retrieved)
            candidates.extend(embed_cands)
            
        # 4. Aggregation
        final_candidate = self.aggregator.aggregate(candidates)
        
        if final_candidate and final_candidate.score >= self.threshold:
            return final_candidate
            
        # 5. Route to Unknown Queue
        self.unknown_queue.enqueue(context, candidates)
        return None
