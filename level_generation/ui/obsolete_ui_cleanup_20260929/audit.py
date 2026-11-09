"""Stage a conservative removal manifest; never edit mounted assets or historical receipts."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import re

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "assets_dev"
HUD = ROOT / "level_generation/ui/hud_inventory"
RASTER = {".png", ".bmp", ".pcx", ".jpg", ".jpeg", ".webp"}
TEXT = {".txt", ".yml", ".yaml", ".lua", ".json", ".ini", ".cfg", ".xml"}
CODE = {".cpp", ".h", ".hpp", ".cc", ".c"}
DORMANT = {f"assets_dev/engine/ui/gameplay/{name}.yml" for name in ("controls", "keyboard", "video_options")}
UNMOUNTED = {"assets_dev/engine/ui/gameplay/gameplay_mobile.yml"}
CONTENT = {"inventory_items", "paperdoll_parts", "fitted_equipment_variants", "player_portrait_frames",
           "npc_portrait_family", "registered_arcomage_atlas", "spellbook_page", "spell_icon_pair",
           "map_presentation"}
UI = {"ui_state_set", "ui_background", "ui_frame_or_panel"}
OLD_CONTROLS = re.compile(r"^(?:context_.+_(?:default|pressed)|"
    r"(?:attack|cast|quick_cast|inventory|pause|resume|ascend_compact|descend_compact|interact)_(?:default|pressed)|"
    r"joystick_(?:base|knob)_(?:default|active))$")
OLD_CHROME = re.compile(r"^(?:basebar(?:_.*)?|topbar|scorebg|status_bar|mtextbar|compass|compcovr|mapframe|"
    r"mana[rbgy]|manafrm|mhp_.+|stat[bgryl]|selring|asi[lr]\d+|skull|wizeye|npcpnl|npc(?:up|dw).+|npcopen.+|"
    r"ui-(?:fr.+|or[rl])|fr_(?:stats|inven|skill|award)|quikref|(?:bt|bl|bv|bu|ar)_.+|"
    r"c_(?:close|ok|cncl|clr|dft)_(?:up|dn|ht)|t_(?:new|load|quit|cred)_(?:up|dn|ht)|"
    r"options|controlbg|optkb|optvid|restmain|rexit.|rdawn.|irbgrnd|irt\d+[rb]|ira-\d+_\d+|"
    r"(?:edge|cornr)_.+|backhand|magnif-[ab]|6load1|hglas\d{3}|ia01-\d{3}|"
    r"cursor|divbar|ib_spelico|statbl)$")
RESERVED = {"obsidian_hud_buff_expiring": "Reserved for the explicitly retained future timed-buff strip."}
TOKEN = re.compile(r"[a-zA-Z0-9_][a-zA-Z0-9_.+-]*")
LITERAL = re.compile(r'"([^"\n]*)"')


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def key(value):
    value = str(value).strip().replace("\\", "/").lower()
    return Path(value).stem if Path(value).suffix in RASTER else value.rsplit("/", 1)[-1]


def main():
    previous = HERE / "removal_manifest.json"
    if previous.exists() and read(previous).get("applied"):
        raise RuntimeError("This applied removal manifest is preserved; write a new audit to a fresh directory.")
    roots = [ASSETS / "engine/icons_x2", ASSETS / "engine/hud_x2", ASSETS / "engine/ui",
             ASSETS / "engine/fonts"]
    for world in sorted((ASSETS / "worlds").iterdir()):
        if world.is_dir():
            roots.extend(world / folder for folder in ("icons", "icons_x2", "ui", "fonts"))
    files = sorted({p for root in roots for p in root.rglob("*") if p.is_file()})
    by_name = defaultdict(list)
    for path in files:
        if path.suffix.lower() in RASTER:
            by_name[path.stem.lower()].append(path)
    names = set(by_name)
    animation_names = set()
    for table in ASSETS.rglob("icon_frame_data.txt"):
        for line in table.read_text().splitlines():
            if line and not line.startswith("//"):
                animation_names.add(line.split("\t", 1)[0].strip().lower())
    relevant_names = names | (animation_names - {""})
    refs = defaultdict(list)
    tokens = defaultdict(list)
    reference_counts = Counter()
    inputs = {}
    dynamic = []
    layouts = []

    def add(name, source, line, kind, detail=""):
        k = key(name)
        if k not in relevant_names:
            return
        reference_counts[k, kind] += 1
        if reference_counts[k, kind] > 16:
            return  # Keep representative evidence per kind; scan all sources for new kinds.
        evidence = dict(source=rel(source), line=line, kind=kind)
        if detail:
            evidence["detail"] = detail
        if evidence not in tokens[k]:
            tokens[k].append(evidence)
        if k in names and evidence not in refs[k]:
            refs[k].append(evidence)

    def scan_yaml(node, source, kind, field=""):
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                if k.value not in {"notes", "description"}:
                    scan_yaml(v, source, kind, k.value)
        elif isinstance(node, yaml.SequenceNode):
            for child in node.value:
                scan_yaml(child, source, kind, field)
        elif isinstance(node, yaml.ScalarNode):
            add(node.value, source, node.start_mark.line + 1, kind, field)

    sources = set()
    for folder in ("game", "engine", "editor"):
        sources.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in CODE)
    packages = [ASSETS / "engine", *sorted((ASSETS / "worlds").iterdir())]
    mods = ASSETS / "mods"
    if mods.exists():
        packages.extend(p for p in mods.iterdir() if p.is_dir())
    for package in packages:
        if not package.is_dir():
            continue
        for folder in ("data_tables", "ui", "events", "scripts", "rendering", "fonts", "effects"):
            sources.update(p for p in (package / folder).rglob("*")
                           if p.is_file() and p.suffix.lower() in TEXT)
        sources.update(p for p in package.iterdir() if p.is_file() and p.suffix.lower() in TEXT)
    print(f"Scanning {len(files)} mounted files against {len(sources)} source/data files.", flush=True)
    for source in sorted(sources):
        path = rel(source)
        inputs[path] = sha(source)
        text = source.read_text(errors="replace")
        if source.name == "icon_frame_data.txt":
            continue  # Resolve animation registrations from their consumers below.
        if source.suffix in CODE:
            # Keep line numbers while excluding commented-out historical references.
            text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m[0].count("\n"), text, flags=re.S)
            for number, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith("//"):
                    continue
                for value in LITERAL.findall(line):
                    add(value, source, number, "code_literal")
                    v = key(value)
                    if re.match(r"^[\w-]{2,}%", v):
                        pattern = re.escape(v)
                        pattern = re.sub(r"%[-+0-9.]*[dui]", r"[0-9]+", pattern)
                        pattern = re.sub(r"%[-+0-9.]*s", r".+", pattern)
                        for name in names:
                            if re.fullmatch(pattern, name):
                                add(name, source, number, "dynamic_format", value)
                    recognition = re.search(r"\.(?:starts_with|ends_with|find)\(", line)
                    if v.endswith("_") and v.startswith(("obsidian_", "omenu_")) and not recognition:
                        dynamic.append((v, source, number))
                    if re.fullmatch(r"ira-[1-4]", v):
                        dynamic.append((v + "_", source, number))
        elif source.suffix.lower() in {".yml", ".yaml"}:
            kind = "unmounted_layout" if path in UNMOUNTED else "dormant_layout" if path in DORMANT else "runtime_yaml"
            doc = yaml.compose(text)
            scan_yaml(doc, source, kind)
            if "/ui/" in path:
                layouts.append(dict(path=path, sha256=inputs[path], status=kind))
        else:
            for number, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith(("//", "--", "#")):
                    continue
                for value in set(TOKEN.findall(line)):
                    add(value, source, number, "runtime_data")
                if source.name == "map_stats.txt":
                    fields = line.split("\t")
                    if len(fields) > 2 and fields[0].isdigit():
                        add(Path(fields[2]).stem, source, number, "map_filename_derived", fields[2])

    for prefix, source, number in dynamic:
        for name in names:
            if name.startswith(prefix):
                add(name, source, number, "dynamic_prefix", prefix)
    print("Source references collected; resolving animation consumers and provenance.", flush=True)

    animation_report = []
    for source in sorted(sources):
        if source.name != "icon_frame_data.txt":
            continue
        groups = defaultdict(list)
        animation = ""
        for number, line in enumerate(source.read_text().splitlines(), 1):
            fields = line.split("\t")
            if len(fields) < 5 or line.startswith("//") or fields[0] == "AnimationName":
                continue
            animation = fields[0].strip().lower() or animation
            groups[animation].append((fields[1].strip(), number))
        for animation, frames in groups.items():
            consumers = [r for r in tokens[animation] if r["kind"] not in {"unmounted_layout", "dormant_layout"}]
            for frame, number in frames:
                add(frame, source, number, "active_animation" if consumers else "animation_registration_only", animation)
            animation_report.append(dict(name=animation, frames=[f for f, _ in frames], consumers=consumers))

    accepted = read(HUD / "accepted_icons.json")
    ledger = {r["runtime_output_path"]: r for r in accepted["records"].values()}
    classification = {r["path"].lower(): r for r in read(HUD / "classification.json")["files"]}
    old_inventory = read(HUD / "inventory.json")
    old_by_name = {r["name"].lower(): r for r in old_inventory["assets"]}
    for metadata in (HUD / "accepted_icons.json", HUD / "classification.json", HUD / "inventory.json"):
        inputs[rel(metadata)] = sha(metadata)

    records = []
    for path in files:
        rp = rel(path)
        name = path.stem.lower()
        origin = ledger.get(rp)
        cl = classification.get(origin["source"].lower(), {}) if origin else {}
        treatment = cl.get("treatment", "")
        historical = old_by_name.get(name, {}).get("usages", [])
        historical_ui = any(r["kind"] in {"yaml", "journal_animation_family"} for r in historical)
        evidence = refs[name] if path.suffix.lower() in RASTER else []
        live = [r for r in evidence if r["kind"] not in
                {"unmounted_layout", "dormant_layout", "animation_registration_only"}]
        dormant = [r for r in evidence if r["kind"] == "dormant_layout"]
        animation_only = [r for r in evidence if r["kind"] == "animation_registration_only"]
        is_ui = bool(treatment in UI or historical_ui or name.startswith("obsidian_")
                     or OLD_CONTROLS.fullmatch(name) or OLD_CHROME.fullmatch(name)
                     or "/hud_x2/" in rp or "/ui/dialogue/" in rp)
        status, reason = "retained", "Non-UI content; outside obsolete UI removal scope."
        if rp in UNMOUNTED:
            status, reason = "stage_removal", "Legacy Android layout is not in either platform's mounted layout list."
        elif rp in DORMANT:
            status, reason = "after_settings_retirement", "Still loaded; old settings handlers must be retired together."
        elif path.suffix.lower() in {".yml", ".yaml"}:
            reason = "Mounted layout, current menu design, configuration or world map catalog."
        elif "/fonts/" in rp or re.fullmatch(r"rude(?:font|black|red|white)", name):
            reason = "Font data or supported font role; retain its explicit native/TTF loading contracts."
        elif name in RESERVED:
            reason = RESERVED[name]
        elif path.suffix.lower() in {".json", ".md"}:
            reason = "Provenance/configuration metadata; not obsolete interface artwork."
        elif re.fullmatch(r"(?:sp109-\d+|sp96h[a-l]|sptext01[a-d])", name):
            reason = "Spell-effect artwork/registrations; outside obsolete UI skin removal scope."
        elif treatment in CONTENT or re.match(r"^(?:[67]?item\d|mm9_item_|[67]?pc\d|npc\d|mapdir\d|micon\d)", name):
            reason = "Protected game content: portraits, equipment, spellbook, maps, FX or Arcomage."
        elif live:
            reason = "Has a current source, layout, data or dynamic-family consumer."
        elif not is_ui:
            status, reason = "review_unresolved", "No current literal reference; insufficient evidence that this is retired UI."
        elif dormant:
            status, reason = "after_settings_retirement", "Only the still-loaded legacy settings layouts refer to this UI art."
        elif animation_only:
            status, reason = "after_animation_retirement", "No consumer found for its animation; registration must be retired explicitly."
        else:
            status, reason = "stage_removal", "Identified UI artwork with no current runtime consumer; obsolete-layout refs excluded."
        record = dict(path=rp, name=name, bytes=path.stat().st_size, sha256=sha(path),
                      status=status, reason=reason, treatment=treatment or ("obsidian_ui" if name.startswith("obsidian_") else ""),
                      references=evidence, historical_ui=historical_ui)
        if origin and status != "retained":
            record["accepted_target"] = origin["target"]
            record["redeploy_index"] = rel(HUD / "accepted_icons.json")
            record["archive_artifact"] = str(Path(origin["artifact"]).relative_to(ROOT))
            record["deployment_note"] = "Retire from deployment before deleting; preserve accepted art and frozen receipts."
        records.append(record)

    # Test/config references are a separate hold, not runtime evidence. Never silently break fixtures.
    candidate_names = {r["name"] for r in records if r["status"] == "stage_removal"}
    test_refs = defaultdict(list)
    for source in sorted((ROOT / "tests").rglob("*")):
        if not source.is_file() or source.suffix not in CODE | TEXT:
            continue
        inputs[rel(source)] = sha(source)
        for number, line in enumerate(source.read_text(errors="replace").splitlines(), 1):
            if line.lstrip().startswith(("//", "#", "--")):
                continue
            for value in LITERAL.findall(line) if source.suffix in CODE else TOKEN.findall(line):
                n = key(value)
                if n in candidate_names:
                    test_refs[n].append(dict(source=rel(source), line=number, kind="test_dependency"))
    for record in records:
        if record["status"] == "stage_removal" and test_refs[record["name"]]:
            record["status"] = "after_test_retirement"
            record["reason"] = "Runtime consumer is gone, but a test/fixture still requests this art."
            record["references"].extend(test_refs[record["name"]])

    summary = {}
    for status in sorted({r["status"] for r in records}):
        group = [r for r in records if r["status"] == status]
        summary[status] = dict(files=len(group), bytes=sum(r["bytes"] for r in group),
                               accepted_deployment_entries=sum(r["path"] in ledger for r in group))
    # Keep complete hashes in the census; avoid repeating portrait/equipment provenance in the UI report.
    ui_records = [r for r in records if r["status"] != "retained" or r["treatment"] in UI
                  or r["historical_ui"] or r["name"].startswith(("obsidian_", "omenu_"))
                  or r["path"].endswith((".yml", ".yaml"))]
    report = dict(schema="openyamm-obsolete-ui-audit-v1", generated_utc=datetime.now(timezone.utc).isoformat(),
                  mode="staged-only; mounted assets and Git index unchanged", summary=summary,
                  census_files=len(records), detailed_records=len(ui_records),
                  evidence_limit="Up to 16 source examples per asset and reference kind; all sources scanned.",
                  scanned_roots=[rel(r) for r in roots if r.exists()], source_files=len(inputs), layouts=layouts,
                  animations=animation_report, records=ui_records)
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
    staged = [r for r in records if r["status"] == "stage_removal"]
    (HERE / "removal_manifest.json").write_text(json.dumps(dict(
        schema="openyamm-obsolete-ui-removal-v1", applied=False,
        prerequisite="Apply the accompanying deployment-retirement change before removing accepted runtime exports.",
        files=staged), indent=2) + "\n")
    (HERE / "remove-files.txt").write_text("".join(r["path"] + "\n" for r in staged))
    with (HERE / "inventory.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["status", "path", "bytes", "sha256"])
        for r in records:
            writer.writerow([r["status"], r["path"], r["bytes"], r["sha256"]])
    print(json.dumps(dict(summary=summary, sources=len(inputs), layouts=len(layouts)), indent=2))


if __name__ == "__main__":
    main()
