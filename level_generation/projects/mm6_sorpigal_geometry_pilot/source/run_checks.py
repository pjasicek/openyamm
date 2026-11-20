"""Run the pilot's headless scenarios against the stage (private settings pointing at playtest/assets_dev)."""
import configparser
import subprocess
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
failed = 0
for scenario in sorted((PROJECT / 'source/scenarios').glob('*.yml')):
    with tempfile.TemporaryDirectory(prefix='openyamm-geometry-pilot-') as directory:
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(ROOT / 'settings.ini')
        if not settings.has_section('assets'):
            settings.add_section('assets')
        settings['assets']['root'] = str(PROJECT / 'playtest/assets_dev')
        with (Path(directory) / 'settings.ini').open('w') as stream:
            settings.write(stream)
        result = subprocess.run([str(ROOT / 'build/game/openyamm'), '--world', 'mm6', '--headless-run-scenario',
                                 str(scenario), '--scenario-no-color'], cwd=directory,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = PROJECT / 'review/checks' / (scenario.stem + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout)
    failed += result.returncode != 0
    print(scenario.stem, 'PASS' if result.returncode == 0 else 'FAIL', flush=True)
raise SystemExit(1 if failed else 0)
