
"""Ad-hoc verification of seed/catalog (curated Indian manifest).

Offline: no network, no DB. Negative cases use deliberately-broken fixtures to
prove each gate actually rejects, rather than only passing on good data.
"""
import sys
from pathlib import Path

BACKEND = Path("/home/akash/Desktop/Smart cart/backend")
sys.path.insert(0, str(BACKEND))

from seed.catalog import recipes as rmod
from seed.catalog.build import (build_catalog, validate_catalog, check_duplicates,
                                check_recipe_coverage, check_related_refs,
                                check_category_floor, resolve_related, sku_counts)
from seed.catalog.schema import CatalogError, P, Product, Variant, slugify

fails = []
def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got={got!r}")
    if not ok: fails.append(label)

def raises(label, fn):
    try:
        fn(); check(label, "no error", "CatalogError")
    except CatalogError:
        print(f"  PASS  {label}: raised CatalogError")
    except Exception as e:
        check(label, type(e).__name__, "CatalogError")

CAT = build_catalog()

print("\n[1] manifest loads and every product self-validates")
check("products loaded", len(CAT) > 0, True)
check("all validate", all(p.validate() is None for p in CAT), True)
check("skus == sum(variants)", sum(len(p.variants) for p in CAT),
      sum(sku_counts(CAT).values()))

print("\n[2] positive gates on the real manifest")
check("no duplicate SKUs", check_duplicates(CAT), [])
check("recipe coverage complete", check_recipe_coverage(CAT), [])
check("related refs all resolve", check_related_refs(CAT), [])
check("every product has a description", all(len(p.desc) >= 20 for p in CAT), True)
check("every product has >=1 variant", all(p.variants for p in CAT), True)
check("every product has an image query",
      all(p.query_for(p.variants[0]).strip() for p in CAT), True)
check("all prices in INR band",
      [f"{p.display_name} {v.mrp}" for p in CAT for v in p.variants
       if not 5.0 <= v.mrp <= 5000.0], [])

print("\n[3] NEGATIVE: duplicate detection actually rejects")
dup = P("Butter Salted", "Amul", "Dairy & Eggs", [("100 g", 58)], "x"*25)
check("duplicate pair flagged", len(check_duplicates(CAT + [dup])), 1)
check("clean manifest still clean", check_duplicates(CAT), [])

print("\n[4] NEGATIVE: recipe gate rejects an unstocked ingredient")
orig = rmod.RECIPES[:]
try:
    rmod.RECIPES.append(rmod.R("Fake Dish", "Test", ["unobtainium spice"]))
    miss = check_recipe_coverage(CAT)
    check("unstocked ingredient flagged", len(miss), 1)
    check("names the culprit", "unobtainium" in miss[0], True)
finally:
    rmod.RECIPES[:] = orig
check("coverage restored after cleanup", check_recipe_coverage(CAT), [])

print("\n[5] NEGATIVE: related-ref gate rejects a dangling name")
bad = P("Ghost Item", "Testco", "Bakery", [("1 kg", 50)], "y"*25,
        related=["Totally Nonexistent Product XYZ"])
check("dangling ref flagged", len(check_related_refs(CAT + [bad])), 1)

print("\n[6] NEGATIVE: price + schema validation")
raises("MRP too high rejected", lambda: Variant("1 kg", 99999).validate("t"))
raises("MRP too low rejected",  lambda: Variant("1 kg", 0.5).validate("t"))
raises("short desc rejected",   lambda: P("A", "B", "C", [("1 kg", 50)], "tiny").validate())
raises("no variants rejected",  lambda: P("A", "B", "C", [], "z"*25).validate())
raises("bad unit rejected",
       lambda: P("A", "B", "C", [("1 kg", 50)], "z"*25, unit="furlong").validate())
raises("dup variant size rejected",
       lambda: P("A", "B", "C", [("1 kg", 50), ("1 KG", 60)], "z"*25).validate())

print("\n[7] related resolution maps generic names to real SKUs")
rel = resolve_related(CAT)
check("Spinach -> a paneer product",
      any("Paneer" in x for x in rel["Fresh Spinach"]), True)
check("Banana -> a milk product",
      any("Milk" in x for x in rel["Fresh Banana"]), True)
check("no product relates to itself",
      [k for k, v in rel.items() if k in v], [])

print("\n[8] category floor gate is wired and honest")
check("floor gate reports the partial slice", len(check_category_floor(CAT)) > 0, True)
check("floor=1 passes on current slice", check_category_floor(CAT, minimum=1), [])
raises("strict validate raises while slice is partial",
       lambda: validate_catalog(CAT, strict_floor=True))
rep = validate_catalog(CAT, strict_floor=False)
check("non-floor validate clean", rep["errors"], [])

print("\n[9] india/grocery sanity")
check("every product has a category", all(p.category for p in CAT), True)
check("no placeholder names",
      [p.name for p in CAT if p.name.lower().startswith("product ")], [])
check("recipes all have ingredients", all(r.ingredients for r in rmod.RECIPES), True)
check("slugify is ascii-safe", slugify("Amul  Gold-Milk!! 1L"), "amul gold milk 1l")

print()
print(f"FAILED {fails}" if fails else f"ALL CHECKS PASSED "
      f"({len(CAT)} products / {sum(len(p.variants) for p in CAT)} SKUs / "
      f"{len(rmod.RECIPES)} recipes)")
sys.exit(1 if fails else 0)
