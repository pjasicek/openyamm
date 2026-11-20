"""Prepare review files and an unapplied deployment patch from the audited removal set."""
from collections import Counter
from pathlib import Path
import difflib
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / "level_generation/ui/hud_inventory"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    manifest = json.loads((HERE / "removal_manifest.json").read_text())
    if manifest.get("applied"):
        raise RuntimeError("Removal already applied; preserve this handoff and its recovery manifest.")
    audit = json.loads((HERE / "inventory.json").read_text())
    candidates = manifest["files"]
    patch_dir = HERE / "staged"
    patch_dir.mkdir(exist_ok=True)
    records = {
        r["accepted_target"]: dict(runtime_output_path=r["path"], sha256=r["sha256"], reason=r["reason"])
        for r in candidates if "accepted_target" in r
    }
    retirement = dict(schema="openyamm-runtime-icon-retirements-v1", count=len(records),
                      audit_manifest=str((HERE / "removal_manifest.json").relative_to(ROOT)), records=records)
    retirement_path = patch_dir / "runtime_retirements.json"
    write_json(retirement_path, retirement)

    original = (HUD / "deploy_icons.py").read_text()
    updated = original.replace(
        "INDEX=HUD/'accepted_icons.json'",
        "INDEX=HUD/'accepted_icons.json'\nRETIREMENTS=HUD/'runtime_retirements.json'")
    function = '''
def runtime_records(records):
    """Keep accepted artwork intact while explicitly retiring selected runtime exports."""
    if not RETIREMENTS.exists():
        return records, {}
    manifest = read(RETIREMENTS)
    assert manifest['schema'] == 'openyamm-runtime-icon-retirements-v1'
    retired = manifest['records']
    assert manifest['count'] == len(retired)
    assert retired.keys() <= records.keys(), 'Unknown retired accepted target'
    for target, retirement in retired.items():
        record = records[target]
        assert retirement['runtime_output_path'] == record['runtime_output_path'], target
        assert retirement['sha256'] == record['sha256'], f'Review changed retirement: {target}'
        assert sha(record['artifact']) == record['sha256'], f'Missing retired source art: {target}'
        assert not (ROOT / record['runtime_output_path']).exists(), f'Retired icon is still mounted: {target}'
    return {target: record for target, record in records.items() if target not in retired}, retired

'''
    updated = updated.replace("\ndef main():", "\n" + function + "\ndef main():")
    updated = updated.replace(
        "        assert manifest['count']==len(records)\n",
        "        assert manifest['count']==len(records)\n"
        "        records,retired=runtime_records(records)\n")
    updated = updated.replace(
        "            installed=[]\n",
        "            for target in retired:\n"
        "                q.state['staged_targets'][target]['status']='accepted_runtime_retired'\n"
        "            installed=[]\n")
    updated = updated.replace(
        "result='PASS',accepted=len(records),checked_cells",
        "result='PASS',accepted=manifest['count'],active=len(records),retired=len(retired),checked_cells")
    assert updated != original and "records,retired=runtime_records(records)" in updated
    (patch_dir / "deploy_icons.py").write_text(updated)
    relative_tool = str((HUD / "deploy_icons.py").relative_to(ROOT))
    relative_registry = str((HUD / "runtime_retirements.json").relative_to(ROOT))
    patch = "".join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True),
                                         fromfile="a/" + relative_tool, tofile="b/" + relative_tool))
    patch += "".join(difflib.unified_diff([], retirement_path.read_text().splitlines(True),
                                          fromfile="/dev/null", tofile="b/" + relative_registry))
    (HERE / "deployment_retirement.patch").write_text(patch)
    write_json(patch_dir / "patch_inputs.json", {
        relative_tool: hashlib.sha256(original.encode()).hexdigest(),
        str((HUD / "accepted_icons.json").relative_to(ROOT)):
            hashlib.sha256((HUD / "accepted_icons.json").read_bytes()).hexdigest(),
    })

    # Conditional candidates are deliberately absent from the removal/deployment patch.
    holds = [r for r in audit["records"] if r["status"].startswith("after_")]
    write_json(HERE / "conditional_manifest.json", dict(applied=False, files=holds))
    (HERE / "conditional-files.txt").write_text("".join(r["path"] + "\n" for r in holds))

    for record in candidates:
        path = ROOT / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], path
    # These exports predate or sit outside the accepted-icon ledger; preserve exact bytes before any future removal.
    extras = [r for r in candidates if "archive_artifact" not in r]
    with zipfile.ZipFile(HERE / "recovery_extras.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for record in extras:
            archive.write(ROOT / record["path"], record["path"])
    write_json(HERE / "recovery.json", dict(
        accepted_source_artifacts=sum("archive_artifact" in r for r in candidates),
        extra_archive="recovery_extras.zip", archive_sha256=hashlib.sha256(
            (HERE / "recovery_extras.zip").read_bytes()).hexdigest(),
        files=[dict(path=r["path"], sha256=r["sha256"],
                    recovery=r.get("archive_artifact", "recovery_extras.zip:" + r["path"])) for r in candidates]))
    review = [dict(path=r["path"], name=r["name"], bytes=r["bytes"], status=r["status"],
                   reason=r["reason"], references=r["references"][:4]) for r in candidates + holds]
    (HERE / "review-data.js").write_text("window.cleanupReview = " + json.dumps(review) + ";\n")
    print(json.dumps(dict(files=len(candidates), bytes=sum(r["bytes"] for r in candidates),
                          deploy_retirements=len(records), conditional_files=len(holds),
                          conditional_categories=Counter(r["status"] for r in holds)), indent=2))


if __name__ == "__main__":
    main()
