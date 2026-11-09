"""Prepare selective detail replacements from existing native and accepted art checkpoints."""
import argparse
import json
import shutil
from pathlib import Path
from PIL import Image


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--batch', action='append', required=True)
    args = parser.parse_args()
    root = args.project
    batches = json.loads((root / 'batches.json').read_text())
    generation = json.loads((root / 'generation.json').read_text())
    config = dict(creature='armored crusader', description="Slim adult armored fighter with cylindrical closed silver visor helmet, narrow horizontal eye slit and curved green/white plume. Silver steel plates and chainmail, restrained gold edging, deep forest-green surcoat with original white heraldic emblem and diagonal white bands, dark leather joints, steel boots and straight sword. Preserve native sword grip, foreshortening, raised/planted feet, torso bends and limb visibility. No bulky modern redesign, oversized pauldrons, new accessories, glow or dramatic rim lighting. Preserve original dark tonal weight, readable silver highlights, dark recesses and soft upper-left baked light. Keep white heraldry, steel, gold and leather separate from green cloth and plume for selective recoloring.")
    assert not (root / 'detail_rebatch_plan.json').exists(), 'Resume the existing plan instead.'
    checkpoint = root / 'checkpoints/before_sampling_repair'
    checkpoint.mkdir(parents=True, exist_ok=True)
    for name in ['batches.json', 'generation.json', 'registration.json', 'processing_settings.json',
                 'validation.json', 'README.md', 'review/acceptance.json', 'config.json',
                 'hair_regions.json', 'hair_overlap_corrections.json']:
        source = root / name
        target = checkpoint / name
        if source.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    plan = {}
    for key in args.batch:
        old = batches.pop(key)
        names = old['frames']
        bounds = [Image.open(root / f'native/{name}.png').getbbox() for name in names]
        window = [min(b[0] for b in bounds)-6, min(b[1] for b in bounds)-6,
                  max(b[2] for b in bounds)+6, max(b[3] for b in bounds)+6]
        width, height = window[2]-window[0], window[3]-window[1]
        for capacity, columns in [(6, 3), (4, 2), (2, 1)]:
            aspect = columns*width/(2*height)
            output = [1024, 1536] if aspect < .7 else [1254, 1254] if aspect <= 1.25 else [1536, 1024]
            sampling = min(output[0]/(columns*width), output[1]/(2*height))
            if sampling >= 2.2:
                break
        assert sampling >= 2.2, (key, window, 'Requires custom layout')
        starts = list(range(0, max(1, len(names)-capacity+1), capacity-1))
        if starts[-1]+capacity < len(names):
            starts.append(max(0, len(names)-capacity))
        exported = set()
        for index, start in enumerate(starts):
            selected = names[start:start+capacity]
            references = [name for name in selected if name in exported]
            exported.update(selected)
            new_key = f'{key}_detail_{index}'
            cell = [width*4, height*4]
            batch = dict(old, frames=selected, columns=columns, rows=2, cell_size=cell,
                         native_window=window, reference_scale=4, reference_only_frames=references)
            batches[new_key] = batch
            sheet = Image.new('RGB', (columns*cell[0], 2*cell[1]), (255, 0, 255))
            for i, name in enumerate(selected):
                native = Image.open(root / f'native/{name}.png').crop(window)
                tile = native.resize(cell, Image.Resampling.NEAREST)
                sheet.paste(tile, (i % columns*cell[0], i // columns*cell[1]), tile)
            sheet.save(root / f'references/{new_key}.png')
            prior = generation['batches'][key]['selected']
            shape = 'portrait' if output[1] > output[0] else 'square' if output[0] == output[1] else 'landscape'
            prompt = f'''Use case: style-transfer. Faithfully restore these Might and Magic VII native {config['creature']} animation sprites, preserving the accepted enhanced identity and art style.
Input 1 controls exact POSE, VIEW and LAYOUT: {columns} columns by TWO rows; {len(selected)} occupied cells in row-major order: {', '.join(selected)}. Leave unused cells fully transparent. Camera: {old.get('direction', 'native stored view')}.
Input 2 is the accepted enhanced standing identity/material reference. Input 1 controls the new layout and every limb angle, sword grip, sword projection and plume shape. Preserve the slim armor proportions and white heraldry.
Identity: {config['description']}
Preserve every native pose, equipment, small effects, thin features, proportions, silhouette, foot contact and tonal weight. Keep one common anatomical scale and source-relative cell positions. No per-pose zoom, stretching, recentering or generic standing substitutions. Clarify fine material surfaces with restrained native upper-left baked lighting, without enlarged pixel stair steps. Keep material boundaries distinct for deterministic offline masks.
Generate a high-detail {shape} canvas, approximately {output[0]} by {output[1]} pixels or larger with the same layout. All anatomy, arrows, weapons and thin tips must stay fully within their cells, with clear transparent gutters. Preserve the supplied crop margins.
Deliver an RGBA PNG with genuine transparent background and clean alpha edges. Do not paint a checkerboard, key color, black or white backdrop. Keep empty canvas and gutters transparent. No background shadows, gradients, text, labels, grid lines, colored bounce or halos. No added effects or redesign.
'''
            (root / f'prompts/{new_key}.txt').write_text(prompt)
            (root / f'prompts/submitted/{new_key}_v1.txt').write_text(prompt)
            plan[new_key] = dict(replaces=key, frames=selected, reference_only_frames=references,
                                 prior_art=prior, status='pending_generation', native_window=window,
                                 observed_output_budget=output, projected_sampling=sampling)
        assert exported == set(names)
    (root / 'batches.json').write_text(json.dumps(batches, indent=2)+'\n')
    (root / 'detail_rebatch_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps(plan, indent=2))


if __name__ == '__main__':
    run()
