#!/usr/bin/env python3
"""Generate game audio with ElevenLabs from a YAML job file, with a credit ledger and resume (tools/audio/README.md).

    tools/run_elevenlabs.sh plan    <jobs.yml>                 # jobs, variants, estimated and spent credits
    tools/run_elevenlabs.sh run     <jobs.yml> [ids...]        # generate what is missing, within the budget
    tools/run_elevenlabs.sh process <jobs.yml> [ids...]        # raw downloads -> processed WAVs, metrics, picks
    tools/run_elevenlabs.sh review  <jobs.yml>                 # writes <workspace>/review/index.html
    tools/run_elevenlabs.sh create-voice <jobs.yml> <design id> pN   # save a Voice Design preview as a voice

The workspace is the job file's directory: ledger.json (one entry per paid request), raw/<id>/ (the downloads),
out/<id>/ (processed variants v1.wav..., the pick as <output>.wav, prompt.txt) and picks.yml (automatic picks; a
`choice` written there by hand wins). A request whose raw download exists is never sent again: the raw file name
carries a hash of everything that shapes the request, so changing a prompt makes new variants and keeps the old.

The API key is read from a file (ELEVENLABS_API_KEY_FILE, default ~/.config/openyamm/elvenlabs.key) and sent only as
a request header; it is never printed, logged or put on a command line.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

import numpy as np
import yaml

API = 'https://api.elevenlabs.io'
KEY_FILE = Path(os.environ.get('ELEVENLABS_API_KEY_FILE', str(Path.home() / '.config/openyamm/elvenlabs.key')))
# Sound effects cost 40 credits per second of requested duration by the docs (overview/capabilities/sound-effects,
# 2026-10-23); TTS about one credit per character. The responses' `character-cost` header reported about 11 per
# second on 2026-10-23. The ledger records both; the budget is checked against the larger, so a header that
# under-reports can never overspend the cap.
SFX_CREDITS_PER_SECOND = 40
SAMPLE_RATE = 48000              # the engine mixes at 48 kHz stereo (engine/AudioSystem.cpp)
PCM_FORMATS = {'pcm_48000': 48000, 'pcm_44100': 44100, 'pcm_24000': 24000, 'pcm_22050': 22050}
KINDS = ('sfx', 'tts', 'music', 'voice_design')
# Eleven Music: 900 credits per minute (elevenlabs.io/pricing, 2026-10-23); its responses carry no cost header.
MUSIC_CREDITS_PER_MINUTE = 900


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def api_key():
    if not KEY_FILE.exists():
        raise SystemExit(f'No API key file at {KEY_FILE}')
    key = KEY_FILE.read_text().strip()
    if not key:
        raise SystemExit(f'The API key file {KEY_FILE} is empty')
    return key


# --- Job file and workspace -----------------------------------------------------------------------------------------
class Workspace:
    def __init__(self, jobs_path):
        self.jobs_path = jobs_path.resolve()
        self.root = self.jobs_path.parent
        data = yaml.safe_load(self.jobs_path.read_text())
        if data.get('schema') != 'openyamm.elevenlabs.jobs.v1':
            raise SystemExit('jobs file schema must be openyamm.elevenlabs.jobs.v1')
        self.budget = int(data['budget'])
        self.allow_music = bool(data.get('music', False))
        self.kind_budgets = {kind: int(value) for kind, value in (data.get('kind_budgets') or {}).items()}
        self.defaults = data.get('defaults', {})
        self.formats = list(self.defaults.get('formats', ['wav_48000', 'mp3_44100_192', 'mp3_44100_128']))
        self.jobs = []
        seen = set()
        for raw in data['jobs']:
            job = {**{k: v for k, v in self.defaults.items() if k != 'formats'}, **raw}
            if job['id'] in seen:
                raise SystemExit(f"job {job['id']} is listed twice")
            seen.add(job['id'])
            if job.get('kind') not in KINDS and job.get('kind') != 'derived':
                raise SystemExit(f"job {job['id']}: kind must be one of {KINDS} or derived")
            job.setdefault('output', job['id'])
            job.setdefault('variants', 1)
            job.setdefault('loop', False)
            job.setdefault('channels', 1)
            self.jobs.append(job)
        self.by_id = {job['id']: job for job in self.jobs}
        self.ledger_path = self.root / 'ledger.json'
        self.ledger = json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {'requests': []}
        self.picks_path = self.root / 'picks.yml'
        self.picks = (yaml.safe_load(self.picks_path.read_text()) or {}) if self.picks_path.exists() else {}

    def save_ledger(self):
        temporary = self.ledger_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.ledger, indent=1) + '\n')
        temporary.replace(self.ledger_path)

    def spent(self):
        """Credits charged by the API's own reports (the estimate where a response had none)."""
        return sum(entry['credits'] for entry in self.ledger['requests'])

    def committed_kind(self, kind):
        jobs = {job['id'] for job in self.jobs if job['kind'] == kind}
        return sum(max(entry['credits'], entry.get('estimate', 0)) for entry in self.ledger['requests']
                   if entry['job'] in jobs or entry.get('kind') == kind)

    def committed(self):
        """The conservative total the budget is checked against: per request the larger of report and estimate."""
        return sum(max(entry['credits'], entry.get('estimate', 0)) for entry in self.ledger['requests'])

    def select(self, ids):
        if not ids:
            return self.jobs
        missing = [i for i in ids if i not in self.by_id]
        if missing:
            raise SystemExit('unknown job ids: ' + ', '.join(missing))
        return [self.by_id[i] for i in ids]


def request_body(job):
    if job['kind'] == 'voice_design':
        # Voice Design (POST /v1/text-to-voice/design): one request returns three previews of the description,
        # each speaking `text` (100-1000 characters; the charge is that text).
        body = {'voice_description': job['prompt'], 'model_id': job.get('model', 'eleven_ttv_v3'),
                'text': job['text'], 'auto_generate_text': False, 'should_enhance': bool(job.get('enhance', False))}
        for key in ('guidance_scale', 'loudness', 'seed', 'quality'):
            if job.get(key) is not None:
                body[key] = job[key]
        return body
    if job['kind'] == 'music':
        assert str(job.get('model', 'music_v2_5')).startswith('music_'), job['id']
        return {'prompt': job['prompt'], 'music_length_ms': int(float(job['duration']) * 1000),
                'model_id': job.get('model', 'music_v2_5'), 'force_instrumental': bool(job.get('instrumental', True))}
    if job['kind'] == 'sfx':
        body = {'text': job['prompt'], 'model_id': job.get('model', 'eleven_text_to_sound_v2'),
                'prompt_influence': float(job.get('prompt_influence', 0.3))}
        if job.get('duration') is not None:
            body['duration_seconds'] = float(job['duration'])
        if job['loop']:
            body['loop'] = True
        return body
    return {'text': job['prompt'], 'model_id': job.get('model', 'eleven_multilingual_v2'),
            'voice_settings': job.get('voice_settings', {'stability': 0.5, 'similarity_boost': 0.75})}


def job_hash(job):
    shape = {'kind': job['kind'], 'body': request_body(job), 'voice': job.get('voice_id')}
    return hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()[:10]


def raw_paths(ws, job):
    """The raw downloads of a job's current request shape, one per variant (any extension)."""
    if job['kind'] == 'derived':
        return []
    directory = ws.root / 'raw' / job['id']
    stem = job_hash(job)
    result = []
    for index in range(1, job['variants'] + 1):
        if job['kind'] == 'voice_design':
            # The request's record (the previews' generated ids); the previews are <stem>_vN.pM.mp3 beside it.
            record = directory / f'{stem}_v{index}.json'
            result.append(record if record.exists() else None)
            continue
        found = sorted(directory.glob(f'{stem}_v{index}.*')) if directory.exists() else []
        result.append(found[0] if found else None)
    return result


def estimate(job):
    if job['kind'] == 'sfx':
        return math.ceil(float(job.get('duration') or 5.0) * SFX_CREDITS_PER_SECOND)
    if job['kind'] == 'tts':
        return len(job['prompt'])
    if job['kind'] == 'voice_design':
        return len(job['text'])
    if job['kind'] == 'music':
        return math.ceil(float(job['duration']) / 60.0 * MUSIC_CREDITS_PER_MINUTE)
    return 0


# --- Requests -------------------------------------------------------------------------------------------------------
def post(endpoint, body, output_format, key):
    url = f'{API}{endpoint}?output_format={output_format}'
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                     headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read(), dict(response.headers)


def post_json(endpoint, body, key, query=''):
    request = urllib.request.Request(f'{API}{endpoint}{query}', data=json.dumps(body).encode(), method='POST',
                                     headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read()), dict(response.headers)


