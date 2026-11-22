#!/usr/bin/env python3
"""Read voice takes with two local Whisper models and say which ones both read (lane AU, D-38).

    work/venv/bin/python whisper_check.py <job> [<job> ...]        # every out/<job>/vN.wav (or pN.wav)
    work/venv/bin/python whisper_check.py --text "..." <file.wav>  # one file against a given text

The expected text is the job's `line` (the part after "Speaker: "), else its `prompt` with audio tags ([...]) removed.
The rule (as Hesper's boss lines, design/kreegan_world/audio/BOSS_LINES.md): faster-whisper small.en must read the
words exactly and base.en at most one word off, after lower-casing, dropping punctuation and treating the world's
names leniently (`NAMES`: a name may be heard as any one or two words). A take passes only if both do.
The models come from the local Hugging Face cache (Systran/faster-whisper-small.en, -base.en), run on the CPU with
int8 and two threads.
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import yaml
from faster_whisper import WhisperModel
from scipy.io import wavfile
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
NAMES = {'xeen', 'sheltem', 'corak', 'soulbox'}
NUMBERS = {'6th': 'sixth'}


def words(text):
    text = re.sub(r'\[[^\]]*\]|\([^)]*\)', ' ', text.lower())
    text = text.replace('soul box', 'soulbox').replace("'s", 's')
    result = [w for w in re.sub(r"[^a-z0-9 ]+", ' ', text).split()]
    return [NUMBERS.get(w, w) for w in result]


def errors(expected, heard):
    """Word errors, a name heard as one or two other words counting as none."""
    matcher = SequenceMatcher(a=expected, b=heard, autojunk=False)
    count = 0
    for op, a0, a1, b0, b1 in matcher.get_opcodes():
        if op == 'equal':
            continue
        span = expected[a0:a1]
        if op == 'replace' and all(w in NAMES for w in span) and (b1 - b0) <= 2 * len(span):
            continue
        if op == 'replace' and span == ['a'] and heard[b0:b1] in (['ah'], ['uh']):
            continue            # the article spoken full ("ah"): the same sound, written differently
        count += max(a1 - a0, b1 - b0)
    return count


def load(path):
    """The take as 16 kHz mono float (decoded here: the venv's PyAV does not take faster-whisper's options)."""
    rate, data = wavfile.read(path)
    audio = data.astype(np.float32) / (32768.0 if data.dtype == np.int16 else 1.0)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return resample_poly(audio, 16000, rate).astype(np.float32) if rate != 16000 else audio


def expected_text(job):
    line = job.get('line')
    if line:
        return line.split(': ', 1)[1] if ': ' in line else line
    return job.get('prompt', '')


def main():
    args = sys.argv[1:]
    models = {name: WhisperModel(name, device='cpu', compute_type='int8', cpu_threads=2)
              for name in ('small.en', 'base.en')}
    checks = []
    if args and args[0] == '--text':
        checks.append((args[1], [Path(a) for a in args[2:]]))
    else:
        jobs = {job['id']: job for job in yaml.safe_load((HERE / 'jobs.yml').read_text())['jobs']}
        for job_id in args:
            job = jobs[job_id]
            source = job
            if job.get('kind') == 'derived':
                source = jobs[job['from'][0]]
            files = sorted((HERE / 'out' / job_id).glob('v[0-9]*.wav')) or sorted((HERE / 'out' / job_id).glob('p*.wav'))
            text = expected_text(job if job.get('line') else source) if job.get('kind') != 'voice_design' else job['text']
            checks.append((text, files))
    for text, files in checks:
        expected = words(text)
        print(f'== {text}')
        for path in files:
            heard, verdict = {}, {}
            audio = load(path)
            for name, model in models.items():
                segments, _ = model.transcribe(audio, language='en', beam_size=5)
                heard[name] = ' '.join(s.text.strip() for s in segments)
                verdict[name] = errors(expected, words(heard[name]))
            passed = verdict['small.en'] == 0 and verdict['base.en'] <= 1
            print(f"  {path.parent.name}/{path.name}: {'PASS' if passed else 'fail'} "
                  f"(small.en {verdict['small.en']}, base.en {verdict['base.en']})")
            for name in models:
                print(f'      {name:<8} {heard[name]}')


if __name__ == '__main__':
    main()
