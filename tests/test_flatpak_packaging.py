"""Check bundle recovery and script edits during a long-running Flatpak export."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


REPO = Path(__file__).resolve().parents[1]


class FlatpakPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='openyamm-flatpak-wrapper-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.wrapper = self.root / 'packaging/flatpak/build_flatpak.sh'
        self.wrapper.parent.mkdir(parents=True)
        shutil.copyfile(REPO / 'packaging/flatpak/build_flatpak.sh', self.wrapper)
        self.output = self.root / 'build/flatpak'
        (self.output / 'repo/objects').mkdir(parents=True)
        self.calls = self.root / 'calls'
        self.ready = self.root / 'ready'
        self.release = self.root / 'release'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        OPENYAMM_TEST_CALLS=str(self.calls), OPENYAMM_TEST_READY=str(self.ready),
                        OPENYAMM_TEST_RELEASE=str(self.release))
        self.tool('flatpak', '''
if [ "$1" = "--version" ]; then
    printf 'Flatpak 1.16.6\n'
elif [ "$1" = "build-bundle" ]; then
    touch "$3"
else
    exit 1
fi
''')
        for name in ('cmake', 'python3', 'ostree'):
            self.tool(name, 'exit 0\n')
        self.tool('flatpak-builder', '''
touch "$OPENYAMM_TEST_READY"
while [ ! -f "$OPENYAMM_TEST_RELEASE" ]; do sleep 0.02; done
''')

    def tool(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/bash\nset -euo pipefail\n'
                        + f'printf "%s\\n" "{name} $*" >> "$OPENYAMM_TEST_CALLS"\n' + body)
        path.chmod(0o755)

    def test_bundle_only_needs_no_builder_or_source_checkout(self):
        (self.bin / 'flatpak-builder').unlink()
        result = subprocess.run(['bash', str(self.wrapper), '--bundle-only'], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.output / 'OpenYAMM.flatpak').is_file())
        calls = self.calls.read_text().splitlines()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], f'flatpak build-bundle {self.output}/repo '
                                  f'{self.output}/OpenYAMM.flatpak io.github.openyamm.OpenYAMM stable')

    def test_bundle_only_rejects_missing_exports_and_conflicting_options(self):
        shutil.rmtree(self.output / 'repo')
        result = subprocess.run(['bash', str(self.wrapper), '--bundle-only'], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No exported Flatpak repository', result.stderr)
        for option in ('--no-bundle', '--clean-only'):
            result = subprocess.run(['bash', str(self.wrapper), '--bundle-only', option], env=self.env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn('cannot be combined', result.stderr)
        self.assertFalse(self.calls.exists())

    def test_running_build_uses_parsed_workflow_after_script_changes(self):
        for name in ('CMakeLists.txt', 'LICENSE', 'COPYRIGHT', 'settings_release.ini',
                     'tools/openyamm_shaderc_stubs.cpp', 'tools/cook_sprite_atlases_main.cpp',
                     'tools/SpriteAtlasEncode.cpp', 'tools/SpriteAtlasEncode.h',
                     'tools/TextureBlockEncode.cpp', 'tools/TextureBlockEncode.h',
                     'tools/cook_model_textures_main.cpp',
                     'tools/cook_sprite_atlases.py', 'tools/package_runtime_assets.py'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        for name in ('cmake', 'engine', 'game', 'packaging/icons', 'packaging/licenses',
                     'assets_dev/engine', 'assets_dev/worlds/mm6', 'assets_dev/worlds/mm7',
                     'assets_dev/worlds/mm8', 'assets_dev/worlds/mmmerge'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(['bash', str(self.wrapper), '--jobs=1', '--no-install'],
                                   env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not self.ready.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(self.ready.exists(), 'Wrapper did not reach the builder')
            self.wrapper.write_text(self.wrapper.read_text() + '\nprintf "unfinished replacement\n')
            self.release.touch()
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIn('Bundle:', stdout)
            self.assertTrue((self.output / 'OpenYAMM.flatpak').is_file())
        finally:
            self.release.touch()
            if process.poll() is None:
                process.kill()
                process.communicate()


if __name__ == '__main__':
    unittest.main()
