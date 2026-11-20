"""Present matched material comparisons and checked animation poses without new dependencies."""
import html
import json
from pathlib import Path
import shutil

stage = Path(__file__).resolve().parent
report = json.loads((stage / 'validation.json').read_text())
assert report['passed']
shutil.copyfile('/tmp/codex-clipboard-bdj2lN.png', stage / 'native_face_reference.png')


def figure(file, caption, cls=''):
    return f'<figure class="{cls}"><img src="{file}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>'


pairs = ''
for label, name in [('Face, front', 'face_front'), ('Face, left oblique', 'face_left'),
                    ('Face, right oblique', 'face_right'), ('Right hand', 'right_hand'),
                    ('Left hand', 'left_hand'), ('Feet, front', 'feet_front'), ('Feet, profile', 'feet_profile')]:
    pairs += f'<h2>{label}</h2><div class="pair">' + \
             figure(f'review_frames/before_{name}.png', 'Meshy textures on the same animated pose') + \
             figure(f'review_frames/after_{name}.png', 'Corrected materials — actual exported GLB') + '</div>'
poses = ''
for clip, frame in [('Standing', 0), ('Walk_Native', 15), ('Attack', 12), ('Attack', 24), ('Hit', 18),
                    ('Fidget', 18), ('Walking', 25), ('Running', 16), ('Death', 12), ('Death', 30), ('Ash_Remains', 0)]:
    poses += f'<h3>{html.escape(clip.replace("_", " "))} · frame {frame}</h3><div class="pair">' + \
             figure(f'review_frames/{clip}_{frame}_front.png', 'Front') + \
             figure(f'review_frames/{clip}_{frame}_profile.png', 'Profile') + '</div>'
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MM6 Demon — White Claws and Red Eyes</title>
<style>
body{margin:0;background:#1b1e23;color:#e4e2dc;font:16px/1.5 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:24px}
h1{font-size:28px;margin:0 0 8px}h2{font-size:21px;margin-top:36px}h3{font-size:18px}p{color:#bfc7cd}a{color:#efa874}
nav{display:flex;gap:24px;flex-wrap:wrap;margin:18px 0 24px}.pair,.triple{display:grid;gap:16px}.pair{grid-template-columns:repeat(2,minmax(0,1fr))}
.triple{grid-template-columns:repeat(3,minmax(0,1fr))}figure{margin:0;background:#292e35;border-radius:8px;overflow:hidden}
img{display:block;width:100%;height:auto}figcaption{padding:10px 14px;color:#bbc5ce;font-size:14px}.native img{image-rendering:pixelated}
details{margin:36px 0}summary{cursor:pointer;font-size:22px}.full{max-width:620px;margin:auto}.full img{width:100%}
@media(max-width:700px){main{padding:15px}.pair,.triple{grid-template-columns:1fr}h1{font-size:23px}}
</style><main><h1>MM6 Demon — White Claws and Red Eyes</h1>
<p>White hand talons, toe claws and rear foot spurs; consistent salmon-red irises and black pupils.
The Meshy skin and green harness textures are retained. All nine animation curves and the original rig are preserved.</p>
<nav><a href="mm6_demon_textured.blend" download>Editable Blender project</a><a href="mm6_demon_textured.glb" download>Animated GLB</a>
<a href="README.md">Notes</a><a href="validation.json">Checks</a></nav>
'''
page += '<div class="triple">' + figure('native_face_reference.png', 'Native face reference', 'native') + \
        figure('review_frames/before_face_front.png', 'Meshy materials, matching camera') + \
        figure('review_frames/after_face_front.png', 'Corrected materials, matching camera') + '</div>'
page += '<h2>Full character</h2><div class="full">' + \
        figure('review_frames/Standing_0_front.png', 'Standing — actual animated GLB') + '</div>'
page += pairs + '<details><summary>Check animation poses</summary>' + poses + '</details>'
page += '<p>The comparisons use identical poses, cameras and lighting. Animation panels show representative still poses from the exported GLB.</p></main></html>'
(stage / 'index.html').write_text(page)
(stage / 'README.md').write_text('''# MM6 demon — local material corrections

Open [index.html](index.html) for the native face reference, matched Meshy/corrected
material comparisons and representative poses from all nine exported clips.

## Files

- `mm6_demon_textured.blend`: editable animated master with packed textures. Active scene:
  `MM6_Demon_Textured_Animations`, Standing at frame zero, 48 fps.
- `mm6_demon_textured.glb`: animated portable model, nine clips, 85 joints, 16474 body triangles.
- `textures/`: the unchanged Meshy maps and the locally baked white-claw colour map.
- `material_regions.json`: reviewed polygon mask and input/texture hashes.
- `validation.json`: preservation, export and representative-pose checks.

The source is `Meshy_AI_mm6_demon_meshy_uploa_1005094724_texture.glb`. Its geometry
and UV coordinates match our static UV upload. The animated source remains
`../texturing_upload_20261005/mm6_demon_uv_master.blend`.

The body and harness use the original generated material. The two iris surfaces use
salmon-red sRGB (0.86, 0.38, 0.36); the pupil caps use near-black (0.015, 0.012, 0.012).
Eyes have no generated bump or metallic map. Hand and foot talons, including the rear
foot spurs, use a neutral white colour map, zero metallic and the existing roughness
and tangent-normal detail. The colour bake brightens and desaturates the ivory pigment
while retaining dark skin at the roots. The mask uses hand-tip/lower-foot anatomy and ivory
pigment, with one adjacent polygon ring for dark baked patches. It does not recolour
the ivory shoulder spikes or teeth.

The Blender master keeps four body material slots: body, iris, pupil and white talons.
No topology, UV, normal, weight, bind or animation changes were made. The extra talon
material adds one material primitive; triangle count is unchanged. The original UV
master, Meshy download and previous revisions remain unchanged.

The actual GLB was reimported, its material colours and maps checked, and representative
deformed vertices compared across all nine clips, including fractional Running timing.
Comparison renders use the actual GLB with matching pose, camera and lighting. These
checks do not constitute final artistic acceptance or engine installation.

## Reproduction

Run `python3 prepare_return.py` from this directory to extract maps and the mask.
Through Blender MCP, import `author_materials.py` and call `apply()` in a session without
the new textured scene. This appends the UV master from the preserved source checkpoint.
Then, from the repository root:

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/export_and_review.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/build_review.py
```

To inspect an animation in Blender, mute all rig/object/shape-key NLA tracks, assign
the matching strip Action and its Action Slot, then set frames according to the clip.
Alternatively, use the existing `SELECT_ANIMATION.py` text in the project to enable
one clip's NLA tracks. Nine clips: Standing, Walk_Native, Attack, Hit, Fidget, Death,
Ash_Remains, Walking and Running.
''')
print('Built material comparison review.')
