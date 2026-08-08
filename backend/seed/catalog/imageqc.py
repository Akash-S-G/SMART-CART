"""Pixel-level quality control for fetched product images.

Deliberately minimal, and that is an empirical result rather than laziness.

Thresholds were calibrated against a hand-labelled sample of 67 fetched images
(labels from visual inspection).  Measuring the labelled sets showed that most
intuitive "quality" signals do **not** separate good pack shots from junk:

    signal              good range        junk range        usable?
    corner luma         45 - 238          0 - 130           no, overlaps
    corner uniformity   1% - 85%          19% - 100%        no, overlaps
    corner saturation   14 - 88           0 - 14            no, inverted
    aspect ratio        1.17 - 1.56       1.34 - 2.01       yes, above ~1.75
    short edge          >= 300px          236 - 299px       yes

Retailers shoot on black, on grey, in-scene and tightly cropped, so a
"bright uniform backdrop" is simply not a quality signal for e-commerce
imagery.  Trying to enforce one rejected 44/67 images including shots
independently judged textbook-perfect.

Blur detection was also tried and removed: edge-variance scored the blurry
sample at 2587 against 2977-4295 for good shots -- too close to threshold
without causing false positives.

So this module only rejects what is measurably separable: banner aspect
ratios, tiny images, and fully blank frames.  Everything else is left to
ImageStore's perceptual-hash dedup and human review.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_SIDE = 300          # below this the image is an upscaled thumbnail
MAX_ASPECT = 1.75       # above this it is a banner/strip, not a pack shot
BLANK_LUMA = 6          # a frame this dark everywhere is a failed render


@dataclass
class Verdict:
    ok: bool
    reason: str = ""
    detail: str = ""

    def __bool__(self) -> bool:
        return self.ok


def _luma(p) -> float:
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def _mean_luma(img) -> float:
    small = img.resize((32, 32))
    px = list(small.getdata())
    return sum(_luma(p) for p in px) / len(px)


def inspect(img) -> Verdict:
    """Run every check that measurably works against a PIL RGB image."""
    w, h = img.size

    if min(w, h) < MIN_SIDE:
        return Verdict(False, "low-res", f"{w}x{h}")

    aspect = max(w, h) / max(1, min(w, h))
    if aspect > MAX_ASPECT:
        return Verdict(False, "banner-aspect", f"{aspect:.2f}")

    mean = _mean_luma(img)
    if mean < BLANK_LUMA:
        return Verdict(False, "blank-frame", f"luma {mean:.1f}")

    return Verdict(True, "ok", f"{w}x{h} luma {mean:.0f}")
