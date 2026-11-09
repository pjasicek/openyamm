"""Package correctly timed previews from the reimported GLB renders."""
from pathlib import Path
import hashlib
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review'
NATIVE = ROOT.parent / 'direct_complete/native'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
BG = (35, 44, 40, 255)
FPS = 48

def panel(image, label, size=(600, 682)):
    out = Image.new('RGBA', size, BG)
    out.alpha_composite(image.convert('RGBA'), (0, 32))
    ImageDraw.Draw(out).text((12, 6), label, font=FONT, fill=(235, 237, 227))
    return out.convert('RGB')

def native_frame(index):
    image = Image.open(NATIVE / f'gobat{"abcdef"[index]}0.png').convert('RGBA')
    scale = 1.73
    resized = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.NEAREST)
    out = Image.new('RGBA', (600, 650))
    out.alpha_composite(resized, (round(300-177.5*scale), round(590-image.height*scale)))
    return out

def video(filename, frames):
    w, h = frames[0].size
    # Six repeats make these short clips convenient in ordinary video players.
    process = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                                '-f', 'rawvideo', '-pixel_format', 'rgb24',
                                '-video_size', f'{w}x{h}', '-framerate', str(FPS),
                                '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18',
                                '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                                str(OUT / filename)], stdin=subprocess.PIPE)
    for _ in range(6):
        for frame in frames:
            process.stdin.write(frame.convert('RGB').tobytes())
    process.stdin.close()
    assert process.wait() == 0

comparison, three_views = [], []
for frame in range(36):
    native = panel(native_frame(frame//6), 'Native MM6 • held 125 ms per pose')
    views = [panel(Image.open(OUT / f'attack_{view}_{frame:02}.png'), label)
             for view, label in [('front', 'New 3D • front'), ('quarter', 'New 3D • quarter'),
                                 ('back', 'New 3D • back')]]
    for target, panels in [(comparison, [native, views[0], views[1]]), (three_views, views)]:
        out = Image.new('RGB', (1800, 682))
        for column, image in enumerate(panels):
            out.paste(image, (column*600, 0))
        target.append(out)
video('attack_comparison.mp4', comparison)
video('attack_three_views.mp4', three_views)
closeups = []
for frame in range(36):
    combined = Image.new('RGB', (1052, 342), BG[:3])
    draw = ImageDraw.Draw(combined)
    for column, view in enumerate(['front', 'quarter']):
        image = Image.open(OUT/f'attack_{view}_{frame:02}.png').convert('RGBA')
        cropped = image.crop((44, 130, 570, 440))
        background = Image.new('RGBA', cropped.size, BG)
        background.alpha_composite(cropped)
        combined.paste(background.convert('RGB'), (column*526, 32))
        draw.text((column*526+12, 6), f'Corrected arm / hand • {view}', font=FONT, fill='white')
    closeups.append(combined)
video('hand_repair/corrected_attack_closeup.mp4', closeups)
durations = [round((i+1)*1000/FPS)-round(i*1000/FPS) for i in range(36)]
three_views[0].save(OUT / 'attack_preview.webp', save_all=True, append_images=three_views[1:],
                    duration=durations, loop=0, quality=90, method=4)

contact = Image.new('RGB', (1800, 682), BG[:3])
for column in range(6):
    images = [native_frame(column), Image.open(OUT / f'attack_front_{column*6:02}.png')]
    for row, image in enumerate(images):
        small = panel(image, f'{"Native" if row == 0 else "New"} • {column*.125:.3f}s')
        contact.paste(small.resize((300, 341), Image.Resampling.LANCZOS), (column*300, row*341))
contact.save(OUT / 'native_attack_comparison.png')
for name, end in [('Running', 32), ('Walking', 50), ('Hit_Reaction_1', 58), ('Idle_Sword', 48)]:
    frames = [panel(Image.open(OUT / f'{name}_{i:02}.png'), name) for i in range(end)]
    video(f'{name}.mp4', frames)

report = json.loads((OUT / 'export_verification.json').read_text())
report['artifact_sha256'] = {
    name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    for name in ['goblin_finished.blend', 'goblin_finished.glb', 'inputs/gob_source.glb']
}
source = Path('/home/pjasicek/Downloads/gob.glb')
assert hashlib.sha256(source.read_bytes()).hexdigest() == report['artifact_sha256']['inputs/gob_source.glb']
report['original_source_unchanged'] = True
report['preview_timing'] = {'fps': FPS, 'attack_seconds': .75, 'native_pose_seconds': .125,
                            'video_repeats': 6, 'attack_webp_milliseconds': sum(durations)}
(OUT / 'export_verification.json').write_text(json.dumps(report, indent=2)+'\n')
print('PREVIEWS_COMPLETE', json.dumps(report['preview_timing']))
