"""Viewer manifest for review/viewer/mm6_natf_cand.glb (export_candidates.py): clip durations from the GLB, display order."""
import hashlib, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
V = Path(__file__).resolve().parents[1] / 'review/viewer'; g = V / 'mm6_natf_cand.glb'
doc, binary = read_glb(g)
SRC = {'Standing': 'accepted clip', 'Attack (current)': 'accepted clip (Dagger R2, re-posed in Codex rounds 3-5)',
       'Cast (current)': 'accepted clip (Cast R Attack Hand 1, re-posed)'}
order = ['Standing', 'Attack (current)', 'Mixamo Sword And Shield Attack 2', 'Mixamo Stable Sword Inward Slash',
         'Mixamo Sword And Shield Slash 4', 'HS Dagger R2 (current base)', 'HS Dagger R1', 'HS Dagger R3',
         'Mixamo Stabbing', 'Mixamo Stabbing 2', 'Cast (current)', 'HS Cast R Attack Hand 1 (current base)',
         'HS Cast R Attack Hand 2', 'HS Cast R Attack 1', 'HS Cast R Buff 1']
ends = {a['name']: max(max(struct.unpack(f'<{doc["accessors"][s["input"]]["count"]}f', accessor_bytes(doc, binary, s['input'])))
                       for s in a['samplers']) for a in doc['animations']}
clips = {n: {'label': n, 'duration': round(ends[n], 6), 'mode': 'loop' if n == 'Standing' else 'once',
             'provenance': SRC.get(n, 'raw library retarget: stance planted, shield arm held in the Standing guard; not fitted'),
             'anchors': []} for n in order}
h = hashlib.sha256(g.read_bytes()).hexdigest()
m = {'revision': 'anim-candidates-1', 'model': 'MM6 female Cannibal: attack/cast library candidates',
     'default_clip': 'Attack (current)', 'default_model': 'cand', 'feedback': '../feedback/user_feedback.json',
     'clips': clips, 'models': [{'id': 'cand', 'label': 'natf master (untiered textures)', 'url': f'{g.name}?v={h[:12]}',
                                 'revision': 'anim-candidates-1', 'sha256': h}]}
(V / 'manifest.json').write_text(json.dumps(m, indent=1)); print({k: v['duration'] for k, v in clips.items()})