def ledger_entry(ws, job, index, headers, cost, **extra):
    lower = {name.lower(): value for name, value in headers.items()}
    reported = lower.get('character-cost') or lower.get('x-character-count')
    entry = {'job': job['id'], 'kind': job['kind'], 'variant': index, 'hash': job_hash(job), 'time': now(),
             'request_id': lower.get('request-id') or lower.get('x-request-id'),
             'history_item_id': lower.get('history-item-id'), 'song_id': lower.get('song-id'),
             'credits': int(float(reported)) if reported else cost,
             'credits_source': 'api' if reported else 'estimate', 'estimate': cost, **extra}
    ws.ledger['requests'].append(entry)
    ws.save_ledger()
    print(f"  {job['id']} v{index}: {entry['credits']} credits ({entry['credits_source']}), "
          f'charged {ws.spent()}, committed {ws.committed()} of {ws.budget}')
    return entry


def generate_design(ws, job, index, key):
    """One Voice Design request: three previews, kept as <stem>_vN.pM.mp3 with a record of their generated ids."""
    import base64
    directory = ws.root / 'raw' / job['id']
    stem = f'{job_hash(job)}_v{index}'
    try:
        data, headers = post_json('/v1/text-to-voice/design', request_body(job), key,
                                  '?output_format=' + job.get('design_format', 'mp3_44100_192'))
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{job['id']} v{index}: HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:400]}")
    directory.mkdir(parents=True, exist_ok=True)
    previews = []
    for number, preview in enumerate(data.get('previews', []), start=1):
        path = directory / f'{stem}.p{number}.mp3'
        path.write_bytes(base64.b64decode(preview['audio_base_64']))
        previews.append({'preview': f'p{number}', 'generated_voice_id': preview['generated_voice_id'],
                         'duration_secs': preview.get('duration_secs'), 'file': path.name})
    record = directory / f'{stem}.json'
    record.write_text(json.dumps({'text': data.get('text'), 'previews': previews}, indent=1) + '\n')
    ledger_entry(ws, job, index, headers, estimate(job), format='design', bytes=record.stat().st_size,
                 output=str(record.relative_to(ws.root)))


def format_refused(error_body):
    text = error_body.lower()
    return any(word in text for word in ('output_format', 'output format', 'tier', 'subscription', 'not allowed'))


def generate(ws, job, index, key, dry_run):
    directory = ws.root / 'raw' / job['id']
    stem = f'{job_hash(job)}_v{index}'
    cost = estimate(job)
    if ws.committed() + cost > ws.budget:
        raise SystemExit(f"budget: {job['id']} v{index} (~{cost} credits) would pass the cap of {ws.budget} "
                         f'(committed {ws.committed()}, charged {ws.spent()}); stopping')
    cap = ws.kind_budgets.get(job['kind'])
    if cap is not None and ws.committed_kind(job['kind']) + cost > cap:
        raise SystemExit(f"budget: {job['id']} v{index} (~{cost} credits) would pass the {job['kind']} cap of {cap} "
                         f"(committed {ws.committed_kind(job['kind'])}); stopping")
    if dry_run:
        print(f"  would request {job['id']} v{index} (~{cost} credits)")
        return
    if job['kind'] == 'voice_design':
        generate_design(ws, job, index, key)
        return
    endpoint = {'sfx': '/v1/sound-generation', 'music': '/v1/music'}.get(job['kind'],
                                                                       f"/v1/text-to-speech/{job.get('voice_id')}")
    body = request_body(job)
    formats = list(job.get('formats') or ws.formats)
    for output_format in formats:
        try:
            data, headers = post(endpoint, body, output_format, key)
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', 'replace')[:400]
            if error.code in (400, 403, 422) and format_refused(detail) and output_format != formats[-1]:
                print(f'  {output_format} refused ({error.code}), trying the next format')
                ws.ledger.setdefault('format_refusals', {})[output_format] = detail
                ws.save_ledger()
                continue
            raise SystemExit(f"{job['id']} v{index}: HTTP {error.code}: {detail}")
        extension = output_format.split('_')[0]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{stem}.{output_format}.{extension}'
        path.write_bytes(data)
        if extension == 'pcm':
            # Raw PCM (interleaved stereo) kept losslessly as FLAC: the same samples at about half the size.
            flac = path.with_suffix('.flac')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ac', '2',
                            '-ar', str(PCM_FORMATS[output_format]), '-i', str(path), str(flac)], check=True)
            path.unlink()
            path = flac
        lower = {name.lower(): value for name, value in headers.items()}
        reported = lower.get('character-cost') or lower.get('x-character-count')
        entry = {'job': job['id'], 'kind': job['kind'], 'variant': index, 'hash': job_hash(job), 'time': now(),
                 'request_id': lower.get('request-id') or lower.get('x-request-id'),
                 'history_item_id': lower.get('history-item-id'), 'song_id': lower.get('song-id'),
                 'credits': int(float(reported)) if reported else cost,
                 'credits_source': 'api' if reported else 'estimate', 'estimate': cost,
                 'format': output_format, 'bytes': len(data), 'output': str(path.relative_to(ws.root))}
        ws.ledger['requests'].append(entry)
        ws.ledger['formats_accepted'] = sorted(set(ws.ledger.get('formats_accepted', [])) | {output_format})
        ws.save_ledger()
        print(f"  {job['id']} v{index}: {len(data)} bytes, {entry['credits']} credits ({entry['credits_source']}), "
              f'charged {ws.spent()}, committed {ws.committed()} of {ws.budget}')
        return
    raise SystemExit(f"{job['id']}: every output format was refused")


def args_allow_music(ws):
    """The user's decision to generate music with Eleven Music (README, 2026-10-23) is recorded in the job file."""
    return bool(ws.allow_music)


def cmd_run(ws, ids, dry_run):
    key = None if dry_run else api_key()
    for job in ws.select(ids):
        if job['kind'] == 'derived':
            continue
        if job['kind'] == 'music' and not args_allow_music(ws):
            raise SystemExit('music jobs need `music: true` in the job file (tools/audio/README.md, Licensing)')
        for index, path in enumerate(raw_paths(ws, job), start=1):
            if path is None:
                generate(ws, job, index, key, dry_run)
                time.sleep(0.3)
    print(f'charged {ws.spent()} credits; committed {ws.committed()} of the {ws.budget} cap')


def cmd_plan(ws, ids):
    total_missing = 0
    for job in ws.select(ids):
        paths = raw_paths(ws, job)
        missing = sum(path is None for path in paths) if job['kind'] != 'derived' else 0
        total_missing += missing * estimate(job)
        print(f"{job['id']:<24} {job['kind']:<7} {job.get('duration', '-')!s:>5}s x{job['variants']} "
              f"{'loop ' if job['loop'] else ''}done {len(paths) - missing}/{len(paths)} "
              f'~{missing * estimate(job)} credits to go')
    print(f'charged {ws.spent()}, committed {ws.committed()} of {ws.budget}; the missing requests are estimated at '
          f'{total_missing} (docs rate)')


# --- Processing -----------------------------------------------------------------------------------------------------
def decode(path):
    """A raw download as float32 (frames, channels) at SAMPLE_RATE."""
    output_format = path.suffixes[-2].lstrip('.') if len(path.suffixes) >= 2 else ''
    if output_format in PCM_FORMATS and path.suffix == '.pcm':
        # The sound-generation PCM is interleaved stereo (probed 2026-10-23: 1 s at pcm_48000 is 192 000 bytes).
        samples = np.frombuffer(path.read_bytes(), dtype='<i2').astype(np.float32) / 32768.0
        rate = PCM_FORMATS[output_format]
        audio = samples[:len(samples) // 2 * 2].reshape(-1, 2)
        if rate != SAMPLE_RATE:
            audio = resample(audio, rate)
        return audio
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels',
                            '-of', 'csv=p=0', str(path)], capture_output=True, text=True, check=True)
    channels = int(probe.stdout.strip() or 1)
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', str(channels),
                             '-ar', str(SAMPLE_RATE), '-'], capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, channels).copy()


def resample(audio, rate):
    data = audio.astype('<f4').tobytes()
    result = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ac', str(audio.shape[1]), '-ar', str(rate),
                             '-i', '-', '-f', 'f32le', '-ar', str(SAMPLE_RATE), '-'],
                            input=data, capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, audio.shape[1]).copy()


def db(value):
    return 20.0 * math.log10(max(float(value), 1e-9))


def envelope(mono, window=0.01):
    size = max(1, int(SAMPLE_RATE * window))
    count = len(mono) // size
    if count == 0:
        return np.array([np.sqrt(np.mean(mono ** 2))])
    return np.sqrt(np.mean(mono[:count * size].reshape(count, size) ** 2, axis=1))


