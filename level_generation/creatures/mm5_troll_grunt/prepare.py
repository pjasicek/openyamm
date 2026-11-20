"""Prepare a new MM5 creature adaptation; native MM8 art is only a motion reference."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
VIEWS = ['front', 'front-left three-quarter', 'left profile', 'rear-left three-quarter', 'straight back']


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def source_record(path):
    return {'path': str(path.relative_to(REPO)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    donor = json.loads((HERE.parent / 'mm8_m476/sources.json').read_text())
    batches = json.loads((HERE.parent / 'mm8_m476/batches.json').read_text())
    palette_path = REPO / donor['palette_sources']['477']['path']
    colors = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
    source_root = REPO / 'reference/mm4_5_world_of_xeen/unpacked'
    native_sources = []
    for ext in ['mon', 'att']:
        folder = source_root / f'sprites/dark/056.{ext}'
        meta = json.loads((folder / 'frames.json').read_text())
        for frame in meta['frames']:
            native_sources.append(dict(source_record(folder / frame['file']), **frame, resource=f'056.{ext}'))
        native_sources.append(source_record(folder / 'frames.json'))
        native_sources.append(source_record(source_root / f'raw/dark/056.{ext}'))
    native_sources.append(source_record(source_root / 'raw/dark/dark.mon'))
    motion_sources = {}
    images = {}
    for name, record in donor['sources'].items():
        path = REPO / record['path']
        indexes = np.array(Image.open(path))
        rgba = Image.fromarray(np.dstack([colors[indexes], (indexes != 0).astype(np.uint8) * 255]))
        # Native MM8 troll holds its weapon in its left hand. Reflect the complete motion reference
        # for the right-handed MM5 character; stored views now turn toward image left.
        images[name] = ImageOps.mirror(rgba)
        motion_sources[name] = dict(source_record(path), palette=477, original_canvas=record['size'],
                                    original_bounds=record['native_bbox'], reference_reflected=True)
    jobs = {}
    for key, batch in batches.items():
        if key == 'identity':
            continue
        names = batch['frames']
        view = int(key[-1])
        action = key.split('_')[1]
        boxes = [images[name].getbbox() for name in names]
        crop = [min(b[0] for b in boxes)-8, min(b[1] for b in boxes)-8,
                max(b[2] for b in boxes)+8, max(b[3] for b in boxes)+8]
        count = len(names)
        cols, rows = (3, 3) if count == 8 else (3, 2)
        cw, ch = crop[2]-crop[0], crop[3]-crop[1]
        sheet = Image.new('RGBA', (cols*cw, rows*ch))
        for i, name in enumerate(names):
            im = images[name].crop(crop)
            # A single union crop retains the donor's contact points and motion without individual fitting.
            sheet.paste(im, (i % cols*cw, i // cols*ch))
        ref = HERE / f'references/{key}.png'
        sheet.save(ref)
        descriptions = {
            'w': 'Eight consecutive frames of a complete in-place walking cycle, alternating planted and lifted feet. Carry the wooden club in the RIGHT hand, near right shoulder. Preserve the footfall phases in the motion reference.',
            'a': 'Eight consecutive frames of one club attack: anticipation, windup, raised club, forward/downward strike, follow-through, then recovery. Match motion-reference phases and foreshortening, but replace its weapon with the simple wooden MM5 club held in RIGHT hand. Keep the supporting feet planted where the reference shows them planted.',
            'n': 'Five consecutive recoil/hit-reaction frames: flinch backward, recoil, deepest stagger, regain balance, recovery. No wounds or blood. Keep the wooden club in RIGHT hand.',
            'f': 'Five consecutive small idle/fidget frames. Match the reference head/arm/torso gestures, with restrained motion and stable feet. Keep the wooden club in RIGHT hand.',
            'd': 'Five falling/corpse frames: four successive collapse poses, then the fully prone resting corpse. Last cell is a low horizontal body, not another crouching stance. Match each reference silhouette, orientation and foreshortening. No wounds or blood. Keep body mass and limb lengths unchanged when prone; do not enlarge a fallen body to fill its cell. Keep the wooden club present.'
        }
        shape = '1536x1536 square' if rows == 3 else '1536x1024 landscape'
        prompt = f'''Use case: style-transfer. Author a coherent MM7/MM8-style game animation sheet for the MM5 Troll Grunt.
Input 1 is the selected five-view enhanced IDENTITY reference. Preserve this exact creature: stocky crouched teal troll, broad ugly face, long pointed ears, short tusks, yellow-green eyes, shaggy brick-red hair, ragged sleeveless cobalt-blue cloth vest with bare chest, muted purple trousers, ochre rope belt, plain dark cuffed leather boots, rough wooden club in anatomical RIGHT hand. Same materials, hair length, face, proportions, club size and restrained restored pre-rendered RPG shading in every cell. No added equipment.
Input 2 is only a NATIVE MM8 MOTION/POSE reference, already reflected for the correct hand. It is not identity, clothing, colors or body design authority. Translate its motion phases onto the stockier identity character, retain consistent bone lengths. Input 3 is original MM5 design provenance only.
OUTPUT: {shape} PNG, exactly {cols} columns x {rows} rows of equal cells, {count} complete occupied cells in row-major order, remaining cell EMPTY. No labels or grid lines. Direction in EVERY cell: {VIEWS[view]}. The same camera angle as identity cell {view+1}; no view drift during animation. {descriptions[action]}
Use the identity's anatomical scale consistently, with an upright-equivalent hair-to-sole height about 390 pixels within each 512px-high output cell. Do not fit each pose to an equal bounding box. Standing ground line at local y=460 and ground root at x=256; preserve actual foot lifts and intentional lean/motion from the pose reference. Collapsed poses occupy much less height while keeping limb lengths. Leave 24px safety padding around complete club, hands, hair, boots. No cropped parts, overlapping cells, independently resized characters or duplicated poses.
Lighting: fixed soft upper-left/front illumination, subdued earthy tonal weight, detailed natural cloth folds, matte teal skin, dark worn leather, no rim glow, glossy plastic, exaggerated specular, comic outlines, pixel blocks or dither. Reconstruct fine shading like the accepted identity, not enlarged pixels from the pose reference.
Background: genuine transparent alpha, including empty cells; preserve clean thin hair/cloth edges. No painted checkerboard, background, ground plane, cast shadow, text or watermark.
'''
        (HERE / f'prompts/{key}.txt').write_text(prompt)
        jobs[key] = dict(frames=names, action=action, view=view, columns=cols, rows=rows,
                         native_union_crop=crop, reference_cell=[cw,ch], state='prepared',
                         references=['raw/identity_v2.png', f'references/{key}.png', 'references/mm5_design.png'])
    save_json(HERE / 'jobs.json', jobs)
    animations = donor['bindings']['58']['actions']
    save_json(HERE / 'sources.json', dict(schema_version=1, creature='mm5:troll_grunt',
        source_appearance='MM5 DARK.CC 056.mon / 056.att, decoded with mm4.pal',
        source_frames=native_sources, motion_sources=motion_sources, motion_palette=source_record(palette_path),
        motion_template='MM8 Troll A: descriptor 58; group m477*, textures m476*; reference mirrored',
        target_unique_frames=160, native_mm5_frame_count=12,
        adaptation_note='All final art is newly authored. MM8 timing/topology is an explicit adaptation, not MM5 native timing. Hidden MM5 views and locomotion/death are inferred.',
        mm5_shared_resource_records=['Troll Grunt (56)', 'Troll Guard (81)', 'Troll Chief (82)', 'Hobstadt (83)'],
        palette_note='One decoded native appearance; no distinct native recolor presets established. Do not invent native variants.',
        motion_animations=animations))
    print(f'Prepared {len(jobs)} motion sheets; {sum(len(j["frames"]) for j in jobs.values())}+5 identity = 160 frames')


if __name__ == '__main__':
    main()
