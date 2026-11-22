#!/usr/bin/env python3
"""Install the Xeen sound picks into the world (lane AU, devdocs/xeen/AUDIO.md).

    python3 level_generation/sounds/xeen_20261120/install.py [--check]

For every name in install.yml: copies the processed pick out/<job>/<name>.wav to
assets_dev/worlds/xeen/audio/xeen/<name>.wav and writes the world's sound rows,
assets_dev/worlds/xeen/audio/sounds.txt (the `sounds` tableContributions file of world.yml). Files are written as a
temporary file and renamed (assets_dev files may share their inode with hard-link scratch roots). A name whose pick is
not processed yet is reported and left out; nothing else is touched. --check only reports what would change.
The installed copies are IMA ADPCM WAVs at the pick's rate (a quarter of 16-bit PCM; SDL_LoadWAV decodes them, lane P,
2026-11-22, the user's approval of a compact WAV format); the picks in out/ stay 16-bit PCM.

The engine finds a sound by its file name anywhere in the merged audio tree (game/audio/SoundCatalog.cpp), so every
name must be unique across the audio folders of all worlds: the script refuses a name another world already ships.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORLD = REPO / 'assets_dev/worlds/xeen'
TARGET = WORLD / 'audio/xeen'
TABLE = WORLD / 'audio/sounds.txt'
HEADER = [
    '/NAME\tID\tTYPE\t3D\tCOMMENTS',
    '/Xeen sounds (lane AU): written by level_generation/sounds/xeen_20261120/install.py from install.yml; do not edit.',
    '/Names are the files under worlds/xeen/audio/xeen/; ids are the world.yml sounds range (devdocs/xeen/AUDIO.md).',
]


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    temporary.chmod(0o644)
    temporary.replace(path)


def other_audio_names():
    names = {}
    for root in [REPO / 'assets_dev/engine/audio'] + sorted((REPO / 'assets_dev/worlds').glob('*/audio')):
        for path in root.rglob('*.wav'):
            if TARGET in path.parents:
                continue
            names.setdefault(path.stem.lower(), path)
    return names


def bed_highpass(data, job):
    """A loop's `bed_highpass_hz` (lane AU, session 3): the processing tool shapes one-shots only, so a bed whose
    takes sit mostly below the asked sound (the desert's wind rumble under its sand hiss) is high-passed here: a
    4th-order Butterworth run over the loop three times end to end and the middle kept (the seam stays continuous),
    then levelled again to the job's `loop_rms_db` with the peak at most -1 dBFS. Returns the new WAV bytes."""
    import io
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, sosfilt
    rate, samples = wavfile.read(io.BytesIO(data))
    audio = samples.astype(np.float64) / 32768.0
    sos = butter(4, float(job['bed_highpass_hz']), 'highpass', fs=rate, output='sos')
    audio = sosfilt(sos, np.concatenate([audio, audio, audio]), axis=0)[len(audio):2 * len(audio)]
    rms = float(np.sqrt(np.mean(audio ** 2))) or 1.0
    peak = float(np.max(np.abs(audio))) or 1.0
    gain = min(10 ** (float(job.get('loop_rms_db', -20.0)) / 20) / rms, 10 ** (-1.0 / 20) / peak)
    out = io.BytesIO()
    wavfile.write(out, rate, np.clip(np.round(audio * gain * 32767.0), -32768, 32767).astype(np.int16))
    return out.getvalue()


# IMA ADPCM block of the installed WAVs: 512 bytes, 1017 frames of a mono sound (4 header bytes per channel). SDL
# decodes whole blocks and ignores the fact chunk, so a sound plays a multiple of this many frames.
ADPCM_BLOCK_BYTES = 512


def adpcm_block_frames(channels):
    return (ADPCM_BLOCK_BYTES - 4 * channels) * 2 // channels + 1


def whole_blocks(data):
    """A loop resampled to a whole number of ADPCM blocks (at most one block longer, a pitch change under 4 cents for
    loops over 7 s): SDL pads the last block, which would put a gap of up to 21 ms into every repeat. The resample is
    periodic (FFT), so the seam stays continuous."""
    import io
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import resample
    rate, samples = wavfile.read(io.BytesIO(data))
    channels = 1 if samples.ndim == 1 else samples.shape[1]
    block = adpcm_block_frames(channels)
    frames = -(-len(samples) // block) * block
    if frames == len(samples):
        return data
    audio = resample(samples.astype(np.float64), frames, axis=0)
    out = io.BytesIO()
    wavfile.write(out, rate, np.clip(np.round(audio), -32768, 32767).astype(np.int16))
    return out.getvalue()


def compact_wav(data, loop):
    """The 16-bit PCM WAV data as an IMA ADPCM WAV (ffmpeg's adpcm_ima_wav, bit-exact: no encoder tag, so the same
    pick gives the same bytes); a loop first fills whole blocks (whole_blocks)."""
    if loop:
        data = whole_blocks(data)
    return subprocess.run(['ffmpeg', '-v', 'error', '-f', 'wav', '-i', 'pipe:0', '-map_metadata', '-1',
                           '-fflags', '+bitexact', '-flags', '+bitexact', '-c:a', 'adpcm_ima_wav',
                           '-block_size', str(ADPCM_BLOCK_BYTES), '-f', 'wav', 'pipe:1'],
                          input=data, capture_output=True, check=True).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    jobs = {job['id']: job for job in yaml.safe_load((HERE / 'jobs.yml').read_text())['jobs']}
    table = yaml.safe_load((HERE / 'install.yml').read_text())['sounds']
    ids = list(table.values())
    if len(set(ids)) != len(ids):
        sys.exit('install.yml: duplicate ids')
    if any(not 62000 <= i <= 63999 for i in ids):
        sys.exit('install.yml: an id outside 62000-63999')
    taken = other_audio_names()
    rows, changed, missing = [], [], []
    for name, sound_id in sorted(table.items(), key=lambda item: item[1]):
        job = jobs.get(name)
        if job is None:
            sys.exit(f'install.yml: {name} is not a job')
        if name.lower() in taken:
            sys.exit(f'{name}: another audio folder already has {taken[name.lower()]}')
        source = HERE / 'out' / name / f"{job.get('output', name)}.wav"
        if not source.exists():
            missing.append(name)
            continue
        data = source.read_bytes()
        if job.get('bed_highpass_hz'):
            data = bed_highpass(data, job)
        data = compact_wav(data, bool(job.get('loop')))
        target = TARGET / f'{name}.wav'
        if not target.exists() or hashlib.sha1(target.read_bytes()).digest() != hashlib.sha1(data).digest():
            changed.append(name)
            if not args.check:
                write_atomic(target, data)
        use = str(job.get('use', '')).replace('\t', ' ').replace('\n', ' ')
        rows.append(f'{name}\t{sound_id}\tswap\t0\t{use}')
    text = ('\n'.join(HEADER + rows) + '\n').encode('ascii', 'replace')
    table_changed = not TABLE.exists() or TABLE.read_bytes() != text
    if table_changed and not args.check:
        write_atomic(TABLE, text)
    stale = sorted(p.stem for p in TARGET.glob('*.wav') if p.stem not in table) if TARGET.exists() else []
    print(f"{len(rows)} rows, {len(changed)} WAVs {'to write' if args.check else 'written'}, "
          f"table {'differs' if table_changed else 'unchanged'}; not processed yet: {len(missing)}")
    if missing:
        print('  missing: ' + ', '.join(missing))
    if stale:
        print('  installed but not in install.yml (left alone): ' + ', '.join(stale))


if __name__ == '__main__':
    main()