def metrics(audio, loop):
    mono = audio.mean(axis=1)
    env = envelope(mono)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    spectrum = np.abs(np.fft.rfft(mono[:SAMPLE_RATE * 4] * np.hanning(min(len(mono), SAMPLE_RATE * 4))))
    frequencies = np.fft.rfftfreq(min(len(mono), SAMPLE_RATE * 4), 1.0 / SAMPLE_RATE)
    centroid = float(np.sum(frequencies * spectrum) / max(np.sum(spectrum), 1e-9))
    result = {'seconds': round(len(audio) / SAMPLE_RATE, 3), 'peak_db': round(db(peak), 1),
              'rms_db': round(db(np.sqrt(np.mean(mono ** 2))), 1),
              'clipped': int(np.sum(np.abs(audio) >= 0.999)),
              'silence': round(float(np.mean(env < 10 ** (-50 / 20))), 3),
              'centroid_hz': int(centroid)}
    if loop:
        span = int(0.1 * SAMPLE_RATE)
        head, tail = mono[:span], mono[-span:]
        result['seam_jump'] = round(float(abs(mono[0] - mono[-1])), 4)
        result['seam_level_db'] = round(abs(db(np.sqrt(np.mean(head ** 2))) - db(np.sqrt(np.mean(tail ** 2)))), 1)
        thirds = np.array_split(env, 3)
        levels = [db(np.mean(part)) for part in thirds]
        result['level_spread_db'] = round(max(levels) - min(levels), 1)
    else:
        loud = np.nonzero(env > 10 ** (-40 / 20))[0]
        result['onset_ms'] = int(loud[0] * 10) if len(loud) else -1
    return result


def declip(audio, threshold=0.995, context=6):
    """Rebuild flat-topped runs (the model's loud outputs clip at full scale) with a cubic spline through the
    neighbouring samples on each side; the result can exceed full scale until it is normalised."""
    from scipy.interpolate import CubicSpline
    audio = audio.copy()
    for channel in range(audio.shape[1]):
        signal = audio[:, channel]
        clipped = np.abs(signal) >= threshold
        if not clipped.any():
            continue
        edges = np.diff(np.concatenate([[0], clipped.astype(np.int8), [0]]))
        for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            if start < context or end + context > len(signal) or end - start > 400:
                continue
            known = np.concatenate([np.arange(start - context, start), np.arange(end, end + context)])
            spline = CubicSpline(known, signal[known])
            rebuilt = spline(np.arange(start, end))
            sign = np.sign(signal[start])
            # Keep the run's polarity and never go below the clip level.
            signal[start:end] = sign * np.maximum(np.abs(rebuilt), threshold)
    return audio


