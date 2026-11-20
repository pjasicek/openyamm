"""Mark the exact reviewed browser revision as accepted and installed."""

import json

from publish import OUT, HUD, ROOT, REVIEW, REVISION, immutable, read, sha


def main():
    accepted = read(OUT / "accepted.json")
    validation = read(OUT / "validation.json")
    assert validation["result"] == "PASS" and validation["review_revision"] == REVISION
    assert validation["accepted_revision_sha256"] == sha(OUT / "accepted.json")
    assert validation["canonical_index_sha256"] == sha(HUD / "accepted_icons.json")
    viewer = HUD / "spellbook_fixup_review"
    assert sha(viewer / "manifest.json") == sha(REVIEW / "manifest.json")
    for record in accepted["records"].values():
        assert sha(ROOT / record["runtime_output_path"]) == record["sha256"]
        relative = record["reviewed_artifact"].removeprefix(str(REVIEW) + "/")
        assert sha(viewer / relative) == record["sha256"]
    result = {
        "schema": "openyamm-spellbook-browser-acceptance-v1", "revision": REVISION,
        "status": "accepted_installed", "acceptedAt": accepted["published_at"],
        "targets": sorted({record["review_target"] for record in accepted["records"].values()}),
        "files": len(accepted["records"]), "changedFiles": accepted["summary"]["changed_runtime_images"],
        "receipt": "../spellbook_acceptance_20260927/accepted.json", "receiptSha256": sha(OUT / "accepted.json"),
        "validation": "../spellbook_acceptance_20260927/validation.json",
    }
    assert len(result["targets"]) == 135
    immutable(viewer / "acceptance.json", result)
    (viewer / "acceptance.js").write_text("window.SPELLBOOK_ACCEPTANCE = " + json.dumps(result) + ";\n")
    print(json.dumps({"acceptedReviewTargets": 135, "installedFiles": result["files"], "revision": REVISION}, indent=2))


if __name__ == "__main__":
    main()
