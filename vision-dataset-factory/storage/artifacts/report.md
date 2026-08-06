# Autonomous Product Knowledge Base Report - Indian Groceries

Generated on: 2026-07-09 13:05:45

---

## 1. Executive Summary

- **Dataset Health Score**: **100/100**
- **Deployment Readiness Score**: **90/100**
- **Total Product Families**: 20
- **Total Active Images**: 93 (100% Real, 0% Synthetic, 0% Pre-augmented)
- **Deduplicated Images**: 0
- **Rejected Images**: 5

---

## 2. Product Knowledge Base Datasets

The final outputs are packaged under `storage/datasets/`:
1. **`detection/`**: Contains YOLO directory structure with train/val/test splits and `data.yaml`.
2. **`ocr/`**: Crop images of product text and variants mapped to text values.
3. **`barcodes/`**: Crop images of product barcodes mapped to decoded string IDs.
4. **`reference_gallery/`**: One canonical front-facing catalog view per product family for visual search reference.
5. **`embeddings/`**: 512-dimensional visual embeddings (e.g. CLIP) for few-shot lookups.
6. **`product_metadata/`**: Canonical JSON registries (products, brands, aliases, packaging, categories).

---

## 3. Coverage & Quality Gates Analysis

### Class Distribution (Real Images Only)
- **Parle-G**: 9 active images
- **Marie Gold**: 7 active images
- **Good Day**: 5 active images
- **KitKat**: 2 active images
- **Dairy Milk**: 3 active images
- **Maggi Masala**: 2 active images
- **Yippee Magic Masala**: 0 active images
- **Thums Up**: 3 active images
- **Sprite**: 6 active images
- **Coca-Cola**: 3 active images
- **Pepsi**: 2 active images
- **Bisleri**: 7 active images
- **Amul Butter**: 12 active images
- **Amul Taaza**: 11 active images
- **Nandini Milk**: 9 active images
- **Aashirvaad Atta**: 0 active images
- **Fortune Sunflower Oil**: 9 active images
- **Surf Excel**: 0 active images
- **Colgate**: 2 active images
- **Lux Soap**: 1 active images

- **Max class size**: 12 images
- **Min class size**: 0 images
- **Class Imbalance Ratio**: 0.00x (Target: $\le 5x$)

### Environment Scene Coverage
- **Catalog / Front-facing**: 19.35% (Target: $\le 30\%$)
- **Shelf Clutter**: 22.58% (Target: $\ge 30\%$)
- **Checkout Counter**: 35.48% (Target: $\ge 20\%$)
- **Handheld / Occlusion**: 22.58% (Target: $\ge 20\%$)

> [!NOTE]
> Class distribution is balanced and satisfies the < 5x Success Gate.

---

## 4. Failure Gallery (Worst Images)

The following images were rejected during quality filtration:
- **Image ID 18**: https://images.openfoodfacts.org/images/products/890/106/309/2853/front_en.4.full.jpg | Reason: `low_resolution` | Resolution: `600x264`
- **Image ID 25**: https://images.openfoodfacts.org/images/products/762/220/233/4009/front_en.9.full.jpg | Reason: `low_resolution` | Resolution: `496x1016`
- **Image ID 33**: https://images.openfoodfacts.org/images/products/317/478/000/0363/front_fr.152.full.jpg | Reason: `low_resolution` | Resolution: `144x520`
- **Image ID 39**: https://images.openfoodfacts.org/images/products/317/478/000/0363/front_fr.152.full.jpg | Reason: `low_resolution` | Resolution: `144x520`
- **Image ID 44**: https://images.openfoodfacts.org/images/products/317/478/000/0363/front_fr.152.full.jpg | Reason: `low_resolution` | Resolution: `144x520`

---

## 5. Multi-Modal Product Lineage Trace

The following trace shows the direct lineage from the exported dataset records back to the source metadata:

#### Image ID: 1
- **Local File Path**: `raw/img_1_9a8dd28071.jpg`
- **SHA256**: `9a8dd28071eb5d09fd894b88b568d2c90e2f8b212cd8b5c082af92758a68999f`
- **pHash**: `cfce6b2a6e791b1f`
- **Camera Angle**: `top`
- **Estimated Occlusion**: `0.0`
- **Product Name**: `Parle-G`
- **Product Brand**: `Parle`
- **Visible OCR metadata**: `None`
- **Barcode GTIN metadata**: `None`
- **Provenance Scraped**: `openfoodfacts (https://openfoodfacts.com)`

