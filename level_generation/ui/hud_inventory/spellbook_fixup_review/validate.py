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
        source = Path(path)
        retained = HERE / "installed" / source.name if source.parent == Path("assets_dev/engine/icons_x2") else ROOT / source
        assert digest(retained) == expected, "Retained review source changed: " + path
    base = np.asarray(verify(data["common"]))
    bookmark = verify(data["bookmarks"]["master"])
    bookmark_pixels = np.asarray(bookmark)
    emblem_mask = np.asarray(verify(data["bookmarks"]["emblemMask"]).getchannel("R"))
    outside_emblem = emblem_mask == 0
    assert outside_emblem.sum() > bookmark.width * bookmark.height * .5
    outside = np.asarray(Image.open(HERE / "layers/variable_mask.png")) == 0
    assert int(outside.sum()) > base.shape[0] * base.shape[1] * .95
    count = 0
    changed = []
    for school in data["schools"]:
        page = np.asarray(verify(school["proposed"]))
        assert page.shape == (960, 1280, 4)
        assert np.array_equal(page[outside], base[outside]), school["name"]
        verify(school["installed"])
        for artifact in school["button"]["states"].values():
            verify(artifact)
        button = school["button"]
        assert button["proposedStates"]["default"] == button["proposedStates"]["highlighted"]
        assert button["rect"]["width"] == 48 and button["rect"]["height"] == 39
        for state in ["default", "pressed"]:
            candidate = verify(button["proposedStates"][state])
            emblem = verify(button["emblems"][state])
            assert candidate.size == emblem.size == bookmark.size == (96, 78)
            assert np.array_equal(np.asarray(candidate)[:, :, 3], bookmark_pixels[:, :, 3]), school["key"]
            assert np.array_equal(np.asarray(candidate)[outside_emblem], bookmark_pixels[outside_emblem]), school["key"]
            assert not np.any(np.asarray(emblem)[:, :, 3][outside_emblem]), school["key"]
            assert np.array_equal(np.asarray(Image.alpha_composite(bookmark, emblem)), np.asarray(candidate))
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
            assert verify(spell["normalPalette"]).size == (256, 1)
            if "opacityTrial" in spell:
                assert school["key"] == "Air"
                changed.append(spell["id"])
                trial = spell["opacityTrial"]
                assert digest(ROOT / trial["processingRecord"]) == trial["processingRecordSha256"]
                record = json.loads((ROOT / trial["processingRecord"]).read_text())
                assert record["ink_opacity"] == trial["previousOpacity"]
                restored_alpha = None
                for state, original in [("normal", normal), ("highlighted", colour)]:
                    candidate = verify(trial[state])
                    assert candidate.size == original.size
                    a, b = np.asarray(original), np.asarray(candidate)
                    assert np.array_equal(a[:, :, :3], b[:, :, :3]), "Air colours changed"
                    assert np.array_equal(a[:, :, 3] > 0, b[:, :, 3] > 0), "Air footprint changed"
                    expected = np.uint8(np.rint(np.minimum(255, a[:, :, 3].astype(float) / trial["previousOpacity"])))
                    assert np.array_equal(b[:, :, 3], expected), "Incorrect Air opacity restoration"
                    assert b[:, :, 3].max() == 255 and np.any((b[:, :, 3] > 0) & (b[:, :, 3] < 255))
                    if restored_alpha is not None:
                        assert np.array_equal(b[:, :, 3], restored_alpha), "Air hover alpha differs"
                    restored_alpha = b[:, :, 3]
    for control in data["controls"]:
        for artifact in control["states"].values():
            verify(artifact)
    assert len(data["schools"]) == 12 and count == 111 and len(data["controls"]) == 3
    assert len(data["differentNativeCanvases"]) == 5
    assert digest(HERE / data["font"]["path"]) == data["font"]["sha256"]
    assert digest(HERE / data["approval"]["path"]) == data["approval"]["sha256"]
    approval = json.loads((HERE / data["approval"]["path"]).read_text())
    assert approval["revision"] == data["approval"]["revision"]
    assert set(approval["artwork"]) == set(data["approval"]["targets"]) | set(data["approval"]["reopenedTargets"])
    assert set(changed) == set(data["approval"]["reopenedTargets"])
    assert not set(changed) & set(data["approval"]["targets"])
    assert len(changed) == 9 and len(data["approval"]["targets"]) == 114
    assert len(approval["artwork"]) == 123
    previous_directory = (HERE / data["previousPreview"]).parent
    previous = json.loads((previous_directory / "manifest.json").read_text())
    assert previous["revision"] == data["recipe"]["air_opacity"]["baseline_revision"]
    for school, old_school in zip(data["schools"], previous["schools"]):
        assert school["key"] == old_school["key"]
        assert school["proposed"]["sha256"] == old_school["proposed"]["sha256"], "Background changed"
        assert school["proposed"] == approval["artwork"][school["id"]]["proposed"]
        assert school["button"] == old_school["button"], "Bookmark changed"
        for spell, old_spell in zip(school["spells"], old_school["spells"]):
            assert spell["id"] == old_spell["id"]
            for key in ["canonical", "proposedNormal", "glyphMask", "normalPalette"]:
                assert spell[key] == old_spell[key], "Approved spell changed: " + spell["id"]
                assert spell[key] == approval["artwork"][spell["id"]][key]
    assert data["controls"] == previous["controls"], "Bottom controls changed"
    report = {"result": "PASS", "revision": data["revision"], "schools": 12, "spellPairs": count,
              "verifiedArtworkFiles": len(checked), "verifiedReviewSources": len(data["sources"]),
              "sharedBackgroundOutsideMedallion": True, "identicalSpellAlphaAndDimensions": True,
              "approvedBaselineArtworkUnchanged": True, "approvalTargets": 114, "airPairsReopened": 9,
              "airTrialOnlyChangesAlpha": True, "airTrialRetainsSoftEdgesAndFootprint": True,
              "airTrialAlphaMatchesBetweenStates": True,
              "bookmarkStates": 24, "identicalBookmarkAlpha": True,
              "bookmarkPixelsIdenticalOutsideEmblem": True, "bookmarkLayersRecomposeExactly": True}
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
            previous_air = np.asarray(Image.open(HERE / "evidence/air_previous.png").convert("RGBA"))
            archived_air = np.asarray(Image.open(previous_directory / "evidence/air.png").convert("RGBA"))
            assert np.array_equal(previous_air, archived_air), "Previous-strength comparison differs from baseline"
            restored_air = np.asarray(Image.open(HERE / "evidence/air_restored.png").convert("RGBA"))
            trial_pixels = np.any(restored_air != previous_air, axis=2)
            allowed = np.zeros(trial_pixels.shape, dtype=bool)
            air = next(school for school in data["schools"] if school["key"] == "Air")
            for spell in air["spells"]:
                if "opacityTrial" in spell:
                    rect = spell["rect"]
                    x, y = int(rect["x"] * 2), int(rect["y"] * 2)
                    allowed[y:y + rect["height"] * 2, x:x + rect["width"] * 2] = True
            assert not np.any(trial_pixels & ~allowed), "Air correction changed pixels outside its spell rectangles"
            assert trial_pixels.sum() > 10000, "Air comparison shows no meaningful opacity change"
            hovered_air = np.asarray(Image.open(HERE / "evidence/air_hover.png").convert("RGBA"))
            ys, xs = np.nonzero(np.any(hovered_air != restored_air, axis=2))
            eye = next(spell for spell in air["spells"] if spell["name"] == "Wizard Eye")["rect"]
            assert len(xs) > 1000
            assert xs.min() >= eye["x"] * 2 - 1 and xs.max() < (eye["x"] + eye["width"]) * 2 + 1
            assert ys.min() >= eye["y"] * 2 - 1 and ys.max() < (eye["y"] + eye["height"]) * 2 + 1
            report["browserAirComparisonMatchesBaseline"] = True
            report["browserAirChangesOnlyNineSpellRectangles"] = True
            report["browserAirHoverChangesOnlySpellRectangle"] = True
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/asset_checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
