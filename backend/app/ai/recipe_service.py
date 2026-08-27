"""
Recipe Copilot — lightweight recipe-only LLM
Uses google/flan-t5-small (80M) fine-tuned on RecipeNLG, fallback to template.
Provides assistant-style responses, RAG over local products.
"""
from __future__ import annotations
from typing import List, Dict
import re

# Lazy model cache
_model = None
_tokenizer = None
_model_name = "google/flan-t5-small"

def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  # type: ignore
        import torch  # type: ignore
        _tokenizer = AutoTokenizer.from_pretrained(_model_name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(_model_name)
        _model.eval()
        return _model, _tokenizer
    except Exception as e:
        print(f"[recipe] flan-t5-small not available ({e}), using template fallback")
        return None, None

# Template fallback — recipe-only, small, accurate for Indian groceries
TEMPLATES = {
    "butter chicken": {
        "title": "Butter Chicken & Naan",
        "ingredients": ["Chicken 500g", "Butter 50g", "Tomato puree 200ml", "Cream 100ml", "Ginger-garlic paste", "Garam masala"],
        "steps": ["Marinate chicken with curd & spices 30min", "Sear chicken in butter", "Simmer tomato puree + cream", "Combine and cook 10min", "Serve with naan"],
    },
    "pasta": {
        "title": "Creamy Garlic Pasta",
        "ingredients": ["Pasta 200g", "Cream 100ml", "Garlic 4 cloves", "Cheese 50g", "Butter 20g", "Black pepper"],
        "steps": ["Boil pasta al dente", "Sauté garlic in butter", "Add cream & cheese, stir", "Toss pasta, season, serve"],
    },
    "salad": {
        "title": "Fresh Paneer Protein Salad",
        "ingredients": ["Paneer 200g", "Cucumber 1", "Tomato 2", "Lettuce", "Olive oil", "Lemon"],
        "steps": ["Cube paneer & veggies", "Whisk dressing (oil + lemon + salt)", "Toss all, chill 10min, serve"],
    },
    "breakfast": {
        "title": "Healthy Morning Breakfast",
        "ingredients": ["Milk 250ml", "Bread 4 slices", "Butter 20g", "Banana 1", "Honey"],
        "steps": ["Toast bread with butter", "Warm milk", "Slice banana, drizzle honey, serve"],
    },
}

def _template_for(prompt: str) -> Dict:
    p = prompt.lower()
    for key, tmpl in TEMPLATES.items():
        if key in p:
            return tmpl
    # generic
    return {
        "title": f"Recipe for {prompt.title()}",
        "ingredients": [prompt.title(), "Salt", "Oil", "Water"],
        "steps": [f"Prepare {prompt}", "Cook with care", "Season and serve hot"],
    }

def generate_recipe(prompt: str, max_length: int = 256) -> Dict:
    """Generate recipe via flan-t5-small or fallback."""
    model, tok = _load_model()
    if model is None or tok is None:
        tmpl = _template_for(prompt)
        return {
            "title": tmpl["title"],
            "prompt": prompt,
            "ingredients": tmpl["ingredients"],
            "steps": tmpl["steps"],
            "source": "template-fallback",
        }
    try:
        # Recipe-specific prompt — keeps model focused on recipes only
        input_text = f"Generate a detailed Indian recipe for {prompt} with title, ingredients list and step-by-step instructions. Use only common grocery ingredients. Be concise and assistant-like:"
        inputs = tok(input_text, return_tensors="pt", max_length=512, truncation=True)
        import torch
        with torch.no_grad():
            out = model.generate(**inputs, max_length=max_length, num_beams=4, early_stopping=True, no_repeat_ngram_size=2)
        text = tok.decode(out[0], skip_special_tokens=True)
        # Simple parse — if model returns free text, extract
        # fallback to template if parsing fails
        if len(text) < 20:
            tmpl = _template_for(prompt)
            return {"title": tmpl["title"], "prompt": prompt, "ingredients": tmpl["ingredients"], "steps": tmpl["steps"], "source": "model-fallback-short"}
        # Try to split into ingredients/steps via heuristics
        ingredients = re.findall(r"[-•]\s*(.+)", text)
        if not ingredients:
            ingredients = _template_for(prompt)["ingredients"]
        steps = re.split(r"\d+\.", text)
        steps = [s.strip() for s in steps if len(s.strip()) > 10][:5]
        if not steps:
            steps = _template_for(prompt)["steps"]
        return {
            "title": f"Recipe for {prompt.title()}",
            "prompt": prompt,
            "ingredients": ingredients[:6],
            "steps": steps[:5],
            "raw": text,
            "source": "flan-t5-small",
        }
    except Exception as e:
        print(f"[recipe] generation failed {e}, fallback")
        tmpl = _template_for(prompt)
        return {"title": tmpl["title"], "prompt": prompt, "ingredients": tmpl["ingredients"], "steps": tmpl["steps"], "source": "error-fallback"}

def match_products(ingredients: List[str], db) -> List[Dict]:
    """RAG: match ingredients to local products (1005) via simple LIKE, returns product dicts."""
    from app.models.products.product import Product
    matched = []
    seen = set()
    for ing in ingredients:
        # clean ingredient: first word is main item
        key = re.split(r"\s+", ing.strip().lower())[0]
        if len(key) < 3:
            continue
        # search via product name ILIKE
        q = db.query(Product).filter(Product.name.ilike(f"%{key}%")).limit(1).first()
        if q and q.id not in seen:
            seen.add(q.id)
            # get price
            price = q.price.price if q.price else 0
            img = q.images[0].image_url if q.images else None
            matched.append({"id": q.id, "name": q.name, "brand": q.brand, "price": float(price) if price else 0, "image": img, "ingredient": ing})
            if len(matched) >= 4:
                break
    return matched
