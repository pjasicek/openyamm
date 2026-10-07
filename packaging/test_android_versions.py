#!/usr/bin/env python3
"""Run the actual package-metadata shell block without building an APK."""

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/nightly.yml").read_text()
metadata_step = workflow.split("      - name: Validate release tag and resolve names\n", 1)[1]
metadata_script = textwrap.dedent(metadata_step.split("        run: |\n", 1)[1].split("\n  android:", 1)[0])


class AndroidVersionTests(unittest.TestCase):
    def resolve(self, ref="refs/heads/main", event="schedule", run=1, attempt=1, succeeds=True):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environment = dict(os.environ, GITHUB_REF=ref, GITHUB_REF_NAME=ref.rsplit("/", 1)[-1],
                               GITHUB_EVENT_NAME=event, GITHUB_SHA="1234567", GITHUB_OUTPUT=str(output),
                               GITHUB_RUN_NUMBER=str(run), GITHUB_RUN_ATTEMPT=str(attempt))
            result = subprocess.run(["bash", "-euo", "pipefail", "-c", metadata_script], env=environment,
                                    capture_output=True, text=True, timeout=10)
            if not succeeds:
                self.assertNotEqual(result.returncode, 0)
                return
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return dict(line.split("=", 1) for line in output.read_text().splitlines())

    def test_release_to_nightly_to_release_and_rerun(self):
        nightly = self.resolve(run=40)
        rerun = self.resolve(run=40, attempt=2)
        release = self.resolve(ref="refs/tags/1.1", event="push", run=41)
        following_nightly = self.resolve(run=42)
        codes = [10000] + [int(values["android_version_code"])
                           for values in (nightly, rerun, release, following_nightly)]
        self.assertTrue(all(older < newer for older, newer in zip(codes, codes[1:])))
        self.assertEqual(nightly["android_version_name"], "nightly-40.1")
        self.assertEqual(release["android_version_name"], "1.1")
        self.assertEqual(release["android_asset_name"], "OpenYAMM-1.1-android-arm64.apk")

    def test_all_build_types_have_explicit_versions(self):
        for event in ("push", "schedule", "workflow_dispatch"):
            with self.subTest(event=event):
                values = self.resolve(event=event)
                self.assertGreater(int(values["android_version_code"]), 10000)
                self.assertEqual(values["android_version_name"], "nightly-1.1")
                self.assertEqual(values["android_asset_name"], "OpenYAMM-nightly-android-arm64.apk")
                self.assertEqual(values["is_tag"], "false")

    def test_reruns_cannot_overlap_the_next_run(self):
        last_attempt = self.resolve(run=40, attempt=99)
        next_run = self.resolve(run=41)
        self.assertLess(int(last_attempt["android_version_code"]), int(next_run["android_version_code"]))
        for attempt in (0, 100):
            self.resolve(attempt=attempt, succeeds=False)

    def test_android_code_limit(self):
        self.assertLessEqual(int(self.resolve(run=20999899, attempt=99)["android_version_code"]), 2100000000)
        self.resolve(run=20999900, succeeds=False)
        self.resolve(run=0, succeeds=False)

    def test_tag_validation_is_preserved(self):
        for tag in ("1.1", "0.14", "2.0"):
            self.assertEqual(self.resolve(ref="refs/tags/" + tag, event="push")["android_version_name"], tag)
        for tag in ("0.0", "v1.1", "1.1.0", "01.1", "1.100"):
            self.resolve(ref="refs/tags/" + tag, event="push", succeeds=False)


if __name__ == "__main__":
    unittest.main()
