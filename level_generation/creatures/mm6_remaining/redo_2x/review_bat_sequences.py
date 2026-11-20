"""Comparable native-canvas motion strips; never fit individual silhouettes."""
import json

from PIL import Image, ImageDraw

from prepare_run import REPO, native


def main():
    root = REPO / 'level_generation/creatures/mm6_bat'
    out = root / 'redo_2x'
    registration = json.loads((out / 'registration.json').read_text())
    manifest = json.loads((root / 'manifest.json').read_text())
    sequences = [('walk', str(view)) for view in range(5)] + [
        ('attack', '0'), ('hit', '0'), ('death', '0')]
    for page in range(2):
        panel = Image.new('RGB', (1480, 1400), (40, 42, 41))
        draw = ImageDraw.Draw(panel)
        for row, (action, view) in enumerate(sequences[page * 4:page * 4 + 4]):
            names = [s['frame'] for s in manifest['animations'][action]['views'][view]]
            source = [native(root, name) for name in names]
            bounds = [image.getbbox() for image in source]
            crop = [min(b[0] for b in bounds)-6, min(b[1] for b in bounds)-6,
                    max(b[2] for b in bounds)+6, max(b[3] for b in bounds)+6]
            width, height = crop[2]-crop[0], crop[3]-crop[1]
            ratio = min(240/width, 145/height)
            size = (round(width*ratio), round(height*ratio))
            draw.text((4, row*350+2), action+' view '+view+'; native above, restored below', fill='white')
            for column, (name, original) in enumerate(zip(names, source)):
                origin = registration[name]['canvas_origin_px']
                restored = Image.open(out/'aligned_2x'/(name+'.png')).convert('RGBA')
                restored = restored.crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                          crop[2]*2-origin[0], crop[3]*2-origin[1]))
                for index, image in enumerate([original.crop(crop), restored]):
                    rendered = image.resize(size, Image.Resampling.NEAREST if index == 0
                                            else Image.Resampling.LANCZOS)
                    panel.paste(rendered, (column*246+(240-size[0])//2,
                                          row*350+25+index*160), rendered)
                draw.text((column*246+4,row*350+330), name, fill='white')
        panel.save(out/'review'/('assembled_sequences_%d.png'%page))


if __name__ == '__main__':
    main()
