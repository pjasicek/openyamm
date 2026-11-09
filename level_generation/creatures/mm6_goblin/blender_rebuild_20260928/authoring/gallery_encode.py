"""Encode and verify the complete gallery, optionally alongside the Blender render queue."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'review/complete_gallery'


def render_status():
    # Blender replaces this small progress document after each frame; retry an overlapping read briefly.
    for attempt in range(5):
        try:
            return json.loads((FOLDER / 'status.json').read_text())
        except json.JSONDecodeError:
            if attempt == 4:
                raise
            time.sleep(.02)


def main(watch=False, actions_to_encode=None):
    manifest = json.loads((FOLDER / 'manifest.json').read_text())
    actions = {action['id']: action for action in manifest['actions']}
    results = []
    for clip in manifest['clips']:
        action = actions[clip['action']]
        folder = FOLDER / clip['folder']
        frames = [folder / (str(index).zfill(3) + '.png') for index in range(clip['frame_count'])]
        while not all(path.exists() for path in frames):
            status = render_status()
            if not watch or status['state'] in ['error', 'complete']:
                raise RuntimeError('Incomplete clip ' + str(clip) + ': ' + str(status))
            time.sleep(1)
        # A file appears before Blender finishes writing it. The render queue advances only afterwards.
        if watch:
            while True:
                status = render_status()
                if status['state'] != 'rendering' or (status['action'], status['view']) != (clip['action'], clip['view']):
                    break
                time.sleep(.3)
        for path in frames:
            header = path.read_bytes()[:24]
            assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (960, 960), path
        output = FOLDER / clip['video']
        command = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-threads', '2']
        if action['id'] == 'corpse':
            command += ['-loop', '1', '-framerate', str(action['fps']), '-i', str(frames[0]), '-t', '1']
        else:
            command += ['-framerate', str(action['fps']), '-i', str(folder / '%03d.png')]
        if action['end_hold']:
            command += ['-vf', 'tpad=stop_mode=clone:stop_duration=' + str(action['end_hold'])]
        command += ['-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(output)]
        encode = actions_to_encode is None or clip['action'] in actions_to_encode
        if encode:
            subprocess.run(command, check=True)
        probe = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
            'stream=codec_name,pix_fmt,width,height,nb_frames,duration,avg_frame_rate', '-of', 'json', str(output)]))['streams'][0]
        count = action['fps'] if action['id'] == 'corpse' else clip['frame_count']
        count += round(action['end_hold'] * action['fps'])
        assert probe['width'] == probe['height'] == 960 and int(probe['nb_frames']) == count, probe
        rate_numerator, rate_denominator = map(int, probe['avg_frame_rate'].split('/'))
        assert rate_numerator == action['fps'] * rate_denominator, probe
        assert probe['codec_name'] == 'h264' and probe['pix_fmt'] == 'yuv420p', probe
        assert abs(float(probe['duration']) - count / action['fps']) < .00001, probe
        results.append({'action': action['id'], 'view': clip['view'], 'file': clip['video'],
                        'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                        'video_frames': count, 'rendered_frames': clip['frame_count'], 'probe': probe})
        (FOLDER / 'encoding_status.json').write_text(json.dumps({'state': 'encoding', 'completed': len(results),
                                                               'total': len(manifest['clips'])}) + '\n')
        print('Encoded' if encode else 'Verified', len(results), '/', len(manifest['clips']),
              action['id'], clip['view'], flush=True)
    assert len(results) == 56
    source = FOLDER / manifest['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['source_sha256']
    (FOLDER / 'video_validation.json').write_text(json.dumps({
        'status': 'pass', 'clips': 56, 'actions': 7, 'views': 8, 'rendered_frames': sum(c['rendered_frames'] for c in results),
        'source_sha256': manifest['source_sha256'], 'source_unchanged': True, 'videos': results}, indent=2) + '\n')
    (FOLDER / 'encoding_status.json').write_text('{"state":"complete","completed":56,"total":56}\n')
    print('All 56 videos verified against the gallery manifest.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--actions', nargs='+', choices=['standing', 'walk', 'attack', 'hit', 'death', 'corpse', 'fidget'],
                        help='Encode only these actions; verify all other existing videos.')
    args = parser.parse_args()
    main(args.watch, args.actions)