def trim_one_shot(audio):
    mono = np.abs(audio).max(axis=1)
    threshold_start, threshold_end = 10 ** (-50 / 20), 10 ** (-55 / 20)
    above = np.nonzero(mono > threshold_start)[0]
    if len(above) == 0:
        return audio
    start = max(0, above[0] - int(0.004 * SAMPLE_RATE))
    tail = np.nonzero(mono > threshold_end)[0]
    end = min(len(audio), tail[-1] + int(0.02 * SAMPLE_RATE))
    audio = audio[start:end].copy()
    fade_in = min(len(audio), int(0.001 * SAMPLE_RATE))
    audio[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
    fade_out = min(len(audio), int(0.03 * SAMPLE_RATE))
    audio[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
    return audio


def make_seamless(audio, crossfade_seconds):
    """Fold the tail into the head with an equal-power crossfade: the new end runs straight into the new start."""
    fade = min(int(crossfade_seconds * SAMPLE_RATE), len(audio) // 4)
    if fade < 2:
        return audio
    t = np.linspace(0.0, 1.0, fade)[:, None]
    body = audio[:len(audio) - fade].copy()
    body[:fade] = audio[:fade] * np.sin(t * math.pi / 2) + audio[len(audio) - fade:] * np.cos(t * math.pi / 2)
    return body


def cut_fade_out(audio, min_seconds=3.0, drop_db=6.0):
    """A music download that fades out (a written ending) is cut where the fade starts, so the fold joins music at the
    track's own level. The trailing run of 1 s windows more than `drop_db` below the median counts as the fade; a
    shorter run is a rhythmic dip and is kept. Returns the audio and the seconds cut."""
    mono = audio.mean(axis=1)
    levels = np.array([db(value) for value in envelope(mono, 1.0)])
    if len(levels) < 8:
        return audio, 0.0
    floor = float(np.median(levels)) - drop_db
    run = 0
    while run < len(levels) // 5 and levels[len(levels) - 1 - run] < floor:
        run += 1
    if run < min_seconds:
        return audio, 0.0
    keep = (len(levels) - run) * SAMPLE_RATE
    return audio[:keep], round(len(audio) / SAMPLE_RATE - keep / SAMPLE_RATE, 1)


def normalize(audio, job):
    peak = float(np.max(np.abs(audio))) or 1.0
    if job['loop']:
        target_rms = 10 ** (float(job.get('loop_rms_db', -20.0)) / 20)
        rms = float(np.sqrt(np.mean(audio ** 2))) or 1.0
        gain = min(target_rms / rms, 10 ** (-1.0 / 20) / peak)
    else:
        gain = 10 ** (float(job.get('peak_db', -1.0)) / 20) / peak
    return audio * gain


def punch_db(audio):
    """The loudest 100 ms window's RMS (dBFS): how loud the body of a one-shot plays, whatever its tail."""
    mono = audio.mean(axis=1)
    size = int(0.1 * SAMPLE_RATE)
    if len(mono) <= size:
        return db(np.sqrt(np.mean(mono ** 2)))
    power = np.convolve(mono ** 2, np.ones(size) / size, mode='valid')
    return db(np.sqrt(float(power.max())))


def low_share(audio, cutoff=200.0):
    """The share of the energy below `cutoff` Hz (0-1): the low end of a shot."""
    mono = audio.mean(axis=1)
    spectrum = np.abs(np.fft.rfft(mono)) ** 2
    frequencies = np.fft.rfftfreq(len(mono), 1.0 / SAMPLE_RATE)
    return float(spectrum[frequencies < cutoff].sum() / max(spectrum.sum(), 1e-12))


def count_hits(audio, window=0.02, dip_db=8.0, top_db=10.0, dip_windows=2):
    """Distinct shots in a one-shot: rises to within `top_db` of the loudest 20 ms window after a dip of at least
    `dip_db` below the previous hit lasting `dip_windows` windows (40 ms: a crackle's flicker is not a new shot).
    The Gate Bastion's twin shot should count 2."""
    levels = [db(value) for value in envelope(audio.mean(axis=1), window)]
    loudest = max(levels)
    count, armed, peak, low, below = 0, True, -200.0, 0.0, 0
    for level in levels:
        if armed:
            low = min(low, level)
            if level >= loudest - top_db and (count == 0 or level >= low + dip_db):
                count, armed, peak, below = count + 1, False, level, 0
        else:
            peak = max(peak, level)
            below = below + 1 if level <= peak - dip_db else 0
            if below >= dip_windows:
                armed, low = True, level
    return count


def shape_tone(audio, job):
    """Optional tone shaping of a one-shot: `highpass_hz` (a 2nd-order high-pass that drops sub-sonic rumble, which
    only eats headroom), `lowpass_hz` (a 2nd-order low-pass; with a high `highpass_hz` a small-speaker band) and
    `low_shelf: {hz, db}` (an RBJ low shelf, more low end for heavy shots)."""
    from scipy.signal import butter, lfilter, sosfilt
    if job.get('highpass_hz'):
        sos = butter(2, float(job['highpass_hz']), 'highpass', fs=SAMPLE_RATE, output='sos')
        audio = sosfilt(sos, audio, axis=0).astype(np.float32)
    if job.get('lowpass_hz'):
        sos = butter(2, float(job['lowpass_hz']), 'lowpass', fs=SAMPLE_RATE, output='sos')
        audio = sosfilt(sos, audio, axis=0).astype(np.float32)
    shelf = job.get('low_shelf')
    if shelf:
        gain = 10 ** (float(shelf['db']) / 40)
        w0 = 2 * math.pi * float(shelf['hz']) / SAMPLE_RATE
        alpha = math.sin(w0) / 2 * math.sqrt(2)          # shelf slope 1
        cos_w0, root = math.cos(w0), 2 * math.sqrt(gain) * alpha
        b = [gain * ((gain + 1) - (gain - 1) * cos_w0 + root), 2 * gain * ((gain - 1) - (gain + 1) * cos_w0),
             gain * ((gain + 1) - (gain - 1) * cos_w0 - root)]
        a = [(gain + 1) + (gain - 1) * cos_w0 + root, -2 * ((gain - 1) + (gain + 1) * cos_w0),
             (gain + 1) + (gain - 1) * cos_w0 - root]
        audio = lfilter(b, a, audio, axis=0).astype(np.float32)
    return audio


def limit(audio, ceiling, lookahead=0.002, release=0.06):
    """A look-ahead peak limiter: the gain needed to keep every sample under `ceiling`, held over the look-ahead
    window (so it is down before the peak arrives) and released smoothly. Returns the audio and the deepest gain
    reduction in dB."""
    from scipy.ndimage import minimum_filter1d
    level = np.abs(audio).max(axis=1)
    needed = np.minimum(1.0, ceiling / np.maximum(level, 1e-9))
    ahead = max(1, int(lookahead * SAMPLE_RATE))
    held = minimum_filter1d(needed, size=2 * ahead + 1, mode='nearest')
    coefficient = math.exp(-1.0 / (release * SAMPLE_RATE))
    gain = np.empty_like(held)
    current = 1.0
    for index, target in enumerate(held):                 # instant attack (look-ahead), exponential release
        current = target if target < current else target + (current - target) * coefficient
        gain[index] = current
    smooth = max(1, ahead // 2)
    padded = np.concatenate([np.full(smooth, gain[0]), gain, np.full(smooth, gain[-1])])
    gain = np.convolve(padded, np.ones(smooth) / smooth, mode='same')[smooth:-smooth]
    gain = np.minimum(gain, held)
    return audio * gain[:, None], round(-db(float(gain.min())), 1)


def make_loud(audio, job):
    """`loudness_db`: lift a peak-normalised one-shot until its loudest 100 ms (punch_db) reaches the target, a
    look-ahead limiter holding the peak at `peak_db` (never clipping). The boost is capped at `max_boost_db`."""
    ceiling = 10 ** (float(job.get('peak_db', -1.0)) / 20)
    target = float(job['loudness_db'])
    boost = 0.0
    result, reduction = audio, 0.0
    for _ in range(6):
        shortfall = target - punch_db(result)
        if shortfall < 0.1:
            break
        boost = min(boost + shortfall, float(job.get('max_boost_db', 10.0)))
        result, reduction = limit(audio * 10 ** (boost / 20), ceiling)
        if boost >= float(job.get('max_boost_db', 10.0)):
            break
    peak = float(np.max(np.abs(result))) or 1.0
    if peak > ceiling:
        result = result * (ceiling / peak)
    return result, round(boost, 1), reduction


def write_wav(path, audio):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(audio, -1.0, 1.0) * 32767.0).round().astype('<i2')
    with wave.open(str(path), 'wb') as stream:
        stream.setnchannels(audio.shape[1])
        stream.setsampwidth(2)
        stream.setframerate(SAMPLE_RATE)
        stream.writeframes(data.tobytes())


def write_audio(path, audio):
    """A WAV, or a FLAC (music masters: lossless at about half the size) through ffmpeg."""
    if path.suffix == '.wav':
        write_wav(path, audio)
        return
    data = (np.clip(audio, -1.0, 1.0) * 32767.0).round().astype('<i2')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ac', str(audio.shape[1]), '-ar', str(SAMPLE_RATE),
                    '-i', '-', str(path)], input=data.tobytes(), check=True)


def encode_mp3(source, target):
    """The engine's music format (GameAudioSystem reads Music/<N>.mp3): 320 kbit/s LAME, whose gapless header lets
    the decoder drop the encoder delay and padding, so a looped track wraps without a gap."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-codec:a', 'libmp3lame', '-b:a', '320k',
                    str(target)], check=True)


def music_metrics(audio):
    """Listening-oriented measures of a track: its level over time (how even or how swelling), the longest quiet gap,
    how busy it is (onsets per minute), the brightness, and how its ending and opening compare (the loop)."""
    mono = audio.mean(axis=1)
    window = 3 * SAMPLE_RATE
    levels = np.array([db(np.sqrt(np.mean(mono[i:i + window] ** 2) + 1e-12))
                       for i in range(0, max(1, len(mono) - window + 1), window)])
    env = envelope(mono, 0.05)
    quiet = env < 10 ** (-40 / 20)
    longest, run = 0, 0
    for value in quiet:
        run = run + 1 if value else 0
        longest = max(longest, run)
    frame = 2048
    count = len(mono) // frame
    spectra = np.abs(np.fft.rfft(mono[:count * frame].reshape(count, frame) * np.hanning(frame), axis=1))
    flux = np.maximum(np.diff(spectra, axis=0), 0).sum(axis=1)
    threshold = flux.mean() + 2 * flux.std()
    onsets = int(np.sum((flux[1:-1] > threshold) & (flux[1:-1] >= flux[:-2]) & (flux[1:-1] >= flux[2:])))
    minutes = len(mono) / SAMPLE_RATE / 60
    frequencies = np.fft.rfftfreq(frame, 1.0 / SAMPLE_RATE)
    mean_spectrum = spectra.mean(axis=0)
    centroid = float(np.sum(frequencies * mean_spectrum) / max(np.sum(mean_spectrum), 1e-9))
    median = float(np.median(levels))
    return {'seconds': round(len(audio) / SAMPLE_RATE, 1), 'peak_db': round(db(np.max(np.abs(audio))), 1),
            'rms_db': round(db(np.sqrt(np.mean(mono ** 2))), 1), 'clipped': int(np.sum(np.abs(audio) >= 0.999)),
            'silence': round(float(np.mean(quiet)), 3),
            'level_spread_db': round(float(np.percentile(levels, 90) - np.percentile(levels, 10)), 1),
            'loudest_window_db': round(float(levels.max() - median), 1),
            'longest_gap_s': round(longest * 0.05, 2), 'onsets_per_minute': int(onsets / max(minutes, 1e-6)),
            'centroid_hz': int(centroid), 'head_db': round(float(levels[0] - median), 1),
            'tail_db': round(float(levels[-1] - median), 1), 'arc_db': [round(float(v - median), 1) for v in
                                                                         [np.mean(part) for part in
                                                                          np.array_split(levels, 4)]]}


def music_score(job, info):
    """Higher is better for a loopable background track: even (no big swells), no dead gaps, not clipped, the asked
    length, and an opening and ending at the track's own level (no fade-out or finale to hide at the wrap)."""
    value = 100.0 - max(0.0, info['level_spread_db'] - 8.0) * 3 - max(0.0, info['loudest_window_db'] - 6.0) * 3
    value -= min(info['longest_gap_s'], 10) * 4 + min(info['raw_clipped'], 2000) * 0.01
    value -= abs(info['raw_seconds'] - float(job['duration'])) / float(job['duration']) * 20
    value -= max(0.0, abs(info['raw_head_db']) - 4) + max(0.0, abs(info['raw_tail_db']) - 4)
    return round(value, 1)


def music_note(info):
    arc = ' / '.join(f'{v:+.0f}' for v in info['arc_db'])
    busy = info['onsets_per_minute']
    texture = 'sparse' if busy < 40 else 'moving' if busy < 120 else 'busy'
    tone = 'dark' if info['centroid_hz'] < 1200 else 'warm' if info['centroid_hz'] < 2500 else 'bright'
    parts = [f'{texture} ({busy} onsets/min), {tone}', f'level by quarter {arc} dB',
             f"spread {info['level_spread_db']} dB, loudest 3 s {info['loudest_window_db']:+.0f} dB"]
    if info['longest_gap_s'] > 1.0:
        parts.append(f"a {info['longest_gap_s']} s quiet gap")
    if info.get('fade_cut_s'):
        parts.append(f"the download's {info['fade_cut_s']} s fade-out cut before the fold")
    if info['raw_tail_db'] < -6:
        parts.append(f"the download fades out ({info['raw_tail_db']:+.0f} dB), crossfaded into the opening")
    if info['raw_clipped']:
        parts.append(f"{info['raw_clipped']} clipped samples (declipped)")
    return '; '.join(parts)


def read_wav(path):
    with wave.open(str(path), 'rb') as stream:
        frames = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').astype(np.float32) / 32768.0
        return frames.reshape(-1, stream.getnchannels())


def score(job, info):
    """Higher is better: no clipping, little silence, the asked length, and for loops an even level and clean seam."""
    value = 100.0 - min(info['raw_clipped'], 400) * 0.1 - info['silence'] * 60     # clipped runs are declipped
    if job.get('duration'):
        value -= abs(info['raw_seconds'] - float(job['duration'])) / float(job['duration']) * 20
    if job['loop']:
        value -= info['level_spread_db'] * 2 + info['seam_level_db']
    elif info['onset_ms'] > 40:
        value -= min(info['onset_ms'], 400) / 20
    if job.get('score_bias') == 'power' and 'punch_before_db' in info:
        # Heavy shots: favour a take that is loud and dense by nature (its loudest 100 ms close to the peak, so it
        # needs little limiting) and has the most low end; deep limiting costs.
        value += (info['punch_before_db'] + 12) * 2 + info['low_share'] * 20 - max(0.0, info['limited_db'] - 6) * 3
    if job.get('hits') and 'hits' in info:
        value -= abs(info['hits'] - int(job['hits'])) * 30   # the brief: a twin shot that plays as one fails it
    return round(value, 1)


def note(job, info):
    parts = []
    if info['raw_clipped']:
        parts.append(f"{info['raw_clipped']} clipped samples in the download (declipped)")
    if info['silence'] > 0.3:
        parts.append(f"{int(info['silence'] * 100)} % near-silent")
    if job['loop']:
        parts.append(f"level spread {info['level_spread_db']} dB over the loop")
    else:
        parts.append(f"{info['seconds']} s after trim")
    if 'boost_db' in info:
        parts.append(f"punch {info['punch_db']} dBFS (+{info['boost_db']} dB, limited {info['limited_db']} dB), "
                     f"{int(info['low_share'] * 100)} % below 200 Hz, "
                     f"{info['hits']} hit{'s' if info['hits'] != 1 else ''}")
    centroid = info['centroid_hz']
    parts.append('dark' if centroid < 900 else 'mid' if centroid < 2500 else 'bright')
    return ', '.join(parts)


def derived_source(ws, part):
    """A derived job's part: `<job>` (that job's installed pick) or `<job>/vN.wav` (one of its variants)."""
    if '/' in part:
        return ws.root / 'out' / part
    return ws.root / 'out' / part / f"{ws.by_id[part]['output']}.wav"


def tape_pitch(audio, semitones):
    """Played back slower (lower and longer) or faster, as tape would."""
    return resample(audio, round(SAMPLE_RATE * 2.0 ** (float(semitones) / 12.0)))


def rubberband(audio, pitch_ratio=1.0, tempo=1.0, formant='shifted'):
    """ffmpeg's rubberband filter: `pitch_ratio` and `tempo` (above 1 is faster), formants `shifted` with the pitch
    or `preserved`. High pitch quality; the output is what the filter returns (its length follows the tempo)."""
    data = audio.astype('<f4').tobytes()
    options = f'pitch={pitch_ratio:.6f}:tempo={tempo:.6f}:formant={formant}:pitchq=quality:window=standard'
    result = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ac', str(audio.shape[1]),
                             '-ar', str(SAMPLE_RATE), '-i', '-', '-af', f'rubberband={options}',
                             '-f', 'f32le', '-'], input=data, capture_output=True)
    if result.returncode:
        raise SystemExit('this treatment needs ffmpeg with the rubberband filter: '
                         + result.stderr.decode('utf-8', 'replace')[:200])
    return np.frombuffer(result.stdout, dtype='<f4').reshape(-1, audio.shape[1]).copy()


