"""
Script to detect and remove non-English / foreign supermarket products
from PostgreSQL (local smartcart DB).
Cascades deletion cleanly across all dependent child tables:
- product_images
- product_prices
- inventory
- product_weights
- product_detection
- cart_items
- order_items
- reviews
- wishlists
- inventory_transactions
"""

import re
from sqlalchemy import create_engine, text

# Comprehensive foreign vocabulary covering French, German, Spanish, Italian, Dutch OpenFoodFacts items
FOREIGN_PATTERNS = [
    # French articles and functional words
    r'\b(de|des|du|le|la|les|au|aux|et|pour|avec|sans|sur|dans|d|l)\b',
    # French food vocabulary
    r'\b(pomme|pommes|chocolat|noir|lait|fraise|fraises|cerise|cerises|myrtille|myrtilles|abricot|abricots|citron|citrons|carotte|carottes|avocat|avocats|poire|poires|figue|figues|mangue|mangues|pasteque|ananas|framboise|framboises|peche|peches|noisette|noisettes|amande|amandes|pruneaux|dattes|raisins|noix|coco)\b',
    r'\b(compote|compotes|confiture|confitures|gourdes|rapees|aromatise|sauvage|sauvages|moelleux|moelleuses|entiers|morceaux|sirop|jus|saveur|vinaigre|farine|creme|fromage|croquettes|viande|poisson|legumes|huile|tranches|bocal|denoyautes|noyaux|pepites)\b',
    # German functional words and foods
    r'\b(und|aus|mit|fuer|nach|ohne|von|der|die|das|dem|den|ein|eine|einen)\b',
    r'\b(apfel|apfelsaft|beeren|beerenmischung|datteln|feigen|zitronen|kirschen|erdbeeren|himbeeren|tomaten|gehackte|schokolade|kaese|kase|milch|brot|mehl|entsteint|getrocknet|aprikosen|pflaumen|kokoschips|heidelbeeren)\b',
    # Spanish functional words and foods
    r'\b(para|con|sin|por|del|las|los|desecadas|hueso|ciruelas|fresas|manzana|manzanas|limon|limones|aceite|leche|queso|galletas|rallado|carne|perro|gato|conejo|pollo|naranjas|yogur)\b',
    # Dutch / Scandinavian
    r'\b(kattensnack|zalmsmaak|vis selectie|groente|bosbessen|in gelei|op sap|laks|aardbeien|epler)\b',
    # Italian
    r'\b(salmone|alimento gato|alimento cane|fragole|confettura)\b',
    # Other foreign keywords
    r'\b(banane|bananes)\b'
]

compiled = [re.compile(p, re.IGNORECASE) for p in FOREIGN_PATTERNS]

def is_foreign(name: str) -> bool:
    name_lower = name.lower()
    # Exceptions that are standard English
    if 'coconut' in name_lower:
        name_clean = name_lower.replace('coconut', '')
    else:
        name_clean = name_lower

    for pat in compiled:
        if pat.search(name_clean):
            return True
    return False

def run(dry_run: bool = False):
    engine = create_engine('postgresql+psycopg://smartcart_user:777@localhost:5432/smartcart')
    
    with engine.connect() as conn:
        products = conn.execute(text("""
            SELECT id, sku, name 
            FROM products 
            WHERE sku NOT LIKE 'VIS%' 
              AND name NOT LIKE '%Product 0%' 
              AND name NOT LIKE '%Product 1%';
        """)).fetchall()

    to_delete = []
    for p_id, sku, name in products:
        if is_foreign(name):
            to_delete.append((p_id, sku, name))

    print(f"Total catalog products analyzed: {len(products)}")
    print(f"Foreign products identified for deletion: {len(to_delete)}")
    
    if dry_run:
        print("Dry run - sample of products that would be deleted:")
        for d in to_delete[:20]:
            print(f"  {d[1]}: {d[2]}")
        return

    del_ids = [d[0] for d in to_delete]
    if not del_ids:
        print("No foreign products to delete.")
        return

    with engine.begin() as conn:
        # Delete from all referencing child tables
        child_tables = [
            'product_images',
            'product_prices',
            'inventory',
            'product_weights',
            'product_detection',
            'cart_items',
            'order_items',
            'reviews',
            'wishlists',
            'inventory_transactions'
        ]
        
        for table in child_tables:
            conn.execute(
                text(f"DELETE FROM {table} WHERE product_id = ANY(:ids);"),
                {'ids': del_ids}
            )
            print(f"Cleaned references from {table}")

        # Also clean from cloud schema table if present
        conn.execute(
            text("DELETE FROM cloud.product_images WHERE product_id = ANY(:ids);"),
            {'ids': del_ids}
        )

        # Delete from products
        res = conn.execute(
            text("DELETE FROM products WHERE id = ANY(:ids);"),
            {'ids': del_ids}
        )
        print(f"Successfully deleted {res.rowcount} non-English products from `products` table.")

if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
