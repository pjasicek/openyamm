"""Check review artifacts and prove that the source files remain unchanged."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads((HERE / "manifest.json").read_text())
    checked = set()

    def verify(artifact):
        if artifact["path"] not in checked:
            path = HERE / artifact["path"]
            assert digest(path) == artifact["sha256"], path
            checked.add(artifact["path"])
        return Image.open(HERE / artifact["path"]).convert("RGBA")

    for path, expected in data["sources"].items():
        assert digest(ROOT / path) == expected, "Source changed: " + path
    base = np.asarray(verify(data["common"]))
    outside = np.asarray(Image.open(HERE / "layers/variable_mask.png")) == 0
    assert int(outside.sum()) > base.shape[0] * base.shape[1] * .95
    count = 0
    for school in data["schools"]:
        page = np.asarray(verify(school["proposed"]))
        assert page.shape == (960, 1280, 4)
        assert np.array_equal(page[outside], base[outside]), school["name"]
        verify(school["installed"])
        for artifact in school["button"]["states"].values():
            verify(artifact)
        for spell in school["spells"]:
            count += 1
            colour, normal = verify(spell["canonical"]), verify(spell["proposedNormal"])
            assert colour.size == normal.size, spell["name"]
            assert colour.getchannel("A").tobytes() == normal.getchannel("A").tobytes(), spell["name"]
            assert (np.asarray(colour)[:, :, 3] == 0).any(), spell["name"]
            assert np.any(np.asarray(colour)[:, :, :3] != np.asarray(normal)[:, :, :3]), spell["name"]
            for artifact in spell["states"].values():
                verify(artifact)
            verify(spell["glyphMask"])
    for control in data["controls"]:
        for artifact in control["states"].values():
            verify(artifact)
    assert len(data["schools"]) == 12 and count == 111 and len(data["controls"]) == 3
    assert len(data["differentNativeCanvases"]) == 5
    assert digest(HERE / data["font"]["path"]) == data["font"]["sha256"]
    report = {"result": "PASS", "revision": data["revision"], "schools": 12, "spellPairs": count,
              "verifiedArtworkFiles": len(checked), "unchangedSourceFiles": len(data["sources"]),
              "sharedBackgroundOutsideMedallion": True, "identicalSpellAlphaAndDimensions": True}
    browser_path = HERE / "evidence/browser_checks.json"
    if browser_path.exists():
        browser = json.loads(browser_path.read_text())
        if browser["revision"] == data["revision"]:
            before = np.asarray(Image.open(HERE / "evidence/fire_normal.png").convert("RGB"))
            after = np.asarray(Image.open(HERE / "evidence/fire_hover.png").convert("RGB"))
            change = np.any(before != after, axis=2)
            ys, xs = np.nonzero(change)
            aura = next(spell for spell in data["schools"][0]["spells"]
                        if spell["id"] == "SpellbookPageFireSpellFireaura")
            rect = aura["rect"]
            assert len(xs) > 1000, "Browser hover did not change the spell"
            assert xs.min() >= rect["x"] * 2 - 1 and xs.max() < (rect["x"] + rect["width"]) * 2 + 1
            assert ys.min() >= rect["y"] * 2 - 1 and ys.max() < (rect["y"] + rect["height"]) * 2 + 1
            report["browserHoverChangesOnlySpellRectangle"] = True
            report["hoverChangedPixels"] = len(xs)
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/asset_checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
