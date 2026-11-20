#!/usr/bin/env bash
# The carapace chain: spec -> plates on work/rig.blend -> shell weights -> texture -> materials (work/carapace_skinned.blend)
set -euo pipefail
cd "$(dirname "$0")/.."
B="timeout 900 /snap/blender/current/blender --background --factory-startup -noaudio --python"
python3 scripts/carapace_spec.py
$B scripts/make_carapace.py -- work/rig.blend scripts/carapace_noble.json work/carapace_raw.blend 2>&1 | grep -E "^ARMOUR|Error" || true
$B scripts/skin_shell.py -- work/carapace_raw.blend scripts/carapace_noble.json work/carapace_skinned.blend 2>&1 | grep -E "^SHELLHIDE|Error" || true
python3 scripts/carapace_texture.py
$B scripts/carapace_materials.py -- work/carapace_skinned.blend 2>&1 | grep -E "^MATERIALS|Error" || true
