"""Prepare the new dirt's wrapping derivative and original-oriented transition composites/prompts."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
OLD = P.parents[1] / 'mm6_new_sorpigal_transitions'
sys.path.insert(0, str(OLD))
from compose_tiles import linear, srgb


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = P.parent / 'generated/dirt_v2_512.png'
    original = np.asarray(Image.open(source).convert('RGB'), dtype=float)
    shifted = np.roll(original, (256, 256), (0, 1))
    repair = np.asarray(Image.open(P/'materials/dirt_seam_raw.png').convert('RGB').resize(
        (512, 512), Image.Resampling.LANCZOS), dtype=float)
    y, x = np.mgrid[:512, :512]
    distance = np.minimum(abs(x-255.5), abs(y-255.5))
    t = np.clip((32-distance)/16, 0, 1)
    alpha = (t*t*(3-2*t))[:, :, None]
    a = np.roll(shifted*(1-alpha)+repair*alpha, (-256, -256), (0, 1))
    # Retain the established shared sampling contract: symmetric eight-pixel strips, fading by sixteen.
    for axis in [0, 1]:
        for i in range(16):
            weight = 1 if i < 8 else (16-i)/8
            if axis == 0:
                average = (a[i]+a[-1-i])/2
                a[i] = a[i]*(1-weight)+average*weight
                a[-1-i] = a[-1-i]*(1-weight)+average*weight
            else:
                average = (a[:, i]+a[:, -1-i])/2
                a[:, i] = a[:, i]*(1-weight)+average*weight
                a[:, -1-i] = a[:, -1-i]*(1-weight)+average*weight
    a = np.rint(a).astype('uint8')
    assert np.array_equal(a[32:-32, 32:-32], original[32:-32, 32:-32])
    Image.fromarray(a).save(P/'materials/dirt.png')
    small = Image.fromarray(a).resize((256, 256), Image.Resampling.LANCZOS)
    small.save(P/'materials/dirt_256.png')
    pix = np.asarray(small)
    assert np.array_equal(pix[:, 0], pix[:, -1]) and np.array_equal(pix[0], pix[-1])
    repeat = Image.new('RGB', (1280, 1280))
    for y in range(5):
        for x in range(5):repeat.paste(small, (x*256, y*256))
    repeat.save(P/'reports/dirt_repeat.png')
    materials = {'dirt': linear(a.astype(float))}
    for name in ['grass', 'volcano', 'cobbles']:
        shutil.copy2(OLD/'material_seams/connected_v2'/(name+'.png'), P/'materials'/(name+'.png'))
        materials[name] = linear(np.asarray(Image.open(P/'materials'/(name+'.png')).convert('RGB'), dtype=float))
    inventory = json.loads((P/'mask_inventory.json').read_text())['masks']
    for entry in inventory:
        name = entry['tile']
        mask = np.asarray(Image.open(P/'masks/connected_v4'/(name+'.png')).convert('L'), dtype=float)[:, :, None]/255
        composite = srgb(materials['dirt']*(1-mask)+materials[entry['white']]*mask)
        Image.fromarray(composite).save(P/'composites/v4'/(name+'.png'))
        prompt = (OLD/'edge_treatment/prompts/v1'/(name+'.txt')).read_text().strip()
        prompt += (' The dirt in image 1 is the NEW accepted chunky brown master: preserve its exact clod scale and palette. '
                   'Image 2 is this tile\'s exact original directional artwork, not a rotation template. '
                   'Respect every existing corner, inlet, hole, thin neck and road opening; do not simplify the silhouette. '
                   'Match the original\'s irregular local material interpenetration and subtle shaded bleed, '
                   'without a crisp cut-paper seam or a broad blurry halo. Return one square tile at 512x512.')
        (P/'edge_treatment/prompts/v1'/(name+'.txt')).write_text(prompt+'\n')
    for name, material in {'6dirttyl':'dirt', '6grastyl':'grass', '6voltyl':'volcano'}.items():
        Image.fromarray(srgb(materials[material])).save(P/'composites/v4'/(name+'.png'))
    (P/'reports/preparation.json').write_text(json.dumps({
        'master_source':str(source), 'master_sha256':digest(source),
        'dirt_derivative_sha256':digest(P/'materials/dirt.png'),
        'protected_center_448x448_unchanged':True,'runtime_opposite_edges_exact':True,
        'coverage':'connected_v4 copied unchanged; original native orientation retained',
        'composites':36,'new_edge_edits_required':33},indent=2)+'\n')
    print('Prepared periodic dirt derivative, 36 composites and 33 exact directional edge prompts.')


if __name__ == '__main__':main()
