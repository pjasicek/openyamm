#!/usr/bin/env python3
"""Package the approved journal without writing to runtime mounts or Git's index."""
import hashlib
import json
import shutil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]
OVERLAYS = REVIEW.parent / "obsidian_overlays_20260928/staging"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = []
    font_differences = []

    def copy(source, relative, role, pinned=False):
        destination = HERE / relative
        if pinned and destination.exists() and digest(destination) != digest(source):
            raise RuntimeError(f"Pinned source changed: {relative}. Rebase explicitly before preparing again.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
        receipts.append(dict(path=relative, source=str(source.relative_to(ROOT)), sha256=digest(destination), role=role))
        return destination

    source_manifest = json.loads((REVIEW / "asset_manifest.json").read_text())
    assert source_manifest["status"] == "approved-design-01-unmounted-runtime-draft"
    for asset in source_manifest["assets"]:
        source = REVIEW / asset["path"]
        assert digest(source) == asset["sha256"], f"Unrecorded asset change: {source}"
        copy(source, str(Path(asset["target"]).relative_to("assets_dev")), "Approved journal graphics")
    copy(REVIEW / "drafts/journal.yml", "engine/ui/gameplay/journal.yml", "Runtime layout draft")
    copy(REVIEW / "reference_layouts/journal.yml", "reference_layouts/journal.yml", "Pre-integration layout", True)

    # Retain native glyph outlines, FNT spacing and baseline data. Only Autonote's ink presentation changes.
    for name in ["book2", "autonote", "create", "smallnum", "lucida"]:
        font = ROOT / f"assets_dev/engine/fonts/truetype/openyamm_{name}_faithful.ttf"
        reviewed_font = REVIEW / f"assets/fonts/{name}.ttf"
        copy(reviewed_font, f"engine/fonts/truetype/{font.name}", "Exact reviewed faithful MM font")
        if digest(font) != digest(reviewed_font):
            font_differences.append(dict(face=name, reviewed_sha256=digest(reviewed_font),
                                        current_runtime_sha256=digest(font), current_runtime_path=str(font.relative_to(ROOT)),
                                        action="Compare later font changes during integration; do not bulk-overwrite newer fonts"))
        descriptor = ROOT / f"assets_dev/engine/fonts/truetype/{name}.yml"
        copy(descriptor, f"reference_fonts/{name}.yml", "Original descriptor", True)
        staged = copy(descriptor, f"engine/fonts/truetype/{name}.yml", "Faithful MM descriptor")
        if name == "autonote":
            document = yaml.safe_load(staged.read_text())
            document["presentation"] = "tintable"
            staged.write_text("# Approved dark journal: native outlines/metrics with tintable ivory coverage.\n"
                              + yaml.safe_dump(document, sort_keys=False))
            receipts[-1].update(sha256=digest(staged), operation="Only presentation: black-ink -> tintable")
        for folder in ["icons", "english_text"]:
            matches = [p for p in (ROOT / f"assets_dev/engine/fonts/{folder}").iterdir()
                       if p.stem.lower() == name and p.suffix.lower() == ".fnt"]
            assert len(matches) == 1, f"Missing or ambiguous {folder}/{name} metrics"
            copy(matches[0], f"engine/fonts/{folder}/{matches[0].name}", "Native FNT metrics")

    for filename in ["fondamento-regular.ttf", "fondamento.yml", "fondamento-ofl.txt"]:
        copy(OVERLAYS / f"engine/fonts/truetype/{filename}", f"engine/fonts/truetype/{filename}",
             "Shared approved Fondamento face, descriptor and license")
    assert digest(HERE / "engine/fonts/truetype/fondamento-regular.ttf") == digest(REVIEW / "assets/fonts/fondamento.ttf")

    for filename in ["app.js", "style.css", "index.html", "content.js"]:
        copy(REVIEW / filename, f"masters/review_source/{filename}", "Approved browser source snapshot")
    copy(REVIEW.parent / "hud_overlay_study_20260927/button-theme.css",
         "masters/review_source/button-theme.css", "Approved shared button recipe")
    for filename in ["generation_prompts.json", "generated_sources.json", "asset_sources.json",
                     "review_geometry.json", "exported_assets.json", "browser_review.json"]:
        copy(REVIEW / filename, "masters/" + filename, "Source provenance or measured geometry")
    for filename in ["map", "quests", "story", "notes", "notes-fountain", "notes-obelisk", "notes-seer",
                     "notes-misc", "notes-trainer", "status", "browser-review"]:
        copy(REVIEW / f"previews/{filename}.png", f"approved_previews/{filename}.png", "Approved visual reference")

    geometry = json.loads((REVIEW / "review_geometry.json").read_text())
    theme = dict(
        design="carved-obsidian-journal-r01", approved="2026-09-28", logical_canvas=[640, 480],
        review_scale=1.875, map_viewport=[131, 101, 300, 300], text_viewport=[101, 96, 360, 293],
        text_to_submenu_gap=dict(logical=28.066667, reference="test_img/2105.png",
                                 treatment="Narrow body to 360 logical; retain submenu positions, button sizes and font size"),
        palette=dict(body="#e5dcc7", title="#e4c793", page_count="#b4ad95", coordinates="#d0c7b0"),
        fonts=dict(title=dict(face="Book2", size=30, min_title_size=22.4),
                   body=dict(face="AUTONOTE", native_height=18, scale=0.9, presentation="tintable"),
                   map_fields=dict(face="Create", native_height=18),
                   page_count=dict(face="SMALLNUM", native_height=14),
                   buttons=dict(face="Fondamento", descriptor_height=32, scale="label logical height / 32"),
                   status_specimen=dict(face="Lucida", native_height=17, review_logical_size=16.2)),
        live_content="Keep current tables, unlock checks, localization, substitution and native pagination.",
        body_alignment=dict(mode="justify", views=["quests", "story", "notes"], distribution="inter-word",
                            paragraph_final_line="left", single_line_entries="left", automatic_hyphenation=False,
                            page_continuation="Justify the page's last line when its paragraph continues",
                            runtime="Shared native text layout needs justification; current align_x supports left/center/right",
                            comparison="Browser-only Body alignment control; default justify"),
        map=dict(zoom_levels=[384, 768, 1536], button_zoom="Recentre on party", wheel_zoom="Retain native behavior",
                 panning=True, notes="Existing visible discovered pins, hover/selection and coordinates",
                 border=dict(asset="obsidian_journal_map_frame", rect=[118.2, 88.2, 325.6, 325.6],
                             transparent_interior=True, changes_hit_region=False)),
        backdrop=dict(asset="obsidian_journal_backdrop_tile", draw="Repeat behind the full viewport; centre pattern",
                      logical_tile_size=[550/1.875, (550*690/362)/1.875], stretch=False,
                      root_shadow="black, 70 review pixels of blur behind centred journal"),
        entry_divider=dict(asset="obsidian_journal_entry_divider", width_fraction=0.8,
                           height=7/1.875, separation=35/1.875, top_offset=14/1.875,
                           views=["quests", "notes"]),
        page_count="Native page / total; hidden for map and empty content",
        icon_drawing="Contain within measured child bounds; preserve master alpha and aspect ratio",
        status_specimen=dict(asset="obsidian_journal_status_strip", scope="2090 strip treatment only",
                             integration="Apply within current creation status slot; no full creation layout replacement",
                             review_rect=[200, 391, 1200, 82], text_padding=[31/1.875, 23/1.875]),
        geometry="masters/review_geometry.json", runtime_installed=False)
    states = dict(
        schema="Design contract; disabled/state text styles are not UiLayoutManager asset keys",
        state_priority=["disabled", "pressed", "hover", "selected", "normal"],
        labels=dict(normal="#e8d1a4", hover="#fff0c0", pressed="#d7bc86", selected="#ffe3a8", disabled="#888b7b"),
        label_pressed_shift_y=1/1.875, transition_ms=110, pressed_transition_ms=0,
        preserve_selection_while_hovering=True,
        families={family: {state: f"obsidian_journal_{family}_{state}" for state in
                           ["normal", "hover", "pressed", "selected", "disabled"]}
                  for family in ["main", "category", "page", "close"]},
        renderer="Use parent input/selection state for its plate, noninteractive label and icon children",
        disabled="No activation or page/zoom overflow; select explicit disabled PNG in renderer",
        text_shadow_recipe="masters/review_source/button-theme.css",
        measured_button_children={key: geometry[key] for key in
                                  ["#main-navigation button", "#note-categories button", "#page-controls button",
                                   "map_controls", "#close"]})
    (HERE / "design").mkdir(exist_ok=True)
    for name, document in [("theme", theme), ("button_states", states)]:
        (HERE / f"design/{name}.yml").write_text("# Approved design specification; not live UI schema.\n"
                                               + yaml.safe_dump(document, sort_keys=False, width=112))

    approval = dict(design="carved-obsidian-journal-r01", approved_date="2026-09-28",
                    user_instruction="OK I like this, prepare it", status="approved-design-staged-for-integration",
                    views=["map", "quests", "story", "autonotes: all six categories", "2090 status-strip specimen"],
                    runtime_installed=False,
                    previews=[dict(path=r["path"], sha256=r["sha256"]) for r in receipts
                              if r["role"] == "Approved visual reference"])
    approval["refinements"] = [dict(user_instruction='maybe it should be "block" aligned. instead of only to the left. the text bodies.',
                                   change="Justified body paragraphs with natural left-aligned final lines",
                                   previous_baseline="history/r01-left-aligned/approval.json")]
    approval["refinements"].append(dict(reference="test_img/2105.png",
                                       user_instruction="very little free space between the submenu buttons",
                                       change="Wider text-to-submenu gap: 28.07 instead of 11.07 logical pixels",
                                       previous_baseline="history/r01-before-wider-gutter/approval.json"))
    (HERE / "approval.json").write_text(json.dumps(approval, indent=2) + "\n")
    (HERE / "runtime_font_differences.json").write_text(json.dumps(font_differences, indent=2) + "\n")
    (HERE / "asset_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(f"Prepared approved journal: {len(source_manifest['assets'])} PNGs, one layout, six font faces.")


if __name__ == "__main__":
    main()
