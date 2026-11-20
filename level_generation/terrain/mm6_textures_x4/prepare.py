"""Prepare the complete MM6 texture queue and verify existing artwork; never install runtime assets."""

import hashlib
import html
import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
INVENTORY = BASE.parent / "mm6_texture_inventory_20261008.json"
TEMPLE = BASE.parent / "mm6_abandoned_temple_textures"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def image_index(directory):
    return {path.stem.lower(): path for path in directory.iterdir()
            if path.suffix.lower() in (".bmp", ".png")}


def main():
    source = json.loads(INVENTORY.read_text())
    face_names = set(source["remaining_names"]) | set(source["temple_prepared"])
    terrain_names = set(source["terrain"])
    names = face_names | terrain_names
    assert len(face_names) == source["counts"]["all"] == 1507
    assert len(terrain_names) == source["counts"]["terrain_used_separately"] == 120
    assert len(names) == 1622

    native_indexes = [image_index(ROOT / directory) for directory in (
        "reference/mmerge_data_forus/Data/mm6.bitmaps.lod",
        "assets_dev/worlds/mm6/textures",
        "reference/mmerge_data_forus/Data/mm7.bitmaps.lod",
        "reference/mmerge_data_forus/Data/bitmaps.lod",
    ) if (ROOT / directory).is_dir()]
    runtime_indexes = [image_index(ROOT / "assets_dev/worlds/mm6" / directory)
                       for directory in ("textures_x2", "terrain_x2")]
    selected = json.loads((TEMPLE / "corrected_x4_manifest.json").read_text())
    temple_rows = {row["name"]: row for row in selected["selected"]}
    assert set(temple_rows) == set(source["temple_prepared"])
    decisions_path = BASE / "decisions.json"
    decisions = json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
    selections_path = BASE / "selections.json"
    selections = json.loads(selections_path.read_text()) if selections_path.exists() else {}
    assert set(selections) <= names
    rows = []
    for directory in ("references/native", "exports_x4", "review"):
        (BASE / directory).mkdir(parents=True, exist_ok=True)

    for name in sorted(names):
        native = next((index[name] for index in native_indexes if name in index), None)
        runtime = next((index[name] for index in runtime_indexes if name in index), None)
        row = {"name": name, "status": "pending",
               "scope": [kind for kind, pool in (("face", face_names), ("terrain", terrain_names)) if name in pool],
               "indoor_maps": source["indoor"].get(name, []),
               "outdoor_building_maps": source["outdoor_buildings"].get(name, []),
               "terrain_maps": source["terrain"].get(name, []),
               "event_scripts": source["event_states"].get(name, []),
               "wrap_axes": None, "family": None, "artwork_bounds": None,
               "acceptance": {"new_detail": False, "native_fidelity": False,
                              "source_budget": False, "alpha": False,
                              "continuity": False, "brightness_finish": False,
                              "runtime_scale": False, "runtime_appearance": False}}
        if native:
            with Image.open(native) as image:
                row["native_size"] = list(image.size)
                guide = BASE / "references/native" / (name + ".png")
                if not guide.exists():
                    image.convert("RGBA").save(guide)
                assert Image.open(guide).size == image.size, name
            row.update(native_source=relative(native), native_sha256=digest(native),
                       native_reference=relative(guide), reference_sha256=digest(guide),
                       target_x4_size=[value * 4 for value in row["native_size"]])
        else:
            row["status"] = "native_source_unresolved"
        if runtime:
            row.update(esrgan_x2_source=relative(runtime), esrgan_x2_sha256=digest(runtime),
                       esrgan_x2_size=list(Image.open(runtime).size))
        if name in temple_rows:
            chosen = temple_rows[name]
            old_export = TEMPLE / "runtime_corrected_x4" / (name + ".png")
            assert digest(old_export) == chosen["runtime_sha256"], name
            assert Image.open(old_export).size == tuple(value * 4 for value in chosen["native_size"]), name
            for component in chosen["sources"]:
                master = TEMPLE / component["source"]
                assert digest(master) == component["source_sha256"], master
                assert Image.open(master).size == tuple(component["source_size"]), master
                assert (TEMPLE / component["prompt"]).is_file(), component
            export = BASE / "exports_x4" / (name + ".png")
            if not export.exists():
                shutil.copyfile(old_export, export)
                export.chmod(0o644)
            assert digest(export) == chosen["runtime_sha256"], name
            row.update(status="prepared_x4", export=relative(export), export_sha256=digest(export),
                       native_size=chosen["native_size"], target_x4_size=chosen["runtime_size"],
                       provenance_manifest=relative(TEMPLE / "corrected_x4_manifest.json"),
                       construction=chosen["construction"],
                       runtime_review=relative(TEMPLE / "review/material_correction_x4/index.html"),
                       runtime_review_limit="Temple tested; shared-map appearances still require checks")
            row["acceptance"] = {key: True for key in row["acceptance"]}
        if name in selections:
            chosen = selections[name]
            assert set(chosen["acceptance"]) == set(row["acceptance"]), name
            assert all(chosen["acceptance"].values()), name
            export = BASE / chosen["export"]
            assert export.parent == BASE / "exports_x4", export
            assert digest(export) == chosen["export_sha256"], name
            assert Image.open(export).size == tuple(row["target_x4_size"]), name
            for component in chosen["sources"]:
                master = BASE / component["source"]
                assert "generated" in master.parts, master
                assert digest(master) == component["source_sha256"], master
                assert Image.open(master).size == tuple(component["source_size"]), master
                left, top, right, bottom = component["crop"]
                width, height = component["source_size"]
                assert 0 <= left < right <= width and 0 <= top < bottom <= height, component
                assert right - left >= component["target_size"][0], component
                assert bottom - top >= component["target_size"][1], component
            alias = chosen.get("native_equivalent_to")
            if alias:
                alias_native = BASE / "references/native" / (alias + ".png")
                assert digest(alias_native) == row["reference_sha256"], name
                alias_runtime = next((index[alias] for index in runtime_indexes if alias in index), None)
                assert alias_runtime and digest(alias_runtime) == row["esrgan_x2_sha256"], name
            review = BASE / chosen["runtime_review"]
            assert review.is_file(), review
            assert digest(review) == chosen["runtime_review_sha256"], name
            row.update(status="prepared_x4", export=relative(export), export_sha256=digest(export),
                       provenance_manifest=relative(selections_path), construction=chosen["construction"],
                       runtime_review=relative(review), runtime_review_limit=chosen["runtime_review_limit"])
            row["acceptance"] = chosen["acceptance"]
        if name in decisions:
            row["authoring"] = decisions[name]
            if row["status"] != "prepared_x4":
                row["status"] = decisions[name].get("status", row["status"])
        rows.append(row)

    maps = sorted((ROOT / "assets_dev/worlds/mm6/maps").glob("*.blv"))
    maps += sorted((ROOT / "assets_dev/worlds/mm6/maps").glob("*.odm"))
    counts = Counter(row["status"] for row in rows)
    report = {"objective": "Prepare x4+ masters for the complete MM6 texture inventory",
              "inventory_source": relative(INVENTORY), "inventory_sha256": digest(INVENTORY),
              "playbook": "level_generation/terrain/TEXTURE_RESTORATION_PLAYBOOK.md",
              "counts": {"face_names": len(face_names), "terrain_names": len(terrain_names),
                         "shared_face_terrain_names": len(face_names & terrain_names),
                         "total_unique_names": len(rows), "by_status": dict(counts)},
              "map_sources": [{"file": relative(path), "sha256": digest(path)} for path in maps],
              "completion": False, "textures": rows}
    assert len(rows) == len({row["name"] for row in rows}) == len(names)
    assert sum(counts.values()) == len(names)
    assert all(row.get("export") for row in rows if row["status"] == "prepared_x4")
    assert {path.stem for path in (BASE / "exports_x4").glob("*.png")} == {
        row["name"] for row in rows if row["status"] == "prepared_x4"}
    (BASE / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")

    cards = []
    for row in rows:
        reference = row.get("native_reference")
        picture = (f'<img loading="lazy" src="../../../{html.escape(reference)}" alt="Native {row["name"]}">'
                   if reference else '<p>Native source unresolved</p>')
        uses = len(set(row["indoor_maps"] + row["outdoor_building_maps"] + row["terrain_maps"]))
        cards.append(f'<article data-state="{row["status"]}"><b>{row["name"]}</b>{picture}'
                     f'<small>{row.get("native_size", "?")} → {row.get("target_x4_size", "?")}</small>'
                     f'<small>{uses} maps · {row["status"]}</small></article>')
    page = '''<!doctype html><meta charset="utf-8"><title>MM6 x4+ texture inventory</title>
<style>body{background:#171c20;color:#e8e1d3;font:16px system-ui;margin:24px}input,select{font:inherit;margin:12px}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
article{background:#262c30;padding:12px}img{display:block;width:100%;height:160px;object-fit:contain;image-rendering:pixelated}
small{display:block;margin-top:6px;color:#bec4c8}a{color:#d6b779}</style>
<h1>MM6 x4+ master production</h1><p>Native layout references; these thumbnails are not generated artwork.</p>
<p>1622 unique names: 1507 face names and 120 terrain names, with five shared. Verified prepared exports: ''' + str(
        counts["prepared_x4"]) + '''. Imported Temple exports: 62.</p>
<p>Generated candidates, art checks and native runtime checks remain separate. Water/animation requires complete sequences.</p>
<input id="search" placeholder="Texture name"><select id="state"><option value="">All states</option>
<option>pending</option><option>candidate</option><option>prepared_x4</option><option>native_source_unresolved</option></select>
<main>''' + "\n".join(cards) + '''</main><script>
const search=document.querySelector('#search'),state=document.querySelector('#state');
function filter(){for(const card of document.querySelectorAll('article'))card.hidden=!(card.querySelector('b').textContent.includes(search.value.toLowerCase())&&(!state.value||card.dataset.state===state.value));}
search.addEventListener('input',filter);state.addEventListener('change',filter);
</script>'''
    (BASE / "index.html").write_text(page)
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
