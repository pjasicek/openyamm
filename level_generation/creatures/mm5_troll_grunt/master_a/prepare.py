"""Prepare small master-A animation batches using verified native MM8 motion topology."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
VIEWS = ['front', 'front-left three-quarter', 'left profile', 'rear-left three-quarter', 'straight back']
IDENTITY = '''Exact selected master A identity and realistic pre-rendered material language: stocky muscular
adult troll, muted teal-blue skin, broad craggy face, small ivory lower tusks, long hanging reddish auburn hair,
ragged open sleeveless deep-blue cloth vest, worn plum trousers, ochre rope belt, dark cuffed leather boots,
one plain wooden club in anatomical RIGHT hand. Same face, limb lengths, hair, outfit construction and club
size throughout. Detailed modeled anatomy, convincing cloth/leather/wood, smooth dimensional shading.
No cartoon head, pixel blocks, crunchy noise, painted outlines, neon colors, new armor or extra accessories.
Fixed soft upper-left/front key and gentle fill. Camera is orthographic at torso height. Genuine transparent
alpha outside silhouette, no glow, ground plane, shadow, text, grid or checkerboard. Complete hair/club/boots.'''


def main():
    source = json.loads((HERE/'sources.json').read_text())
    palette = np.frombuffer((REPO/source['motion_palette']['path']).read_bytes()[:768], np.uint8).reshape(256, 3)
    old_jobs = json.loads((HERE.parent/'jobs.json').read_text())
    jobs = {}
    descriptions = {
        'w': 'In-place WALK: alternating feet plant, pass and lift through the native phases. Keep pelvis tracking the fixed root. Club rests at right shoulder, free left arm naturally counter-swings. No facing drift.',
        'a': 'One overhead CLUB ATTACK: anticipation, lift, highest windup, forceful downward-forward strike, follow-through, recovery. Follow the supplied phase silhouettes. Right hand always grips club; left hand may support the same shaft only during strike. No hand swapping or extra arm.',
        'n': 'HIT reaction: progressively recoil/stagger, deepest flinch, regain balance. Match the supplied phases; keep right-hand club and original body mass. No wounds or blood.',
        'f': 'Small idle FIDGET: restrained head/shoulder/arm gestures matching the supplied phases; feet stable and planted. Same right-hand shoulder-carried club.',
        'd': 'DEATH: four consecutive stages of falling backward, then a fully settled horizontal corpse. No blood or wounds. Keep the final corpse facing UP wherever the preceding fall lands supine. For rear views show the corresponding back/side surfaces. Body length, club hand and bone lengths remain unchanged. Do not turn a prone body into a crouch or scale it to standing height.'
    }
    for key, old in old_jobs.items():
        names = old['frames']; action = old['action']; view = old['view']
        native = []
        for name in names:
            indices = np.array(Image.open(REPO/source['motion_sources'][name]['path']))
            native.append(ImageOps.mirror(Image.fromarray(np.dstack([palette[indices], (indices != 0).astype(np.uint8)*255]))))
        boxes = [im.getbbox() for im in native]
        crop = [min(b[0] for b in boxes)-6, min(b[1] for b in boxes)-6,
                max(b[2] for b in boxes)+6, max(b[3] for b in boxes)+6]
        chunks = [list(range(4)), list(range(3, 8))] if len(names) == 8 else [list(range(len(names))) ]
        for part, indices in enumerate(chunks):
            job_id = f'{action}{view}_{part}'
            count = len(indices); cols, rows = (2, 2) if count == 4 else (3, 2)
            width, height = crop[2]-crop[0], crop[3]-crop[1]
            sheet = Image.new('RGBA', (cols*width, rows*height))
            for i, n in enumerate(indices):
                sheet.paste(native[n].crop(crop), ((i % cols)*width, (i // cols)*height))
            reference = f'references/{job_id}_motion.png'; sheet.save(HERE/reference)
            shape = '1024x1536 portrait; each cell 512x768' if count == 4 else '1536x1024 landscape; each cell 512x512'
            prompt = f'''Use case: identity-preserve. Generate a detailed coherent sprite animation sheet.
Input 1: selected master A, the absolute face/design/material STYLE authority.
Input 2: accepted same-view identity, the absolute CAMERA and directional-anatomy authority.
Input 3: native MM8 MOTION ONLY; transfer its motion phases onto master A. Do not inherit its creature,
equipment, old pixel shading, perspective scale, or low resolution. It is already reflected for right-hand club.
{IDENTITY}
Direction in EVERY cell: {VIEWS[view]}. Hold exactly this viewing angle through the motion.
{descriptions[action]}
OUTPUT: {shape}, {cols} columns by {rows} rows, exactly {count} occupied cells in row-major order;
any remaining cell stays empty. One full pose per cell, no labels. Native sequence frame indices in this
sheet: {indices}. Use one shared anatomical scale across ALL cells, allowing ample room for the complete
club swing and fallen body. Standing-equivalent height about {620 if count == 4 else 430}px; lower/wider
poses keep the same body scale. Maintain 20px clear margins. Reconstruct true fine details, never enlarged pixels.
'''
            refs = ['../style_front_v2/A_faithful_render.png', f'references/identity_{view}.png', reference]
            if part:
                prompt += '\nInput 4 is the accepted preceding action batch: match its identity, materials, camera and shared transition pose (first cell here = final cell there).\n'
                refs.append(f'raw/{action}{view}_0.png')
                if action == 'a':
                    prompt += '''\nAction continuation is authoritative: cell 1 repeats the preceding batch's final
DOWNWARD STRIKE pose exactly. Cell 2 is the lower follow-through, cell 3 begins drawing the club back,
cell 4 returns it toward the right shoulder, cell 5 settles into the matching idle. Do NOT restart the
anticipation or overhead windup. Native poses guide stance/direction; the accepted strike fixes the authored
timing phase. Keep the RIGHT hand gripping; the supporting left hand can release during recovery.\n'''
            (HERE/f'prompts/{job_id}.txt').write_text(prompt)
            jobs[job_id] = dict(action=action, view=view, part=part, frames=[names[i] for i in indices],
                                columns=cols, rows=rows, native_union_crop=crop, references=refs,
                                prompt=f'prompts/{job_id}.txt', state='prepared')
    (HERE/'jobs.json').write_text(json.dumps(jobs, indent=2)+'\n')
    print(f'Prepared {len(jobs)} sheets with explicit overlap; 155 animation images plus five standing views.')


if __name__ == '__main__':
    main()
