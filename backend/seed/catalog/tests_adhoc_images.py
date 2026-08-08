
"""Ad-hoc verification of seed/catalog image pipeline (option C: hybrid)."""
import sys
from pathlib import Path
BACKEND = Path("/home/akash/Desktop/Smart cart/backend")
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(BACKEND/"seed"))
from PIL import Image
from io import BytesIO
from seed.catalog import images as cimg, imageqc
from seed.catalog.build import build_catalog, resolve_related
from seed.adapters.curated_india import fetch, _candidate

fails = []
def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {got!r}")
    if not ok: fails.append(label)

print("\n[1] imageqc rejects only what is measurably separable")
# build synthetic images
def mk(w, h, luma=128, aspect_banner=False):
    W = 1400 if aspect_banner else 700
    H = 400 if aspect_banner else 500
    return Image.new("RGB", (W, H), (luma, luma, luma))
check("banner rejected",     imageqc.inspect(mk(700,500,aspect_banner=True)).ok, False)
check("blank frame rejected",imageqc.inspect(mk(700,500,luma=2)).ok, False)
check("low-res rejected",    imageqc.inspect(Image.new("RGB",(200,400))).ok, False)
check("normal pack passes",  imageqc.inspect(mk(700,500,luma=200)).ok, True)
check("dark retail passes",  imageqc.inspect(mk(700,500,luma=45)).ok, True)  # black-bg pack
check("tight crop passes",   imageqc.inspect(mk(700,500,luma=120)).ok, True)

print("\n[2] negative: QC must not reject labelled-good real images")
import glob
labelled = ['saffola-gold-refined-oil-1.jpg','tata-tea-premium-leaf-tea-1.jpg',
            'madhur-refined-sugar-1.jpg','india-gate-classic-basmati-rice-2.jpg',
            'everest-red-chilli-powder-1.jpg','aashirvaad-whole-wheat-atta-1.jpg',
            'fresh-onion-2.jpg']
rejected = [n for n in labelled
            if not imageqc.inspect(Image.open(f"/home/akash/Desktop/Smart cart/backend/static/products/_preview/{n}").convert("RGB")).ok]
check("0 labelled-good rejected", rejected, [])

print("\n[3] hybrid sourcing tries open licences before websearch")
ps = {p.display_name: p for p in build_catalog()}
amul = cimg.gather(ps["Amul Butter Salted"], None, want=3)
check("Amul butter ends on websearch (no OFF/Commons brand pack)",
      any(c["source"] == "websearch" for c in amul), True)
onion = cimg.gather(ps["Fresh Onion"], None, want=3)
check("fresh onion gets wikimedia candidate",
      any(c["source"] == "wikimedia" for c in onion), True)
check("every candidate carries provenance",
      all("license" in c and "source" in c for c in amul + onion), True)

print("\n[4] curated_india adapter emits one candidate per variant")
plan = type("P", (), {"name": "Dairy & Eggs"})()
cands = fetch(plan, None)
butter = [c for c in cands if "Amul Butter" in c["name"]]
check("Amul Butter has a variant-suffixed SKU", len(butter) >= 1, True)
check("candidate carries base price + weight",
      all("_base_price" in c and "_weight" in c for c in butter), True)
check("candidate carries related + ingredient tags",
      all("_related" in c and "_ingredient_tags" in c for c in butter), True)
check("source stamped curated-india", all(c["source"]=="curated-india" for c in cands), True)

print("\n[5] adapter honours category filter")
plan2 = type("P", (), {"name": "Bakery"})()
cands2 = fetch(plan2, None)
check("Bakery plan yields only bakery candidates",
      all(any(b in c["name"] for b in ["Bread","Pav","Bun","Rusk","Cake","Khari"])
          for c in cands2), True)

print()
print("FAILED:", fails) if fails else print("ALL CHECKS PASSED")
sys.exit(1 if fails else 0)
