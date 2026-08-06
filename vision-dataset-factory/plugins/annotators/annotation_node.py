import os
from typing import Dict, Any, List
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Image, Annotation
from engine.executor import resolve_plugin_class

class AnnotationNode(PipelineNode):
    """Pipeline node that runs auto-annotation on all active, un-annotated images."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.annotator_name = self.config.get("annotator", "plugins.annotators.grounding_dino.GroundingDinoAnnotator")
        self.prompt_template = self.config.get("prompt_template", "product packaging")
        self.min_confidence = self.config.get("min_confidence", 0.5)

    async def execute(self, context: PipelineContext) -> PipelineContext:
        print(f"[AnnotationNode] Initializing annotator plugin: {self.annotator_name}")
        
        # Resolve and instantiate the annotator plugin
        try:
            annotator_cls = resolve_plugin_class(self.annotator_name)
            annotator = annotator_cls(self.name, self.config.get("annotator_config", {}))
        except Exception as e:
            print(f"[AnnotationNode] Failed to resolve annotator plugin: {e}")
            raise

        processed_count = 0
        failed_count = 0
        
        with get_db_session(context.db_path) as session:
            # Query all active images that don't have approved/pending annotations yet
            active_images = session.query(Image).filter_by(status="active").all()
            
            for img in active_images:
                # Skip if already annotated
                existing = session.query(Annotation).filter_by(image_id=img.id).first()
                if existing:
                    # Already annotated, skip
                    continue
                    
                abs_path = os.path.join(context.storage_dir, img.local_path)
                if not os.path.exists(abs_path):
                    continue
                
                # Determine query prompt based on product metadata (brand/name)
                product = img.product
                prompt = self.prompt_template
                if "{product_name}" in prompt:
                    prompt = prompt.replace("{product_name}", product.canonical_name)
                if "{brand}" in prompt:
                    prompt = prompt.replace("{brand}", product.canonical_brand or "")
                    
                try:
                    # Run plugin annotation
                    results = await annotator.annotate(abs_path, prompt)
                    
                    added_ann_count = 0
                    for res in results:
                        bbox = res.get("bbox") # [x, y, w, h] normalized
                        conf = res.get("confidence", 1.0)
                        
                        # Validate bounding box coordinates
                        if not bbox or len(bbox) != 4:
                            continue
                        if conf < self.min_confidence:
                            continue
                            
                        # Ensure within boundaries
                        if any(coord < 0.0 or coord > 1.0 for coord in bbox):
                            print(f"[AnnotationNode] Bbox {bbox} out of boundaries for {img.local_path}. Clipping.")
                            bbox = [min(1.0, max(0.0, coord)) for coord in bbox]
                            
                        # Register Annotation in DB
                        new_ann = Annotation(
                            image_id=img.id,
                            annotator_plugin=self.annotator_name,
                            model_version=self.config.get("model_version", "v1"),
                            bbox=bbox,
                            confidence=conf,
                            format="yolo",
                            status="approved"
                        )
                        session.add(new_ann)
                        added_ann_count += 1
                        
                    if added_ann_count > 0:
                        processed_count += 1
                    else:
                        print(f"[AnnotationNode] No valid annotations generated for {img.local_path}")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"[AnnotationNode] Error annotating {img.local_path}: {e}")
                    failed_count += 1
                    
            session.commit()
            
        print(f"[AnnotationNode] Completed annotation run. Processed: {processed_count}, Failed/Skipped: {failed_count}")
        context.state[f"{self.name}_processed_count"] = processed_count
        context.state[f"{self.name}_failed_count"] = failed_count
        return context
