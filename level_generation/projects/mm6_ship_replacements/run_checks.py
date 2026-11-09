#!/usr/bin/env python3
"""Exercise each new berth with private settings and saves; retain concise native evidence."""
import configparser
import json
from pathlib import Path
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
results = []
for scenario in sorted((PROJECT / "source/scenarios").glob("*.yml")):
    with tempfile.TemporaryDirectory(prefix="openyamm-mm6-ships-check-") as directory:
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(ROOT / "settings.ini")
        settings["assets"]["root"] = str(PROJECT / "playtest/assets_dev")
        with (Path(directory) / "settings.ini").open("w") as stream:
            settings.write(stream)
        result = subprocess.run([str(ROOT / "build/game/openyamm"), "--world", "mm6", "--headless-run-scenario",
                                 str(scenario), "--scenario-no-color"], cwd=directory,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = PROJECT / "review/checks" / (scenario.stem + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    lines = result.stdout.splitlines()
    first_step = next((i for i, line in enumerate(lines) if line.startswith("RUN step ")), 0)
    log.write_text(f"Scenario: {scenario.name}\nExit code: {result.returncode}\n"
                   + "\n".join(lines[first_step:]) + "\n")
    results.append({"scenario": scenario.name, "exit_code": result.returncode,
                    "log": str(log.relative_to(PROJECT))})
    print(scenario.stem, "PASS" if result.returncode == 0 else "FAIL", flush=True)
(PROJECT / "review/checks.json").write_text(json.dumps(results, indent=2) + "\n")
raise SystemExit(1 if any(result["exit_code"] for result in results) else 0)
