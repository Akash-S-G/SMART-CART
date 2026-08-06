import torch
import numpy as np
from PIL import Image
from typing import Any
from transformers import AutoProcessor, AutoModel
from interfaces.embedder import EmbedderInterface
from core.models import ProviderMetadata

class SigLIPEmbedder(EmbedderInterface):
    def __init__(self, model_id: str = "google/siglip-base-patch16-224"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load in float16 to save memory (if on CUDA, else use float32 or bfloat16)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id, torch_dtype=dtype).to(self.device)
        self.model.eval()
        
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="siglip", version="transformers", capabilities={"dimensions": 768, "dtype": "float16/32"})
        
    def encode(self, image: Any) -> np.ndarray:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
            
        try:
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            if torch.cuda.is_available():
                inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
                
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                
            if hasattr(outputs, "image_embeds"):
                outputs = outputs.image_embeds
            elif hasattr(outputs, "pooler_output"):
                outputs = outputs.pooler_output
            elif hasattr(outputs, "last_hidden_state"):
                outputs = outputs.last_hidden_state
                
            # If shape is (batch, patches, dim), mean pool over patches
            if len(outputs.shape) == 3:
                outputs = outputs.mean(dim=1)
                
            # Normalize the embedding for FAISS cosine similarity
            embedding = outputs[0].cpu().numpy()
            embedding = embedding / np.linalg.norm(embedding)
            return embedding
        except Exception as e:
            print(f"SigLIP Error: {e}")
            return np.zeros(768)
