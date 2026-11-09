"""Stage the isolated native attack review after prepare_native_fixture.py."""
from pathlib import Path
import hashlib
import json
import yaml

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
F = Path(json.loads((P / 'review/ingame/fixture.json').read_text())['assets_root'])
relative = Path('engine/behaviors/behaviors.yml')
raw = (ROOT / 'assets_dev' / relative).read_bytes()
doc = yaml.safe_load(raw)
doc['behaviors']['review/minotaur_melee'] = 'engine/behaviors/review_minotaur_melee.lua'
(F / relative).unlink()
(F / relative).write_text(yaml.safe_dump(doc, sort_keys=False))
assert (ROOT / 'assets_dev' / relative).read_bytes() == raw
(F / 'engine/behaviors/review_minotaur_melee.lua').write_text(
    'return Behavior.define{version=1,think_interval=.1,'
    'onStart=function(self,s) self:setAiType("normal");self:setNoFlee(true) end,'
    'onThink=function(self,s) if not self:isPerforming() then '
    'self:perform{clip="Attack",seconds=1.9,fallback="attack_melee"} end end}\n')
scene_path = F / 'worlds/mm6/maps/oute3.scene.yml'
scene = yaml.safe_load(scene_path.read_text())
actor = scene['initial_state']['actors'][44]
assert actor['monster_id'] == 68 and actor['name'] == 'MinotaurPeasant sprite preload fixture'
actor.update(position={'x': -4050, 'y': 3170, 'z': 0}, radius=60, height=160,
             move_speed=250, group=999, immobile=False)
scene_path.write_text(yaml.safe_dump(scene, sort_keys=False))
report = {'scope': 'Isolated visual fixture only', 'actor_index': 44,
          'behavior': 'Temporary scripted Attack presentation; production native wimpy AI unchanged.',
          'tour': 'review/ingame/attack_final.yml',
          'original_registry_sha256': hashlib.sha256(raw).hexdigest(),
          'note': 'Fixed preloaded map actor avoids variable post-load encounter actor indices. '
                  'Its inherited NPC display name is irrelevant to the model check.'}
(P / 'review/ingame/combat_fixture.json').write_text(json.dumps(report, indent=2) + '\n')

# The presentation API requires an explicit role mapping; otherwise it holds the native impact pose.
relative = Path('worlds/mm8/models/actors.yml')
raw = (ROOT / 'assets_dev' / relative).read_bytes()
doc = yaml.safe_load(raw)
for binding in doc['actors']:
    if binding.get('model') == 'worlds/mm8/models/mm8_m488.glb':
        binding['script_clips'] = {'Attack': 'Attack'}
(F / relative).unlink()
(F / relative).write_text(yaml.safe_dump(doc, sort_keys=False))
assert (ROOT / 'assets_dev' / relative).read_bytes() == raw
