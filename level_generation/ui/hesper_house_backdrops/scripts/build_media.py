#!/usr/bin/env python3
"""Downsample the selected Codex masters and package them for the existing house-video player."""
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
manifest_path = PROJECT / 'generation_runs_house_backdrops.json'
manifest = json.loads(manifest_path.read_text())
backdrops = json.loads((PROJECT / 'backdrops.json').read_text())
jobs = manifest['jobs']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert len(jobs) == len(backdrops) * 2
sheet = Image.new('RGB', (3 * 480, -(-len(backdrops) // 3) * 378), (25, 25, 30))
draw = ImageDraw.Draw(sheet)
for index, backdrop in enumerate(backdrops):
    candidates = [job for job in jobs if job['key'] == backdrop['key']]
    assert {job['candidate'] for job in candidates} == {1, 2}
    assert all(job['status'] == 'generated' for job in candidates)
    chosen = [job for job in candidates if job['selected']]
    assert len(chosen) == 1, backdrop['key']
    job = chosen[0]
    source = PROJECT / job['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == job['sha256']
    still = PROJECT / 'selected' / f"hes_house_{job['key']}.png"
    video = PROJECT / 'runtime' / f"hes_house_{job['key']}.ogv"
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                    '-vf', 'scale=460:344:flags=lanczos,setsar=1', '-frames:v', '1', str(still)], check=True)
    # Theora output is not byte-stable: keep a clip whose still and clip still match the recorded exports.
    recorded = job.get('exports', {})
    if not (video.exists() and recorded.get(str(still.relative_to(PROJECT))) == digest(still)
            and recorded.get(str(video.relative_to(PROJECT))) == digest(video)):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-framerate', '25',
                        '-i', str(still), '-t', '2', '-an', '-c:v', 'libtheora', '-q:v', '10',
                        '-pix_fmt', 'yuv420p', '-map_metadata', '-1', str(video)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                               '-of', 'json', str(video)]))['streams']
    assert len(probe) == 1 and probe[0]['codec_name'] == 'theora'
    assert (probe[0]['width'], probe[0]['height']) == (460, 344)
    assert abs(float(probe[0]['duration']) - 2) < .05
    job['exports'] = {str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in (still, video)}
    x, y = (index % 3) * 480 + 10, (index // 3) * 378
    draw.text((x, y + 6), f"{job['picture']} {job['key']} / candidate {job['candidate']}", fill='white')
    with Image.open(still) as image:
        assert image.size == (460, 344)
        sheet.paste(image, (x, y + 26))
sheet.save(PROJECT / 'review/selected_sheet.jpg', quality=95)
manifest['export'] = {'size': [460, 344], 'resampling': 'ffmpeg Lanczos; full frame, no crop',
                      'codec': 'Theora', 'quality': 10, 'pixel_format': 'yuv420p',
                      'seconds': 2, 'fps': 25, 'audio': False}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(f"PASS: {len(backdrops)} native-size PNGs and silent Theora clips; raw masters preserved")
