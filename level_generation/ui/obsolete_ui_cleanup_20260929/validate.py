"""Validate a staged or applied cleanup manifest, recovery sources and retirement guards."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = read(HERE / "removal_manifest.json")
    audit = read(HERE / "inventory.json")
    records = manifest["files"]
    applied = manifest.get("applied", False)
    paths = {r["path"] for r in records}
    assert len(paths) == len(records)
    assert paths == set((HERE / "remove-files.txt").read_text().splitlines())
    assert not paths.intersection(r["path"] for r in read(HERE / "conditional_manifest.json")["files"])
    for record in records:
        assert record["status"] == "stage_removal"
        assert not any(r["kind"] not in {"unmounted_layout"} for r in record["references"]), record["path"]
        if applied:
            assert not (ROOT / record["path"]).exists(), record["path"]
        else:
            assert sha(ROOT / record["path"]) == record["sha256"], record["path"]
        if "archive_artifact" in record:
            assert sha(ROOT / record["archive_artifact"]) == record["sha256"], record["path"]
    recovery = read(HERE / "recovery.json")
    assert sha(HERE / recovery["extra_archive"]) == recovery["archive_sha256"]
    with zipfile.ZipFile(HERE / recovery["extra_archive"]) as archive:
        for record in records:
            if "archive_artifact" not in record:
                assert hashlib.sha256(archive.read(record["path"])).hexdigest() == record["sha256"]
    protected = ["assets_dev/engine/icons_x2/ia02-001.png",
                 "assets_dev/engine/icons_x2/obsidian_hud_buff_expiring.png",
                 "assets_dev/worlds/mm7/icons_x2/7out06.bmp",
                 "assets_dev/worlds/mm8/icons_x2/elemf.bmp",
                 "assets_dev/engine/ui/gameplay/touch_controls.yml",
                 "assets_dev/engine/ui/gameplay/spellbook.yml"]
    for path in protected:
        assert (ROOT / path).is_file() and path not in paths, path
    inputs = read(HERE / "inputs.json")
    changed = [p for p, digest in inputs.items() if not (ROOT / p).is_file() or sha(ROOT / p) != digest]
    if not applied:
        assert not changed, f"Re-run the audit for changed source/data: {changed}"
    staged = HERE / "staged"
    source = ((ROOT / "level_generation/ui/hud_inventory/deploy_icons.py") if applied
              else staged / "deploy_icons.py").read_text()
    compile(source, "staged/deploy_icons.py", "exec")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "runtime_records")

    # Exercise the deletion guard in a disposable fixture, without importing Queue or touching its ledger.
    checks = []
    with tempfile.TemporaryDirectory(prefix="obsolete-ui-retirement-check-") as work:
        root = Path(work)
        namespace = {"ROOT": root, "RETIREMENTS": root / "retirements.json", "read": read, "sha": lambda p: sha(Path(p))}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "retirement-guard", "exec"), namespace)
        select = namespace["runtime_records"]
        artifact = root / "accepted-source.png"
        artifact.write_bytes(b"accepted artwork fixture")
        digest = sha(artifact)
        entries = {"retired": dict(runtime_output_path="icons/old.png", sha256=digest, artifact=str(artifact)),
                   "active": dict(runtime_output_path="icons/new.png", sha256=digest, artifact=str(artifact))}
        assert select(entries) == (entries, {})
        checks.append("No registry preserves the existing deployment set")
        retirement = dict(schema="openyamm-runtime-icon-retirements-v1", count=1, records={
            "retired": dict(runtime_output_path="icons/old.png", sha256=digest)})
        registry = namespace["RETIREMENTS"]
        registry.write_text(json.dumps(retirement))
        active, retired = select(entries)
        assert set(active) == {"active"} and set(retired) == {"retired"}
        checks.append("Explicit retirement excludes only its accepted target")
        destination = root / "icons/old.png"
        destination.parent.mkdir()
        destination.write_bytes(b"still installed")
        try:
            select(entries)
        except AssertionError as error:
            assert "still mounted" in str(error)
        else:
            raise AssertionError("Mounted retired file was accepted")
        destination.unlink()
        checks.append("Still-mounted retired artwork is rejected")
        retirement["records"]["retired"]["sha256"] = "unreviewed revision"
        registry.write_text(json.dumps(retirement))
        try:
            select(entries)
        except AssertionError as error:
            assert "changed retirement" in str(error)
        else:
            raise AssertionError("Changed accepted revision was accepted")
        checks.append("Changed accepted artwork requires a new retirement review")
    if not applied:
        subprocess.run(["git", "apply", "--check", str(HERE / "deployment_retirement.patch")], cwd=ROOT, check=True)
    report = dict(result="PASS", removal_files=len(records), removed_bytes=sum(r["bytes"] for r in records),
                  census_files=audit["census_files"], unchanged_source_inputs=len(inputs) - len(changed),
                  deployment_patch="Applied" if applied else "git apply --check passed; not applied",
                  retirement_guard_checks=checks,
                  recoverable_candidates=len(records),
                  mounted_candidates="All removed" if applied else "All still present and unchanged",
                  live_assets_modified=applied)
    (HERE / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