def shift_pitch(audio, semitones):
    """Pitch shifted with the length kept (ffmpeg's rubberband filter), so the copy stays on the source's words."""
    data = audio.astype('<f4').tobytes()
    ratio = 2.0 ** (float(semitones) / 12.0)
    result = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ac', str(audio.shape[1]),
                             '-ar', str(SAMPLE_RATE), '-i', '-', '-af', f'rubberband=pitch={ratio:.6f}',
                             '-f', 'f32le', '-'], input=data, capture_output=True)
    if result.returncode:
        raise SystemExit('undertone needs ffmpeg with the rubberband filter: '
                         + result.stderr.decode('utf-8', 'replace')[:200])
    shifted = np.frombuffer(result.stdout, dtype='<f4').reshape(-1, audio.shape[1])
    fitted = np.zeros_like(audio)
    fitted[:min(len(audio), len(shifted))] = shifted[:len(audio)]
    return fitted


def voice_shift(audio, shift):
    """`shift: {pitch, formant, tempo}`: the voice's pitch and its formants (the size of the throat) moved
    independently, in semitones, with the length kept (divided by `tempo`, 1 by default; below 1 is slower).
    The formants move by tape (resampling moves pitch, formants and length together) and rubberband then puts the
    pitch where it is asked with the formants preserved and the length back. A formant shift down is what makes a
    voice sound larger than a person; a pitch shift alone only sounds like a lower person."""
    pitch, formant = float(shift.get('pitch', 0)), float(shift.get('formant', 0))
    tempo = float(shift.get('tempo', 1.0))
    if formant:
        audio = tape_pitch(audio, formant)                 # pitch and formants by `formant`, length * 2^(-f/12)
    if pitch != formant or formant or tempo != 1.0:
        audio = rubberband(audio, 2.0 ** ((pitch - formant) / 12.0), 2.0 ** (-formant / 12.0) * tempo,
                           'preserved')
    return audio


def add_undertone(audio, undertone):
    """`undertone: {semitones, gain_db, delay_ms}`: a pitch-shifted copy of the line (its length kept) mixed under it,
    `gain_db` down and `delay_ms` late: a second, lower throat beneath the voice. The tail grows by the delay.
    A list of such layers mixes each (a fifth and a sub-octave, or a slightly detuned double for a chorus)."""
    layers = undertone if isinstance(undertone, list) else [undertone]
    copies = []
    for layer in layers:
        copy = shift_pitch(audio, float(layer.get('semitones', -7)))
        delay = int(float(layer.get('delay_ms', 15)) / 1000.0 * SAMPLE_RATE)
        copies.append((delay, copy * 10 ** (float(layer.get('gain_db', -12)) / 20)))
    mixed = np.zeros((len(audio) + max(delay for delay, _ in copies), audio.shape[1]), dtype=np.float32)
    mixed[:len(audio)] += audio
    for delay, copy in copies:
        mixed[delay:delay + len(copy)] += copy
    return mixed


def ring_modulate(audio, ring):
    """`ring: {hz, mix}`: the voice multiplied by a low sine (30-80 Hz), blended `mix` (0-1) with the dry voice: the
    sidebands at the voice's harmonics plus and minus `hz` add an inhuman buzz that a throat cannot make."""
    t = np.arange(len(audio)) / SAMPLE_RATE
    carrier = np.sin(2.0 * math.pi * float(ring.get('hz', 50)) * t)[:, None]
    mix = float(ring.get('mix', 0.2))
    return (audio * (1.0 - mix) + audio * carrier * mix).astype(np.float32)


def add_room(audio, room):
    """`room: {seconds, mix, lowpass_hz, predelay_ms}`: a short dark room. A synthetic impulse (decaying noise, a
    fixed seed, falling 60 dB over `seconds`, low-passed at `lowpass_hz`) convolved with the voice, its level
    matched to the dry voice and mixed `mix` under it. The tail grows by the room's length."""
    from scipy.signal import butter, fftconvolve, sosfilt
    seconds = float(room.get('seconds', 0.4))
    length = int(seconds * SAMPLE_RATE)
    rng = np.random.default_rng(int(room.get('seed', 7)))
    t = np.arange(length) / SAMPLE_RATE
    impulse = rng.standard_normal(length) * np.exp(-6.9 * t / seconds)
    impulse = sosfilt(butter(2, float(room.get('lowpass_hz', 2500)), 'lowpass', fs=SAMPLE_RATE, output='sos'), impulse)
    predelay = int(float(room.get('predelay_ms', 8)) / 1000.0 * SAMPLE_RATE)
    impulse = np.concatenate([np.zeros(predelay), impulse])
    wet = np.stack([fftconvolve(audio[:, c], impulse) for c in range(audio.shape[1])], axis=1)
    dry_rms = float(np.sqrt(np.mean(audio ** 2))) or 1.0
    wet *= dry_rms / (float(np.sqrt(np.mean(wet ** 2))) or 1.0)
    mixed = np.zeros_like(wet, dtype=np.float32)
    mixed[:len(audio)] += audio
    mixed += wet * float(room.get('mix', 0.15))
    return mixed.astype(np.float32)


def saturate(audio, saturation):
    """`saturation: {drive_db, mix}`: a soft clip (tanh) of the peak-normalised signal driven `drive_db` hotter, back
    to the source's peak and blended `mix` (0-1) with the clean signal: light grit on the voice's edges."""
    peak = float(np.max(np.abs(audio))) or 1.0
    drive = 10 ** (float(saturation.get('drive_db', 6)) / 20)
    wet = np.tanh(audio / peak * drive) / math.tanh(drive) * peak
    mix = float(saturation.get('mix', 1.0))
    return (audio * (1.0 - mix) + wet * mix).astype(np.float32)


