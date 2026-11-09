"""Preserve embedded maps and identify talon faces within the existing hand/foot regions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

stage = Path(__file__).resolve().parent
root = stage.parent
source = Path('/home/pjasicek/Downloads/Meshy_AI_mm6_demon_meshy_uploa_1005094724_texture.glb')
reader = root.parent / 'mm6_goblin/blender_rebuild_20260928/authoring/check_glb.py'
spec = importlib.util.spec_from_file_location('glb_reader', reader)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
model = module.Glb(source)
folder = stage / 'textures'
folder.mkdir(exist_ok=True)
shutil.copyfile(root / 'texturing_upload_20261005/mm6_demon_uv_master.blend', stage / 'uv_source_checkpoint.blend')
for name, image in zip(('meshy_base_color.jpg', 'meshy_metallic_roughness.jpg', 'meshy_normal.jpg'),
                       model.json['images']):
    view = model.json['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    (folder / name).write_bytes(model.binary[start:start + view['byteLength']])

data = np.load(root / 'animations_native_v7_20261005/source_geometry.npz')
uv = np.load(root / 'texturing_upload_20261005/uv_transfer.npz')['uv'].reshape(-1, 3, 2)
points, faces, weights = data['vertices'], data['faces'], data['weights']
names = list(data['group_names'])
tips = json.loads((root / 'animations_native_v7_20261005/tip_vertex_masks.json').read_text())
hand_vertices = np.zeros(len(points), bool)
hand_vertices[[i for ids in tips.values() for i in ids]] = True
hand_faces = hand_vertices[faces].sum(1) >= 2
foot_groups = [names.index('mixamorig:'+side+part) for side in ('Right', 'Left') for part in ('Foot', 'Leg')]
# Rear spurs share shin/ankle weights; their pigment belongs to the same keratin treatment.
foot_vertices = (weights[:, foot_groups].sum(1) > .9) & (points[:, 2] < .26)
foot_faces = foot_vertices[faces].sum(1) >= 2
pixels = np.asarray(Image.open(folder / 'meshy_base_color.jpg').convert('RGB')) / 255.
samples = [uv.mean(1)] + [uv[:, i] * .75 + uv.mean(1) * .25 for i in range(3)]
rgb = np.median([pixels[np.clip(((1-s[:, 1])*pixels.shape[0]).astype(int), 0, pixels.shape[0]-1),
                              np.clip((s[:, 0]*pixels.shape[1]).astype(int), 0, pixels.shape[1]-1)]
                 for s in samples], axis=0)
r, g, b = rgb.T
ivory = ((r > .30) & (r-b > .025) & (g-b > .015) & (g > .70*r)) | \
        ((rgb.min(1) > .45) & (rgb.max(1)-rgb.min(1) < .09))
selected = ivory & (hand_faces | foot_faces)
# Include one adjoining edge ring to cover dark baked patches at talon roots.
adjacent = np.isin(faces, np.unique(faces[selected])).sum(1) >= 2
selected |= adjacent & (hand_faces | foot_faces)
assert selected.any() and (selected & hand_faces).sum() > 50 and (selected & foot_faces).sum() > 20
report = {'source_glb': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'claw_faces': np.flatnonzero(selected).tolist(),
          'hand_claw_faces': int((selected & hand_faces).sum()),
          'foot_claw_faces': int((selected & foot_faces).sum()),
          'mask_rule': 'Hand-tip and lower-foot anatomy intersected with ivory pigment; one adjacent edge ring includes baked shadows.',
          'preserved_maps': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}}
(stage / 'material_regions.json').write_text(json.dumps(report, indent=2)+'\n')
print({k: v for k, v in report.items() if k != 'claw_faces'})
