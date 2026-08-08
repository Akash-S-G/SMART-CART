"""Fetch a sample of catalog images and render an HTML contact sheet.

Quality-review tool: downloads images for a spread of products, saves them
under static/products/_preview/ and writes preview.html so the images can be
eyeballed before committing to a full seed run.
"""

from __future__ import annotations

import html
import io
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from catalog import images as cimg          # noqa: E402
from catalog import imageqc                   # noqa: E402
from catalog.build import build_catalog     # noqa: E402

UA = cimg.UA
OUT = Path(__file__).resolve().parents[1] / "static" / "products" / "_preview"
MIN_BYTES = 3000


def download(url: str, dest: Path) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read()
    except Exception as e:                                    # noqa: BLE001
        return False, f"{type(e).__name__}"
    if len(data) < MIN_BYTES:
        return False, f"too small ({len(data)}B)"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.verify()
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if min(im.size) < 250:
            return False, f"low res {im.size[0]}x{im.size[1]}"
        im.thumbnail((600, 600), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "JPEG", quality=85)
        return True, f"{im.size[0]}x{im.size[1]}"
    except Exception as e:                                    # noqa: BLE001
        return False, f"decode {type(e).__name__}"


def main(per_category: int = 4, want: int = 3) -> None:
    products = build_catalog()
    by_cat: dict[str, list] = {}
    for p in products:
        by_cat.setdefault(p.category, []).append(p)

    rows, ok_n, fail_n = [], 0, 0
    src_count: dict[str, int] = {}
    qc_rej = 0

    for cat in sorted(by_cat):
        for p in by_cat[cat][:per_category]:
            cands = cimg.gather(p, None, want=want)
            saved = []
            for i, c in enumerate(cands, 1):
                slug = "".join(ch if ch.isalnum() else "-"
                               for ch in p.display_name.lower())[:48]
                dest = OUT / f"{slug}-{i}.jpg"
                ok, note = download(c["url"], dest)
                if ok:
                    # pixel-level QC gate -- mirrors what the seeder will do
                    verdict = imageqc.inspect(Image.open(dest).convert("RGB"))
                    if not verdict.ok:
                        ok, note = False, f"qc:{verdict.reason}"
                        qc_rej += 1
                        try:
                            dest.unlink()
                        except OSError:
                            pass
                if ok:
                    ok_n += 1
                    src_count[c["source"]] = src_count.get(c["source"], 0) + 1
                    saved.append((dest.name, c["source"], c["license"], note))
                else:
                    fail_n += 1
            rows.append((p, saved))
            print(f"  {p.display_name:44} {len(saved)}/{len(cands)}")

    cards = []
    for p, saved in rows:
        v = " | ".join(f"{x.size} \u20b9{x.mrp:g}" for x in p.variants)
        imgs = "".join(
            f'<figure><img src="{html.escape(n)}" loading="lazy">'
            f'<figcaption>{html.escape(s)} &middot; {html.escape(note)}</figcaption></figure>'
            for n, s, _lic, note in saved) or '<p class="none">no image</p>'
        cards.append(f"""<article>
  <h3>{html.escape(p.display_name)}</h3>
  <p class="cat">{html.escape(p.category)} &middot; {html.escape(v)}</p>
  <p class="desc">{html.escape(p.desc)}</p>
  <div class="imgs">{imgs}</div>
</article>""")

    summary = " &middot; ".join(f"{k}: {v}" for k, v in sorted(src_count.items()))
    doc = f"""<!doctype html><meta charset="utf-8">
<title>SmartCart - curated catalog image preview</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:24px;background:#0f1115;color:#e6e6e6}}
 h1{{font-size:20px}} .meta{{color:#9aa4b2;margin-bottom:20px}}
 article{{border:1px solid #262b36;border-radius:10px;padding:14px;margin:0 0 14px;background:#151922}}
 h3{{margin:0 0 4px;font-size:15px}}
 .cat{{margin:0 0 6px;color:#7ee787;font-size:12px}}
 .desc{{margin:0 0 10px;color:#9aa4b2;font-size:12.5px}}
 .imgs{{display:flex;gap:10px;flex-wrap:wrap}}
 figure{{margin:0;width:190px}}
 img{{width:190px;height:190px;object-fit:contain;background:#fff;border-radius:8px}}
 figcaption{{font-size:11px;color:#7d8590;margin-top:4px}}
 .none{{color:#f85149}}
</style>
<h1>SmartCart &mdash; curated Indian catalog, image preview</h1>
<p class="meta">{len(rows)} products &middot; {ok_n} images saved, {fail_n} rejected &middot; {summary}</p>
{"".join(cards)}
"""
    (OUT / "preview.html").write_text(doc, encoding="utf-8")
    print(f"\nsaved {ok_n}, download/QC-rejected {fail_n} (QC {qc_rej}) -> {OUT/'preview.html'}")
    print("by source:", src_count)


if __name__ == "__main__":
    main(per_category=int(sys.argv[1]) if len(sys.argv) > 1 else 4)