def treat(audio, job):
    """A derived one-shot's chain after the join: `shift` (pitch and formants apart, the length kept), `pitch`
    (tape), `undertone`, `ring`, `saturation`, `room`, the tone shaping
    (`highpass_hz`, `lowpass_hz`, `low_shelf`), the peak normalisation and, with `loudness_db`, the lift and limiter
    of a one-shot. Returns the audio and the loudness record."""
    if job.get('shift'):
        audio = voice_shift(audio, job['shift'])
    if job.get('pitch'):
        audio = tape_pitch(audio, job['pitch'])
    if job.get('undertone'):
        audio = add_undertone(audio, job['undertone'])
    if job.get('ring'):
        audio = ring_modulate(audio, job['ring'])
    if job.get('saturation'):
        audio = saturate(audio, job['saturation'])
    if job.get('room'):
        audio = add_room(audio, job['room'])
    audio = normalize(shape_tone(audio, job), job)
    loudness = {}
    if job.get('loudness_db') is not None:
        # Matched, not only lifted: a take whose loudest 100 ms is already above the target is turned down to it
        # (its peak then below `peak_db`), so a set of voice lines plays at one level.
        natural = punch_db(audio)
        audio, boost, reduction = make_loud(audio, job)
        excess = punch_db(audio) - float(job['loudness_db'])
        if excess > 0.5:
            audio = audio * 10 ** (-excess / 20)
            boost = round(boost - excess, 1)
        loudness = {'punch_before_db': round(natural, 1), 'boost_db': boost, 'limited_db': reduction}
    return audio, loudness


def treatment_note(job):
    parts = []
    if job.get('shift'):
        shift = job['shift']
        parts.append(f"voice pitch {float(shift.get('pitch', 0)):+g} st, formants {float(shift.get('formant', 0)):+g} st"
                     + (f", tempo {shift['tempo']}" if shift.get('tempo', 1.0) != 1.0 else ''))
    if job.get('pitch'):
        parts.append(f"pitched {job['pitch']:+} semitones")
    if job.get('undertone'):
        layers = job['undertone'] if isinstance(job['undertone'], list) else [job['undertone']]
        parts.append('undertone ' + ' + '.join(f"{float(u.get('semitones', -7)):+g} st at {u.get('gain_db', -12)} dB"
                                                for u in layers) + f", {layers[0].get('delay_ms', 15)} ms late")
    if job.get('ring'):
        parts.append(f"ring {job['ring'].get('hz', 50)} Hz at {job['ring'].get('mix', 0.2)}")
    if job.get('saturation'):
        parts.append(f"drive {job['saturation'].get('drive_db', 6)} dB, mix {job['saturation'].get('mix', 1.0)}")
    if job.get('room'):
        room = job['room']
        parts.append(f"room {room.get('seconds', 0.4)} s at {room.get('mix', 0.15)}, dark {room.get('lowpass_hz', 2500)} Hz")
    if job.get('highpass_hz') or job.get('lowpass_hz'):
        parts.append(f"band {job.get('highpass_hz', 0)}-{job.get('lowpass_hz', 'open')} Hz")
    return ', '.join(parts)


def process_job(ws, job):
    out = ws.root / 'out' / job['id']
    out.mkdir(parents=True, exist_ok=True)
    variants = []
    if job['kind'] == 'derived' and job.get('each'):
        # One treated variant per variant of the source job (a voice line's takes): the pick is made here,
        # on what the game plays, and the source job's own pick does not matter.
        # Several source jobs (the same line in two deliveries) number their takes on: v1-v3, then v4-v6.
        for source_id in job['from']:
            for entry in ws.picks.get(source_id, {}).get('variants', []):
                audio, loudness = treat(read_wav(ws.root / 'out' / source_id / entry['file']), job)
                name = f'v{len(variants) + 1}.wav'
                write_wav(out / name, audio)
                info = {**metrics(audio, False), 'raw_seconds': round(len(audio) / SAMPLE_RATE, 3),
                        'raw_clipped': 0, 'punch_db': round(punch_db(audio), 1), **loudness}
                variants.append({'file': name, **info, 'score': 100.0,
                                 'note': f"take {entry['file']} of {source_id}, {treatment_note(job)}"
                                         + (f", punch {info['punch_db']} dBFS ({loudness['boost_db']:+} dB, limited "
                                            f"{loudness['limited_db']} dB)" if loudness else '')})
    elif job['kind'] == 'derived':
        parts = [read_wav(derived_source(ws, part)) for part in job['from']]
        if job['loop']:
            # A longer bed: the parts joined by equal-power crossfades, then the wrap made seamless.
            fade = int(float(job.get('crossfade', 0.5)) * SAMPLE_RATE)
            t = np.linspace(0.0, 1.0, fade)[:, None]
            audio = parts[0]
            for part in parts[1:]:
                overlap = audio[-fade:] * np.cos(t * math.pi / 2) + part[:fade] * np.sin(t * math.pi / 2)
                audio = np.concatenate([audio[:-fade], overlap, part[fade:]])
            audio = normalize(make_seamless(audio, float(job.get('crossfade', 0.5))), job)
        else:
            gap = np.zeros((int(float(job.get('gap', 0.0)) * SAMPLE_RATE), parts[0].shape[1]), dtype=np.float32)
            joined = []
            for index, part in enumerate(parts):
                joined.append(part)
                if index + 1 < len(parts) and len(gap):
                    joined.append(gap)
            # A tier's variant of a family sound is the pitch alone; a voice line also takes the rest of treat().
            audio, loudness = treat(np.concatenate(joined), job)
        write_wav(out / 'v1.wav', audio)
        info = {**metrics(audio, job['loop']), 'raw_seconds': round(len(audio) / SAMPLE_RATE, 3), 'raw_clipped': 0}
        if not job['loop']:
            info.update({'punch_db': round(punch_db(audio), 1), **loudness})
        treatment = '' if job['loop'] else treatment_note(job)
        source = ' + '.join(job['from']) + (f', {treatment}' if treatment else '')
        variants.append({'file': 'v1.wav', **info, 'score': 100.0, 'note': 'joined from ' + source})
    elif job['kind'] == 'voice_design':
        # The previews of each request, as p1.wav... (several requests number on), with their generated ids: the
        # one saved as a voice (create-voice) is recorded under the job as `voice_id`.
        for record in raw_paths(ws, job):
            if record is None:
                continue
            for preview in json.loads(record.read_text())['previews']:
                audio = normalize(decode(record.parent / preview['file']).mean(axis=1, keepdims=True), job)
                name = f'p{len(variants) + 1}.wav'
                write_wav(out / name, audio)
                info = {**metrics(audio, False), 'raw_seconds': round(len(audio) / SAMPLE_RATE, 3), 'raw_clipped': 0}
                variants.append({'file': name, **info, 'score': 100.0,
                                 'generated_voice_id': preview['generated_voice_id'],
                                 'note': f"preview {preview['preview']} of {record.name}"})
    else:
        master = job.get('master', 'flac' if job['kind'] == 'music' else 'wav')
        for index, path in enumerate(raw_paths(ws, job), start=1):
            if path is None:
                continue
            raw = decode(path)
            if job['kind'] == 'music':
                raw_info = music_metrics(raw)
                repaired = declip(raw) if raw_info['clipped'] else raw
                cut = 0.0
                if job['loop']:
                    repaired, cut = cut_fade_out(repaired)
                    if cut:
                        raw_info['tail_db'] = music_metrics(repaired)['tail_db']
                audio = make_seamless(repaired, float(job.get('crossfade', 4.0))) if job['loop'] else repaired
                audio = normalize(audio, job)
                write_audio(out / f'v{index}.{master}', audio)
                info = {**music_metrics(audio), 'raw_seconds': raw_info['seconds'],
                        'raw_clipped': raw_info['clipped'], 'raw_peak_db': raw_info['peak_db'],
                        'raw_head_db': raw_info['head_db'], 'raw_tail_db': raw_info['tail_db'],
                        **({'fade_cut_s': cut} if cut else {})}
                info['score'] = music_score(job, info)
                info['note'] = music_note(info)
                variants.append({'file': f'v{index}.{master}', **info})
                continue
            if job['channels'] == 1 and raw.shape[1] > 1:
                raw = raw.mean(axis=1, keepdims=True)
            raw_info = metrics(raw, job['loop'])
            repaired = declip(raw) if raw_info['clipped'] else raw
            audio = (make_seamless(repaired, float(job.get('crossfade', 0.25))) if job['loop']
                     else trim_one_shot(shape_tone(repaired, job)))
            audio = normalize(audio, job)
            loudness = {}
            hits = None if job['loop'] else count_hits(audio)     # counted before any limiting flattens the dips
            if not job['loop'] and job.get('loudness_db') is not None:
                natural = punch_db(audio)
                audio, boost, reduction = make_loud(audio, job)
                loudness = {'punch_before_db': round(natural, 1), 'boost_db': boost, 'limited_db': reduction}
            write_wav(out / f'v{index}.wav', audio)
            info = {**metrics(audio, job['loop']), 'raw_seconds': raw_info['seconds'],
                    'raw_clipped': raw_info['clipped'], 'raw_peak_db': raw_info['peak_db']}
            if not job['loop']:
                info['onset_ms'] = raw_info['onset_ms']
                info['punch_db'] = round(punch_db(audio), 1)
                info['low_share'] = round(low_share(audio), 3)
                info['hits'] = hits
                info.update(loudness)
            info['score'] = score(job, info)
            info['note'] = note(job, info)
            variants.append({'file': f'v{index}.wav', **info})
    if not variants:
        return None
    if job['kind'] == 'voice_design':
        entry = ws.picks.get(job['id'], {})
        keep = {k: entry[k] for k in ('voice_id', 'voice_name', 'created', 'choice') if k in entry}
        ws.picks[job['id']] = {**keep, 'picked': entry.get('choice', variants[0]['file']), 'output': job['output'],
                               'listening': entry.get('listening', ''), 'variants': variants}
        (out / 'prompt.txt').write_text(job['prompt'] + '\n\npreview text: ' + job['text'] + '\n')
        return ws.picks[job['id']]['picked']
    (out / 'prompt.txt').write_text(
        (job.get('prompt') or f"derived: {' + '.join(job['from'])}") + '\n\n'
        + yaml.safe_dump({k: job[k] for k in ('kind', 'duration', 'loop', 'variants', 'model', 'prompt_influence',
                                              'instrumental', 'voice_id', 'voice_settings', 'pitch', 'undertone',
                                              'saturation', 'shift', 'ring', 'room', 'highpass_hz', 'lowpass_hz',
                                              'low_shelf', 'loudness_db',
                                              'score_bias', 'line')
                          if k in job}, sort_keys=False))
    entry = ws.picks.get(job['id'], {})
    automatic = max(variants, key=lambda v: v['score'])['file']
    choice = entry.get('choice') if entry.get('choice') in [v['file'] for v in variants] else None
    picked = choice or automatic
    installed = out / f"{job['output']}{Path(picked).suffix}"
    shutil.copyfile(out / picked, installed)
    if job.get('mp3', job['kind'] == 'music'):
        encode_mp3(installed, out / f"{job['output']}.mp3")
    ws.picks[job['id']] = {**({'choice': choice} if choice else {}), 'auto': automatic, 'picked': picked,
                           'output': job['output'], 'listening': entry.get('listening', ''),
                           'variants': variants}
    return picked


