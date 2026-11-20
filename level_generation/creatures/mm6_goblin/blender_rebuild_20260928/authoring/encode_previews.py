"""Encode locally rendered review frames; no model or texture modification."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'review/final'


def main(folder=FOLDER):
    status = json.loads((folder / 'status.json').read_text())
    assert status['state'] == 'complete', status
    clips = json.loads((folder / 'clips.json').read_text())
    clips += json.loads((folder / 'inspection_clips.json').read_text())
    for clip in clips:
        source = folder / clip['folder']
        command = ['ffmpeg', '-y', '-loglevel', 'error']
        if clip['name'] == 'corpse':
            command += ['-loop', '1', '-i', str(source / '000.png'), '-t', '1', '-r', '24']
        else:
            command += ['-framerate', str(clip['fps']), '-i', str(source / '%03d.png')]
        if clip['name'] == 'death':
            command += ['-vf', 'tpad=stop_mode=clone:stop_duration=0.75']
        command += ['-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(folder / clip['video'])]
        subprocess.run(command, check=True)
    for name in ['attack', 'walk', 'death']:
        if name not in {clip['name'] for clip in clips}:
            continue
        layout = '4x3' if name == 'walk' else '3x3'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i',
                        str(folder / ('frames_' + name) / '%03d.png'),
                        '-vf', r'select=not(mod(n\,2)),scale=400:400,tile=' + layout,
                        '-frames:v', '1', str(folder / (name + '_sheet.png'))], check=True)
    print('Encoded', len(clips), 'motion previews and available inspection sheets in', folder)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, default=FOLDER)
    main(parser.parse_args().folder)
