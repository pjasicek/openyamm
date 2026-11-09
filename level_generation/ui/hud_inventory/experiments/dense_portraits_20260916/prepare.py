"""Prepare density experiments from existing bundles without changing production state."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
UI = HERE.parents[1]
REPO = UI.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    state = json.loads((UI / "checkpoint/state.json").read_text())
    families = {"7pc01": [], "7pc02": []}
    identities = {}
    seen = set()
    for number in range(16, 26):
        bundle = UI / "chat_bundles" / f"restoration_200_{number:03d}"
        manifest = json.loads((bundle / "manifest.json").read_text())
        for sheet in manifest["sheets"]:
            layout = json.loads((bundle / sheet["layout"]).read_text())
            for cell in layout["cells"]:
                frame = cell["target"].get("frame") or {}
                family = frame.get("family")
                if family not in families or cell["id"] in seen:
                    continue
                assert cell["native_size"] == [59, 79]
                assert state["external_assignments"][cell["id"]]["status"] == "assigned"
                assert cell["id"] not in state["cells"]
                assert digest(bundle / cell["original_file"]) == cell["original_sha256"]
                assert digest(REPO / cell["member"]["source_path"]) == cell["original_sha256"]
                assert digest(bundle / cell["native_png"]) == cell["rendered_png_sha256"]
                seen.add(cell["id"])
                families[family].append((frame["ordinal"], bundle, sheet, cell))
                identities.setdefault(family, (bundle, sheet))
    for values in families.values():
        values.sort(key=lambda x: x[0])

    for family, (bundle, sheet) in identities.items():
        dest = HERE / "identity" / family
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundle / sheet["native_identity_reference"], dest / "native-reference.png")
        for name, path in sheet["native_identity_files"].items():
            assert digest(bundle / path) == sheet["native_identity_sources"][name]
            shutil.copy2(bundle / path, dest / name)
        dump(dest / "source_contract.json", sheet)

    configs = [
        ("landscape_72", 12, 6, 36, 36, "3072x2048 landscape"),
        ("portrait_72", 8, 9, 40, 32, "2048x3072 portrait"),
        ("square_63", 9, 7, 36, 27, "2048x2048 square"),
        ("wide_75", 15, 5, 45, 30, "3072x1349 wide landscape"),
        ("tight_81", 9, 9, 45, 36, "2304x3072 portrait"),
    ]
    summary = []
    for name, columns, rows, count_a, count_b, requested in configs:
        if len(sys.argv) > 1 and name not in sys.argv[1:]:
            continue
        dest = HERE / name
        dest.mkdir(exist_ok=True)
        assert not (dest / "raw.png").exists(), "Do not overwrite a submitted experiment"
        chosen = families["7pc01"][:count_a] + families["7pc02"][:count_b]
        # Native-coordinate cells have two pixels of padding on every side.
        # Square experiment uses six extra native pixels of exterior horizontal margin.
        outer_x = 7 if name == "square_63" else 0
        cell_w, cell_h, padding = (60, 80, 0.5) if name == "tight_81" else (63, 83, 2)
        native_size = (columns * cell_w + outer_x * 2, rows * cell_h)
        canvas = Image.new("RGB", (native_size[0] * 2, native_size[1] * 2), (255, 0, 255))
        records = []
        for index, (_, bundle, sheet, cell) in enumerate(chosen):
            x = outer_x + (index % columns) * cell_w + padding
            y = (index // columns) * cell_h + padding
            source = bundle / cell["native_png"]
            with Image.open(source) as im:
                assert im.size == (59, 79)
                canvas.paste(im.convert("RGB").resize((118, 158), Image.Resampling.NEAREST), (int(2*x), int(2*y)))
            copies = dest / "sources"
            copies.mkdir(exist_ok=True)
            shutil.copy2(source, copies / source.name)
            records.append(dict(id=cell["id"], slot=index + 1,
                                family=cell["target"]["frame"]["family"],
                                native_rect=[x, y, 59, 79], reference_rect=[2*x, 2*y, 118, 158],
                                original_bundle=bundle.name, original_sheet=sheet["id"],
                                source_png=f"sources/{source.name}", original_contract=cell))
        canvas.save(dest / "reference.png")
        group_rows = count_a // columns
        prompt = f"""Use case: identity-preserve. Faithful restoration of an existing Might and Magic game portrait atlas.
Image 1 is the edit target: exactly {columns} columns by {rows} rows, {len(chosen)} occupied rectangular portrait cells, ordered left to right then top to bottom. Restore this entire atlas in place. Do not simplify the grid, omit, duplicate, merge, reorder, enlarge or recenter any cell.
The first {group_rows} full rows depict ONE character; the remaining rows depict a SECOND character. Image 2 is original native identity reference for the first character; image 3 is original native identity reference for the second. Those two supporting images are identity context only, not extra output cells or approved restorations. Keep identities separate. Each cell's own native expression, gaze, eyelid closure, mouth opening, head angle, wounds, skin color and clothing are authoritative, including unusual expression/effect frames. Do not normalize expressions into repeated neutral faces.
Every cell is a complete opaque 59x79-native-pixel portrait including its original painted background. Each is shown at 2x only for legibility in the input. Reconstruct finer continuous painted contours, hair, facial shading and material detail while preserving the original subdued game-art style and exact facial proportions. No enlarged pixel blocks, blur-only smoothing, photographic restyling, beautification, invented accessories or exaggerated eyes/teeth.
Preserve all cell boundaries and gutters precisely. Magenta RGB 255,0,255 belongs only in the narrow gutters and exterior padding; preserve every portrait's dark opaque background edge to edge. No new borders, labels, numbers, grid lines, checkerboards or shadows. Do not crop hair/chins or change framing. Keep the whole sheet's aspect ratio.
Request output {requested}, or the largest available raster of this aspect ratio, restoring all cells with equal attention. The target is at least 118x158 actual generated pixels inside EACH portrait rectangle before any later resampling, preferably more. Produce one restored atlas image, not a preview montage or separate pictures.
"""
        (dest / "prompt.txt").write_text(prompt)
        manifest = dict(name=name, grid=[columns, rows], target_count=len(chosen),
                        reference_size=list(canvas.size), native_sheet_size=list(native_size),
                        requested_output=requested, minimum_uniform_scale=2.0,
                        status="prepared_not_generated", interpretation="density experiment; not production acceptance",
                        reference="reference.png", reference_sha256=digest(dest / "reference.png"),
                        identity_references=["../identity/7pc01/native-reference.png", "../identity/7pc02/native-reference.png"],
                        prompt="prompt.txt", prompt_sha256=digest(dest / "prompt.txt"), cells=records)
        dump(dest / "manifest.json", manifest)
        dump(dest / "submission.json", dict(prompt=prompt, referenced_image_paths=[str(dest / "reference.png"),
             str(HERE / "identity/7pc01/native-reference.png"), str(HERE / "identity/7pc02/native-reference.png")]))
        summary.append({k:v for k,v in manifest.items() if k not in ("cells", "identity_references")})
    dump(HERE / ("experiments_boundary.json" if len(sys.argv) > 1 else "experiments.json"), summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
