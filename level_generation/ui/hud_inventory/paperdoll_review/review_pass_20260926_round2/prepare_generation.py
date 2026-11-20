"""Prepare four modest, deduplicated weapon sheets for this round's explicit feedback."""
import math
from PIL import Image
from prepare import OUT, HERE, read, write, digest
import json


GROUPS = [
    ['item001', 'item003', 'item004', 'item005', 'item011', 'item018', 'item333', '7item004'],
    ['7item015', '7item022', '7item219', '7item220', '7item221', 'brsword2', 'brsword3', 'cutlass1'],
    ['dagger1', 'dagger2', 'dagger3', 'dagger4', 'dagger5', 'ldagger3', 'item021'],
    ['item010', 'item242', 'item244', '7item030', '7item218', '2hsword3', 'item155'],
]


def main():
    catalog = json.loads((HERE/'catalog.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets = catalog['assets']
    seen = {}
    batches = []
    for index, names in enumerate(GROUPS, 1):
        unique = []
        hashes = set(seen)
        for name in names:
            if assets[name]['sourceHash'] not in hashes:
                unique.append(name)
                hashes.add(assets[name]['sourceHash'])
        names = unique
        cols, rows = 4, math.ceil(len(names)/4)
        cell_width = (max(assets[n]['size'][0] for n in names)+20)*2
        cell_height = (max(assets[n]['size'][1] for n in names)+20)*2
        cell_width = max(cell_width, math.ceil(rows*cell_height/(2*cols)))
        reference = Image.new('RGBA', (cols*cell_width, rows*cell_height))
        cells = []
        for i, name in enumerate(names):
            a = assets[name]
            seen[a['sourceHash']] = a['id']
            native_path = HERE/'native'/(a['id']+'.png')
            native = Image.open(native_path).convert('RGBA')
            native = native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST)
            x = i%cols*cell_width+(cell_width-native.width)//2
            y = i//cols*cell_height+(cell_height-native.height)//2
            reference.alpha_composite(native, (x, y))
            cells.append({'name': name, 'target': a['id'], 'source_hash': a['sourceHash'],
                          'native_png_sha256': digest(native_path), 'rect': [x,y,native.width,native.height],
                          'slot': [i%cols*cell_width,i//cols*cell_height,cell_width,cell_height]})
        folder = OUT/'generated'/f'weapons_{index:02}'
        folder.mkdir(parents=True, exist_ok=True)
        reference.save(folder/'native.png')
        descriptions = '\n'.join(f'Cell {i+1}: {c["name"]}.' for i,c in enumerate(cells))
        special = {
            1: 'Cell 1 and cell 5 are cheap worn iron blades: retain only a few subtle irregular chips, never regular saw teeth. Cell 2 is a wavy silver blade with a dark hilt. Cell 7 is a dark metal blade, not green. The lower right slot is empty.',
            2: 'All steel is neutral silver or dark steel matching the native reference. Cell 7 has a faint neutral metal reflection, NOT the purple tint of the previous restoration. Keep every distinct curved or hooked blade and guard design. Cell 5 retains its gold/silver wing-like guard and short proportions.',
            3: 'Reconstruct clean, pointed dagger edges, original colorful gems and original handles. Cell 7 needs a SLIM blade matching its native width, not a broad leaf blade. The lower right slot is empty.',
            4: 'Cell 1 has a bifurcated tip and intentional small blade notches; keep its existing native black/red skull handle design. Cell 4 is a crescent axe with neutral silver dangling charms; NO purple or pink gems there. Cell 5 has a silver/gold winged hilt, no magenta gap fill. Cell 7 is an ivory/gold wand with a pierced round finial and scrollwork, NO magenta or purple on any part. The lower right slot is empty.'
        }[index]
        prompt = f'''Use case: precise-object-edit. Asset type: transparent game inventory/equipment spritesheet.
The attached image is the authoritative NATIVE DESIGN reference, not an image to enlarge. Repaint/reconstruct all {len(cells)} separate weapons as polished, detailed, coherent fantasy-game item art with clean antialiased edges and continuous material shading. This is a corrective restoration: previous versions failed because blade edges and highlights looked like enlarged source pixels and had green/magenta contour contamination.
Keep exactly the same 4 columns and 2 rows, equal cells, same target order, poses, geometry, weapon proportions and relative placement. Reconstruct metal surfaces and highlights rather than copying individual source pixel blocks. Preserve the exact handle/guard placement and thin blade proportions. Clean, sharp continuous blade edges; no block-shaped highlights, staircase teeth, noisy halos, dither, sharpened pixel grid, or invented tiny edge spikes. Metallic detail should read as smooth bevels, reflections, wear and engraving, not random mottled dots. Actual native intentional hooks/notches are retained smoothly. No added accessories or duplicate items.
Return a genuine transparent RGBA spritesheet. No background, panel, checkerboard, captions or guides. Keep every tip, guard, pommel and fine ornament fully inside its own cell, with transparent clearance all around. Never crop an item at a cell or canvas boundary. Do not put magenta/green backing into thin gaps, guard openings or between ornaments. Only the actual original gemstone colors may remain colorful.
Order is left to right, top row then bottom row:
{descriptions}
{special}
High-resolution reconstruction with individually resolved details and smooth curves; do not simulate pixel art. Keep the equal-cell grid so the outputs can be split reliably.
'''
        (folder/'prompt.txt').write_text(prompt)
        batch = {'name': folder.name, 'grid': [cols,rows], 'size': list(reference.size), 'cells': cells,
                 'input_sha256': digest(folder/'native.png'), 'tool': 'built-in image_gen'}
        write(folder/'manifest.json', batch)
        batches.append(batch)
    aliases = {a['id']: seen[a['sourceHash']] for a in assets.values()
               if a['sourceHash'] in seen and a['id'] != seen[a['sourceHash']]}
    write(OUT/'generated/batches.json', {'batches': batches, 'exact_native_aliases': aliases})
    print({'batches': [(b['name'],len(b['cells']),b['size']) for b in batches], 'aliases': aliases})


if __name__ == '__main__':
    main()