def cmd_process(ws, ids):
    for job in ws.select(ids):
        if job['kind'] == 'derived' and any(not derived_source(ws, part).exists() for part in job['from']):
            continue
        picked = process_job(ws, job)
        if picked:
            print(f"{job['id']:<24} -> {picked}")
    write_picks(ws)


def write_picks(ws):
    header = ('# Generated by tools/audio/elevenlabs_gen.py process: per job the automatic pick (`auto`, by the\n'
              '# objective score), the installed `picked` file and each variant\'s metrics. Write `choice: vN.wav`\n'
              '# under a job to override the pick and `listening:` for a note; both survive reprocessing.\n')
    ws.picks_path.write_text(header + yaml.safe_dump(ws.picks, sort_keys=False, width=120))


def cmd_create_voice(ws, ids):
    """`create-voice <jobs> <design id> pN`: save preview N of a voice_design job as a voice of the account
    (POST /v1/text-to-voice, free) and record its id under the job in picks.yml (`voice_id`, `choice`) and in the
    ledger (0 credits). The TTS jobs then name that `voice_id`."""
    if len(ids) != 2:
        raise SystemExit('create-voice needs a voice_design job id and a preview (pN)')
    job_id, preview = ids
    job = ws.by_id.get(job_id)
    if not job or job['kind'] != 'voice_design':
        raise SystemExit(f'{job_id} is not a voice_design job')
    entry = ws.picks.get(job_id)
    if not entry:
        raise SystemExit(f'{job_id}: run process first')
    if entry.get('voice_id'):
        raise SystemExit(f"{job_id} already has the voice {entry['voice_id']} ({entry.get('choice')})")
    variant = next((v for v in entry['variants'] if v['file'] == f'{preview}.wav'), None)
    if variant is None:
        raise SystemExit(f'{job_id} has no preview {preview}')
    name = job.get('voice_name', job_id)
    body = {'voice_name': name, 'voice_description': job['prompt'][:1000],
            'generated_voice_id': variant['generated_voice_id'],
            'labels': {'project': 'openyamm', 'job': job_id},
            'played_not_selected_voice_ids': [v['generated_voice_id'] for v in entry['variants'] if v is not variant]}
    try:
        data, headers = post_json('/v1/text-to-voice', body, api_key())
    except urllib.error.HTTPError as error:
        raise SystemExit(f'{job_id}: HTTP {error.code}: {error.read().decode("utf-8", "replace")[:400]}')
    entry.update({'choice': variant['file'], 'picked': variant['file'], 'voice_id': data['voice_id'],
                  'voice_name': name, 'created': now()})
    ws.ledger['requests'].append({'job': job_id, 'kind': 'voice_create', 'variant': int(preview.lstrip('p')),
                                  'time': now(), 'credits': 0, 'credits_source': 'free', 'estimate': 0,
                                  'voice_id': data['voice_id'], 'voice_name': name,
                                  'generated_voice_id': variant['generated_voice_id']})
    ws.save_ledger()
    write_picks(ws)
    print(f"{job_id} {preview} -> voice {data['voice_id']} ({name})")


# --- Review page ----------------------------------------------------------------------------------------------------
REVIEW_STYLE = """
:root { --bg: #f6f5f2; --card: #ffffff; --ink: #1d1d1b; --muted: #6b6a66; --line: #e2e0da; --pick: #2f6f4f;
  --redo: #9a4a12; }
@media (prefers-color-scheme: dark) { :root { --bg: #161615; --card: #20201e; --ink: #ecebe6; --muted: #a09e97;
  --line: #34332f; --pick: #6fcf97; --redo: #f0a36b; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 system-ui, sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 22px; margin: 0 0 4px; } h2 { font-size: 17px; margin: 32px 0 8px; }
p.lede { color: var(--muted); margin: 0 0 16px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px;
  margin: 10px 0; }
.card header { display: flex; flex-wrap: wrap; gap: 8px; align-items: baseline; }
.card code { font-size: 13px; } .tag { color: var(--muted); font-size: 13px; }
.prompt { color: var(--muted); font-size: 13px; margin: 6px 0 8px; }
.variants { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 8px; }
.variant { border: 1px solid var(--line); border-radius: 6px; padding: 6px 8px; }
.variant.picked { border-color: var(--pick); box-shadow: inset 3px 0 0 var(--pick); }
.variant .meta { font-size: 12px; color: var(--muted); }
.variant.before { border-style: dashed; }
.redone { font-size: 12px; font-weight: 600; color: var(--redo); border: 1px solid var(--redo); border-radius: 4px;
  padding: 0 5px; }
.feedback { font-size: 13px; margin: 6px 0 0; color: var(--ink); }
.line { font-size: 15px; font-weight: 600; margin: 6px 0 0; }
audio { width: 100%; height: 34px; }
.cast-line { margin: 12px 0 4px; }
.cast-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; }
.cast-col { border: 1px solid var(--line); border-radius: 6px; padding: 6px 8px; min-width: 0; }
.cast-col.current { border-style: dashed; }
.cast-col h4 { margin: 0 0 4px; font-size: 14px; }
.cast-col .meta, .voice .meta { font-size: 12px; color: var(--muted); overflow-wrap: anywhere; }
.voices { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 8px; margin: 6px 0; }
.voice { font-size: 13px; border-left: 3px solid var(--line); padding: 2px 8px; }
details { margin-top: 8px; } summary { cursor: pointer; color: var(--muted); font-size: 13px; }
.suggested { color: var(--pick); font-weight: 600; }
"""


