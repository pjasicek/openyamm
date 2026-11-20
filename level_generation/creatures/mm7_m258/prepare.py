"""Prepare Griffin's complete native art and compact generation sheets once."""
import importlib.util
import json
import math
from pathlib import Path
import re
from PIL import Image

P = Path(__file__).resolve().parent
assert not (P / 'sources.json').exists(), 'Resume preserved sources/batches instead of preparing again.'
spec = importlib.util.spec_from_file_location('native_prepare', P.parent / 'mm7_ambient/prepare.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
description = (
    'The exact native flying griffin: compact brown lion hindquarters, two brown rear legs with red-brown '
    'claw tips, long thin brown tail ending in a small green feather tuft. Feathered muted dark teal-green '
    'eagle head, neck, broad breast and shoulders; two narrow pointed green head tufts, small dark alert '
    'eyes, hooked golden-yellow beak with an orange underside. Two large eagle wings with green upper '
    'coverts, dark shaded feather bases and long muted olive-gray flight feathers with pale subdued tips. '
    'Two golden ochre scaled eagle forelegs with long dark hooked talons. Preserve four legs plus two '
    'wings: eagle forefeet and feline hindfeet, their exact native pose and foreshortening. Keep the '
    'short neck, small head, bulky bird breast, lean brown feline rear body, native wing span and feather '
    'layering. Native upper-left baked lighting, dark restrained tonal weight, no bright rim light. '
    'Only colored plumage/tail tuft and flight feathers change in native palettes; preserve native brown '
    'fur, golden beak, scales, eyes and claws. No saddle, armor, rider, harness, jewelry, new limbs, '
    'effects, background shadow or redesign.'
)
config = dict(label='Griffin A', creature='griffin', base_palette=259,
    connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
    protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
    identity_frames=[f'm258sa{i}' for i in range(5)],
    identity_view='front, front-right oblique, right profile, rear-right oblique, back', description=description)
m.CONFIGS[P.name] = config
m.run(P.name)
sources = json.loads((P / 'sources.json').read_text())['sources']
natives = {n: Image.open(P / f'native/{n}.png') for n in sources}
batches = {}
plan = {}


def emit(key, names, whole_sequence, view, reference_only=()):
    boxes = [natives[n].getbbox() for n in whole_sequence]
    # Common full-sequence window, with room for every native tip and its soft restored edge.
    window = [min(b[0] for b in boxes)-12, min(b[1] for b in boxes)-12,
              max(b[2] for b in boxes)+12, max(b[3] for b in boxes)+12]
    width, height = window[2]-window[0], window[3]-window[1]
    if key == 'standing':
        cols, rows, budget = 3, 2, [1536,1024]
    else:
        cols, rows, budget = 2, 2, [1254,1254]
    projected = min(budget[0]/(cols*width),budget[1]/(rows*height))
    assert projected >= 2.2, (key, window, projected)
    cell = [width*4,height*4]
    sheet = Image.new('RGB',(cell[0]*cols,cell[1]*rows),(255,0,255))
    for i,name in enumerate(names):
        im=natives[name].crop(window).resize(cell,Image.Resampling.NEAREST)
        sheet.paste(im,(i%cols*cell[0],i//cols*cell[1]),im)
    sheet.save(P / f'references/{key}.png')
    batches[key]=dict(frames=names,columns=cols,rows=rows,cell_size=cell,native_window=window,
        reference_scale=4,view=view,reference_only_frames=list(reference_only))
    plan[key]=dict(status='pending_generation',common_sequence=whole_sequence,native_window=window,
        requested_output_budget=budget,projected_sampling=projected,reference_only_frames=list(reference_only))
    identity = '' if key=='standing' else '\nInput2 is the accepted enhanced identity/material reference ONLY; Input1 controls the exact new poses and view. Do not copy Input2 layout.'
    prompt=f'''Use case: style-transfer. Restore these original Might and Magic VII griffin sprites into crisp detailed fantasy game artwork.
Input1 is the native POSE, VIEW and LAYOUT authority: {cols} columns by {rows} rows, {len(names)} occupied cells in row-major order: {', '.join(names)}. View: {view}.{identity}
Identity: {description}
Preserve each exact native wing angle, feather fan, head direction, beak opening, eagle foreleg and feline hindleg pose, claws and tail curve. Preserve the complete silhouette and native anatomical proportions at one common scale. No independent pose zoom, equal-bounds fitting or recentering. Native effects only, no invented action elements. Restore fine feather barbs, scales and fur with sharp resolved material edges, no pixel stair steps, blur or oversharpening halos.
Output approximately {budget[0]} by {budget[1]} pixels or larger, maintaining the exact grid. Keep at least24 output pixels of fully transparent clearance around every complete wing, talon and tail tip. Unused cells and all gutters are fully transparent. No cropped tips or merged poses.
Deliver genuine RGBA PNG transparency. The magenta in the native reference is for readability only; do not paint magenta, white, black, checkerboards, gradients, shadows, grid lines, labels or any backdrop into visible pixels. Preserve the original dark native palette and upper-left lighting. No added accessories or redesign.
'''
    (P / f'prompts/{key}.txt').write_text(prompt)

emit('standing',[f'm258sa{i}' for i in range(5)],[f'm258sa{i}' for i in range(5)],
    'front, front-right oblique, right profile in row1; rear-right oblique, back, empty in row2')
for action in ['w','a','n']:
    for view in range(5):
        names=sorted(n for n in sources if re.fullmatch(f'm258{action}[a-z]{view}',n))
        for part,selected in enumerate([names[:4],names[3:]]):
            emit(f'{action}_{view}_detail_{part}',selected,names,
                 ['FRONT','FRONT-RIGHT OBLIQUE','RIGHT PROFILE','REAR-RIGHT OBLIQUE','BACK'][view]+' in every cell',
                 [names[3]] if part else [])
for view in range(5):
    names=sorted(n for n in sources if re.fullmatch(f'm258[dx][a-z]{view}',n))
    emit(f'death_{view}_detail_0',names[:4],names,f'native death orientations, stored view{view}')
    emit(f'death_{view}_detail_1',names[-4:],names,f'native late fall and prone corpse, stored view{view}',names[-4:-1])
assert sorted(n for b in batches.values() for n in b['frames'] if n not in b['reference_only_frames'])==sorted(sources)
(P / 'batches.json').write_text(json.dumps(batches,indent=2)+'\n')
(P / 'generation_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(len(sources),'native frames,',len(batches),'compact sheets; min projected',min(x['projected_sampling'] for x in plan.values()))
