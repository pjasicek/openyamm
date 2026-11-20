#!/usr/bin/env python3
"""Run the release workflow's version step (.github/workflows/packages.yml) without building anything."""

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


repo_root = Path(__file__).resolve().parents[1]
workflow = (repo_root / ".github/workflows/packages.yml").read_text()
metadata_step = workflow.split("      - name: Resolve version and site\n", 1)[1]
metadata_script = textwrap.dedent(metadata_step.split("        run: |\n", 1)[1].split("\n  content:", 1)[0])


class ReleaseVersionTests(unittest.TestCase):
    def resolve(self, ref="refs/heads/main", event="push", version="", run=1, attempt=1, commit_time=1792100575,
                succeeds=True):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environment = dict(os.environ, GITHUB_REF=ref, GITHUB_REF_NAME=ref.rsplit("/", 1)[-1],
                               GITHUB_REF_TYPE="tag" if ref.startswith("refs/tags/") else "branch",
                               GITHUB_EVENT_NAME=event, INPUT_VERSION=version, GITHUB_OUTPUT=str(output),
                               GITHUB_RUN_NUMBER=str(run), GITHUB_RUN_ATTEMPT=str(attempt),
                               OPENYAMM_COMMIT_TIME=str(commit_time))
            result = subprocess.run(["bash", "-euo", "pipefail", "-c", metadata_script], env=environment,
                                    cwd=repo_root, capture_output=True, text=True, timeout=10)
            if not succeeds:
                self.assertNotEqual(result.returncode, 0)
                return
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return dict(line.split("=", 1) for line in output.read_text().splitlines())

    def test_newer_commits_update_older_packages(self):
        nightly = self.resolve(run=40, commit_time=1792100575)
        release = self.resolve(ref="refs/tags/v1.1", run=41, commit_time=1792100600)
        following_nightly = self.resolve(run=42, commit_time=1792187000)
        codes = [1000000] + [int(values["android_version_code"]) for values in (nightly, release, following_nightly)]
        self.assertTrue(all(older < newer for older, newer in zip(codes, codes[1:])))
        self.assertEqual(nightly["android_version_name"], "nightly-40.1")
        self.assertEqual(release["android_version_name"], "1.1")

    def test_same_commit_shares_a_code(self):
        nightly = self.resolve(run=40)
        rerun = self.resolve(run=40, attempt=2)
        release = self.resolve(ref="refs/tags/v1.1", run=41)
        self.assertEqual(nightly["android_version_code"], rerun["android_version_code"])
        self.assertEqual(nightly["android_version_code"], release["android_version_code"])

    def test_sites(self):
        self.assertEqual(self.resolve()["site"], "")
        self.assertEqual(self.resolve()["version"], "nightly")
        self.assertEqual(self.resolve(event="workflow_dispatch")["site"], "")
        release = self.resolve(ref="refs/tags/v1.7")
        self.assertEqual((release["version"], release["site"]), ("1.7", "stable"))
        staging = self.resolve(event="workflow_dispatch", version="1.8")
        self.assertEqual((staging["version"], staging["site"], staging["android_version_name"]),
                         ("1.8", "staging", "1.8"))

    def test_android_code_limit(self):
        self.assertEqual(int(self.resolve(commit_time=1767225600 + 2100000000)["android_version_code"]), 2100000000)
        self.resolve(commit_time=1767225600 + 2100000001, succeeds=False)
        self.resolve(commit_time=1767225600 + 1000000, succeeds=False)
        self.resolve(commit_time="yesterday", succeeds=False)

    def test_versions_are_validated(self):
        for tag in ("v1.1", "v0.14", "v2.0"):
            self.assertEqual(self.resolve(ref="refs/tags/" + tag)["android_version_name"], tag[1:])
        for tag in ("v0.0", "1.1", "v1.1.0", "v01.1", "v1.100"):
            self.resolve(ref="refs/tags/" + tag, succeeds=False)
        self.resolve(event="workflow_dispatch", version="1.x", succeeds=False)


if __name__ == "__main__":
    unittest.main()