def casting_section(ws, title, jobs):
    """The review page's casting section: per boss, each voiced line with the installed clip and the candidates'
    treated takes side by side (the suggested take first), each candidate's voice description and treatment, and
    the untreated reads and the design previews collapsed. Jobs carry `cast: {boss, candidate, current, design}`;
    the group's jobs without one (a pilot) are listed collapsed at the end."""
    bosses = {}
    for job in jobs:
        if job.get('cast'):
            bosses.setdefault(job['cast']['boss'], []).append(job)
    audio = lambda path, label, meta='': (f'<div class="meta">{label}{(" &middot; " + html.escape(meta)) if meta else ""}'
                                          f'</div><audio controls preload="none" src="{path}"></audio>')
    body = [f'<h2>{html.escape(title)}</h2>',
            '<p class="lede">Round 2 after "more demonic" and "the bosses all sound the same": every speaking boss has two '
            'designed voices of its own (A and B, ElevenLabs Voice Design), each line read twice with eleven_v3 and '
            'given the boss\'s treatment (the same for A and B). Per line: the clip installed now (dashed), then A '
            'and B, the suggested take first (the first that both Whisper models read). Nothing here is installed. '
            'To choose, tell the integrator the boss, the candidate and the take.</p>']
    for boss, items in bosses.items():
        designs = {j['cast']['candidate']: j for j in items if j['kind'] == 'voice_design'}
        treated = [j for j in items if j['kind'] == 'derived']
        untreated = [j for j in items if j['kind'] == 'tts']
        body.append(f'<section class="card"><header><strong>{html.escape(boss)}</strong></header><div class="voices">')
        for candidate, design in sorted(designs.items()):
            entry = ws.picks.get(design['id'], {})
            body.append(f'<div class="voice"><strong>{candidate}</strong> {html.escape(design["prompt"])}'
                        f'<div class="meta">voice {html.escape(str(entry.get("voice_id", "not saved")))} '
                        f'(preview {html.escape(str(entry.get("choice", "-"))[:2])} of {design["id"]})</div></div>')
        body.append('</div>')
        lines = {}
        for job in treated:
            lines.setdefault(job['cast']['current'], {})[job['cast']['candidate']] = job
        for current, by_candidate in lines.items():
            first = next(iter(by_candidate.values()))
            body.append(f'<p class="line cast-line">{html.escape(first.get("line", ""))}</p><div class="cast-grid">')
            installed = ws.by_id.get(current)
            if installed:
                body.append('<div class="cast-col current"><h4>Installed now</h4>'
                            + audio(f'../out/{current}/{installed["output"]}.wav', f'<code>{current}.wav</code>')
                            + '</div>')
            for candidate, job in sorted(by_candidate.items()):
                entry = ws.picks.get(job['id'], {})
                variants = sorted(entry.get('variants', []), key=lambda v: v['file'] != entry.get('picked'))
                body.append(f'<div class="cast-col"><h4>{candidate}</h4><div class="meta">{html.escape(treatment_note(job))}'
                            '</div>')
                for variant in variants:
                    label = (f'<span class="suggested">{variant["file"]} suggested</span>'
                             if variant['file'] == entry.get('picked') else variant['file'])
                    body.append(audio(f'../out/{job["id"]}/{variant["file"]}', label, f'{variant["seconds"]} s'))
                body.append('</div>')
            body.append('</div>')
            notes = [ws.picks.get(job['id'], {}).get('listening') for _, job in sorted(by_candidate.items())]
            body.append(''.join(f'<p class="prompt">{c}: {html.escape(n)}</p>'
                                for c, n in zip(sorted(by_candidate), notes) if n))
        body.append('<details><summary>Untreated reads and the voice design previews</summary><div class="variants">')
        for job in untreated:
            for variant in ws.picks.get(job['id'], {}).get('variants', []):
                body.append('<div class="variant">' + audio(f'../out/{job["id"]}/{variant["file"]}',
                            f'{job["cast"]["candidate"]} untreated {variant["file"]}', job['prompt']) + '</div>')
        for candidate, design in sorted(designs.items()):
            entry = ws.picks.get(design['id'], {})
            for variant in entry.get('variants', []):
                saved = ' (saved as the voice)' if variant['file'] == entry.get('choice') else ''
                body.append('<div class="variant">' + audio(f'../out/{design["id"]}/{variant["file"]}',
                            f'{candidate} design preview {variant["file"]}{saved}') + '</div>')
        body.append('</div></details></section>')
    others = [job for job in jobs if not job.get('cast') and ws.picks.get(job['id'])]
    if others:
        body.append('<details><summary>Pilot takes</summary><div class="variants">')
        for job in others:
            for variant in ws.picks[job['id']]['variants']:
                body.append('<div class="variant">' + audio(f'../out/{job["id"]}/{variant["file"]}',
                            f'{html.escape(job["id"])} {variant["file"]}', job.get('use', '')) + '</div>')
        body.append('</div></details>')
    return body


def cmd_review(ws):
    review = ws.root / 'review'
    review.mkdir(exist_ok=True)
    groups = {}
    for job in ws.jobs:
        groups.setdefault(job.get('group', 'other'), []).append(job)
    body = []
    for group, jobs in groups.items():
        if any(job.get('cast') for job in jobs):
            body.extend(casting_section(ws, group, jobs))
            continue
        body.append(f'<h2>{html.escape(group)}</h2>')
        for job in jobs:
            entry = ws.picks.get(job['id'])
            if not entry:
                continue
            loop = ' <span class="tag">loop</span>' if job['loop'] else ''
            redone = job.get('redone') or {}
            badge = ' <span class="redone">redone after feedback</span>' if redone else ''
            body.append('<section class="card"><header>'
                        f"<strong>{html.escape(job.get('title', job['id']))}</strong>"
                        f"<code>{html.escape(job['output'])}.wav</code>{loop}{badge}"
                        f"<span class=\"tag\">{html.escape(job.get('use', ''))}</span></header>"
                        + (f"<p class=\"feedback\">{html.escape(redone['note'])}</p>" if redone.get('note') else '')
                        + (f"<p class=\"line\">{html.escape(job['line'])}</p>" if job.get('line') else '')
                        + f"<div class=\"prompt\">{html.escape(job.get('prompt') or 'joined: ' + ' + '.join(job.get('from', [])))}</div>"
                        '<div class="variants">')
            if redone.get('before'):
                body.append(f'<div class="variant before"><div class="meta"><strong>before feedback</strong> '
                            f'&middot; the take installed before the redo, for comparison</div><audio controls '
                            f'preload="none" src="../out/{job["id"]}/{redone["before"]}"></audio></div>')
            for variant in entry['variants']:
                picked = ' picked' if variant['file'] == entry['picked'] else ''
                label = 'installed' if picked else ''
                loop_attr = ' loop' if job['loop'] else ''
                body.append(f'<div class="variant{picked}"><div class="meta"><strong>{variant["file"]}</strong> '
                            f'{label} &middot; score {variant["score"]} &middot; {html.escape(variant["note"])}'
                            f'</div><audio controls preload="none"{loop_attr} '
                            f'src="../out/{job["id"]}/{variant["file"]}"></audio></div>')
            listening = entry.get('listening')
            body.append('</div>' + (f'<p class="prompt">Listening: {html.escape(listening)}</p>' if listening else '')
                        + '</section>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Hesper Audio Review</title><style>{REVIEW_STYLE}</style></head><body><main>'
            '<h1>Hesper audio, batch review</h1>'
            f'<p class="lede">Generated with ElevenLabs sound effects, music and speech. The outlined variant is the '
            f'one installed (the automatic pick by an objective score: clipping, silence, length, loop evenness; for '
            f'the heavy shots also loudness and low end; the voice lines are picked by hand, the reason under each). '
            f'To choose another, '
            f'write <code>choice: vN.wav</code> under the job in <code>picks.yml</code> and rerun process and the '
            f'stage. Credits charged: {ws.spent()} (cap {ws.budget}).</p>'
            + '\n'.join(body) + '</main></body></html>\n')
    (review / 'index.html').write_text(page)
    print(review / 'index.html')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('plan', 'run', 'process', 'review', 'create-voice'))
    parser.add_argument('jobs', type=Path)
    parser.add_argument('ids', nargs='*')
    parser.add_argument('--dry-run', action='store_true', help='run: list the requests without sending them')
    args = parser.parse_args()
    ws = Workspace(args.jobs)
    if args.command == 'plan':
        cmd_plan(ws, args.ids)
    elif args.command == 'run':
        cmd_run(ws, args.ids, args.dry_run)
    elif args.command == 'process':
        cmd_process(ws, args.ids)
    elif args.command == 'create-voice':
        cmd_create_voice(ws, args.ids)
    else:
        cmd_review(ws)


if __name__ == '__main__':
    sys.exit(main())
