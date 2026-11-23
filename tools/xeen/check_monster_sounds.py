#!/usr/bin/env python3
"""Measure every Xeen monster row's four sounds against what MM6-MM8's own monster sounds are like.

Each Xeen descriptor (data_tables/monster_descriptors.txt, ids 11000-11999) names four sounds: attack, death, wince
(got hit) and aware (the idle fidget). Each id resolves through the world's sounds table
(worlds/xeen/audio/sounds.txt, the AU lane's WAVs) or the engine's (engine/data_tables/sounds.txt, MM6-MM8 WAVs).
The files are decoded with ffmpeg at their own rate and measured; the bounds come from the same measurements over
every sound the MM6-MM8 descriptors (engine/data_tables/monster_descriptors.txt) use, so "normal" is what the shipped
monsters sound like, not a number picked by ear.

Faults (each an error, exit 1):
  missing   the id has no sounds row, or the row's file is not on disk (id 0 is "no sound", as on 309 MM6-MM8
            descriptor slots: peaceful characters)
  clipped   a run of 3 or more samples at full scale
  hiss      static with no body: under 10 % of the energy below 2.5 kHz, a noise-like spectrum (flatness over 0.05)
            and a centroid over 5.5 kHz (feedback F37: the swarms' and Doom Bug's ElevenLabs takes were hiss at
            7-11 kHz with nothing under 600 Hz, where every MM6-MM8 insect buzzes at 100-600 Hz; a tonal chirp is
            not hiss). Of the 645 MM6-MM8 monster sound files only 5 have under 10 % body and 3 meet the whole rule
            (9 descriptor slots, `--reference` hiss_in_reference): the serpentmen's attack and wince and the
            hydra's move, reptiles hissing on purpose
  loud      active level (RMS of the 50 ms windows within 20 dB of the loudest) above the MM6-MM8 maximum + 1 dB
  quiet     active level under the MM6-MM8 1st percentile - 3 dB
  long      longer than the MM6-MM8 maximum for its slot + 0.5 s (not on bosses: source/monsters.yml `bosses`, whose
            death cries are made long on purpose)
  short     shorter than 0.12 s
  cut       a one-shot (attack, death, wince) whose last 20 ms are within 6 dB of its active level: it stops mid-sound
            and clicks (the MM6-MM8 sounds all fade; a fidget may stop, the engine does not loop it)
  dc        a DC offset over 2 % of full scale (the file's mean and its quietest 50 ms window's mean both:
            a low thump that settles to zero is not one)

Rows sharing one sound are measured once. Engine sounds (MM6-MM8 stand-ins) are measured too, but only `missing` is
an error for them: they are the reference.

    python3 tools/xeen/check_monster_sounds.py             # errors only, exit 1 on any
    python3 tools/xeen/check_monster_sounds.py --all       # every Xeen sound with its numbers
    python3 tools/xeen/check_monster_sounds.py --reference # the MM6-MM8 bounds per slot
    python3 tools/xeen/check_monster_sounds.py --assets <root>  # another asset root
"""

from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import subprocess
import sys

import numpy as np
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets_dev'
XEEN = ASSETS / 'worlds' / 'xeen'


def set_assets(root):
    global ASSETS, XEEN
    ASSETS = pathlib.Path(root).resolve()
    XEEN = ASSETS / 'worlds' / 'xeen'
SLOTS = ('attack', 'death', 'wince', 'aware')
ONE_SHOTS = ('attack', 'death', 'wince')
XEEN_IDS = range(11000, 12000)

HISS_BODY_SHARE = 0.10   # energy share below 2.5 kHz
HISS_FLATNESS = 0.05      # spectral flatness: noise, not a voice, buzz or chirp
HISS_CENTROID = 5500.0
CUT_DB = 6.0
DC_LIMIT = 0.02
SHORT_SECONDS = 0.12


def boss_ids():
    data = yaml.safe_load((XEEN / 'source' / 'monsters.yml').read_text(encoding='utf-8'))
    ids = set()
    for family in (data.get('families') or {}).values():
        for boss in family.get('bosses') or []:
            if isinstance(boss, dict) and 'id' in boss:
                ids.add(int(boss['id']))
    return ids


def table_rows(path):
    rows = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if not line.strip() or line.startswith(('/', '#')):
            continue
        rows.append(line.split('\t'))
    return rows


def descriptors(path, ids=None):
    """id -> (name, [attack, death, wince, aware])"""
    out = {}
    for row in table_rows(path):
        if len(row) < 11 or not row[0].strip().isdigit():
            continue
        rid = int(row[0])
        if ids is not None and rid not in ids:
            continue
        sounds = [int(c) if c.strip().isdigit() else 0 for c in row[7:11]]
        out[rid] = (row[1], sounds)
    return out


def sound_files():
    """sound id -> (name, file or None, origin)"""
    index = {}
    folders = {
        'engine': [ASSETS / 'engine' / 'audio'],
        'xeen': [XEEN / 'audio' / 'xeen', XEEN / 'audio'],
    }
    listings = {origin: {p.name.lower(): p for d in dirs if d.is_dir() for p in d.iterdir()}
                for origin, dirs in folders.items()}
    for origin, table in (('engine', ASSETS / 'engine' / 'data_tables' / 'sounds.txt'),
                          ('xeen', XEEN / 'audio' / 'sounds.txt')):
        for row in table_rows(table):
            if len(row) < 2 or not row[1].strip().isdigit():
                continue
            name = row[0].strip()
            found = listings[origin].get((name + '.wav').lower())
            if found is None and origin == 'xeen':
                found = listings['engine'].get((name + '.wav').lower())
            index[int(row[1])] = (name, found, origin)
    return index


def decode(path):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
                            'stream=sample_rate,channels', '-of', 'csv=p=0', str(path)],
                           capture_output=True, text=True, check=True).stdout.strip().split(',')
    rate, channels = int(probe[0]), int(probe[1])
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, channels)
    return x, rate, channels


def db(v):
    return 20.0 * np.log10(max(float(v), 1e-12))


def flatness(mono, rate, n=2048):
    """Median spectral flatness (geometric over arithmetic mean of the power, 500 Hz-10 kHz, the band every MM6-MM8
    file at 22 kHz still has) over the frames within 30 dB of the loudest: near 0 for a voice, a buzz or a chirp,
    0.1-0.4 for static."""
    freq = np.fft.rfftfreq(n, 1.0 / rate)
    band = (freq >= 500) & (freq <= 10000)
    window = np.hanning(n)
    values, energies = [], []
    for i in range(0, max(0, len(mono) - n), n // 2):
        power = np.abs(np.fft.rfft(mono[i:i + n] * window)) ** 2
        b = power[band] + 1e-20
        energies.append(b.sum())
        values.append(float(np.exp(np.mean(np.log(b))) / np.mean(b)))
    if not values:
        return 0.0
    energies = np.array(energies)
    return float(np.median(np.array(values)[energies >= energies.max() * 1e-3]))


def measure(path):
    x, rate, channels = decode(path)
    full = np.abs(x).max(axis=1) >= 0.999
    clip_run = 0
    run = 0
    for v in full:
        run = run + 1 if v else 0
        clip_run = max(clip_run, run)
    mono = x.mean(axis=1)
    n = len(mono)
    seconds = n / rate
    win = max(1, int(0.05 * rate))
    frames = [mono[i:i + win] for i in range(0, max(1, n - win + 1), win)] or [mono]
    # An offset shifts every window, the quietest too; a low thump leaves the quietest window near zero.
    quietest = min(frames, key=lambda f: float(np.sqrt(np.mean(f ** 2))) if len(f) else 1.0)
    dc = min(abs(float(mono.mean())), abs(float(quietest.mean()))) if n else 0.0
    levels = np.array([db(np.sqrt(np.mean(f ** 2))) if len(f) else -240.0 for f in frames])
    loudest = levels.max()
    active = levels[levels >= loudest - 20.0]
    active_db = db(np.sqrt(np.mean(10 ** (active / 10.0)))) if len(active) else -240.0
    tail = mono[-max(1, int(0.02 * rate)):]
    tail_db = db(np.sqrt(np.mean(tail ** 2)))
    spec = np.abs(np.fft.rfft(mono * np.hanning(n))) ** 2 if n > 16 else np.zeros(2)
    freq = np.fft.rfftfreq(max(n, 2), 1.0 / rate)[:len(spec)]
    total = float(spec.sum()) or 1e-12
    centroid = float((spec * freq).sum() / total)
    body = float(spec[freq < 2500].sum() / total)
    return {
        'flatness': flatness(mono, rate),
        'seconds': seconds, 'rate': rate, 'channels': channels, 'peak_db': db(np.abs(x).max() if n else 0),
        'clip_run': clip_run, 'active_db': active_db, 'tail_db': tail_db, 'centroid': centroid, 'body': body,
        'dc': dc,
    }


def measure_all(paths):
    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(measure, p): p for p in paths}
        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            try:
                out[path] = future.result()
            except (subprocess.CalledProcessError, ValueError, IndexError) as error:
                out[path] = {'error': str(error)}
    return out


def reference_bounds(index, measured):
    per_slot = {slot: [] for slot in SLOTS}
    for _rid, (_name, sounds) in descriptors(ASSETS / 'engine' / 'data_tables' / 'monster_descriptors.txt').items():
        for slot, sid in zip(SLOTS, sounds):
            entry = index.get(sid)
            if entry and entry[1] is not None and 'error' not in measured.get(entry[1], {'error': 1}):
                per_slot[slot].append(measured[entry[1]])
    bounds = {}
    every = [m for slot in SLOTS for m in per_slot[slot]]
    levels = np.array([m['active_db'] for m in every])
    for slot in SLOTS:
        lengths = np.array([m['seconds'] for m in per_slot[slot]])
        bounds[slot] = {
            'count': len(lengths),
            'max_seconds': float(lengths.max()),
            'p99_seconds': float(np.percentile(lengths, 99)),
        }
    bounds['level'] = {'max': float(levels.max()), 'p01': float(np.percentile(levels, 1)),
                       'median': float(np.median(levels))}
    flat = np.array([m['flatness'] for m in every])
    bounds['flatness'] = {'max': float(flat.max()), 'p99': float(np.percentile(flat, 99)),
                          'median': float(np.median(flat))}
    hiss = [m for m in every if is_hiss(m)]
    bounds['hiss_in_reference'] = len(hiss)
    if ONE_SHOTS:
        shots = [m for slot in ONE_SHOTS for m in per_slot[slot]]
        cut = [m for m in shots if m['tail_db'] > m['active_db'] - CUT_DB]
        bounds['cut_in_reference'] = (len(cut), len(shots))
    return bounds


def is_hiss(m):
    return m['body'] < HISS_BODY_SHARE and m['flatness'] > HISS_FLATNESS and m['centroid'] > HISS_CENTROID


def faults(slot, m, bounds, origin, boss):
    if 'error' in m:
        return ['missing (undecodable: %s)' % m['error'][:60]]
    if origin != 'xeen':
        return []
    found = []
    if m['clip_run'] >= 3:
        found.append('clipped (%d samples at full scale)' % m['clip_run'])
    if is_hiss(m):
        found.append('hiss (%.0f %% below 2.5 kHz, flatness %.3f, centroid %.0f Hz)'
                     % (100 * m['body'], m['flatness'], m['centroid']))
    if m['active_db'] > bounds['level']['max'] + 1.0:
        found.append('loud (%.1f dB, MM6-MM8 max %.1f)' % (m['active_db'], bounds['level']['max']))
    if m['active_db'] < bounds['level']['p01'] - 3.0:
        found.append('quiet (%.1f dB, MM6-MM8 1st percentile %.1f)' % (m['active_db'], bounds['level']['p01']))
    if m['seconds'] > bounds[slot]['max_seconds'] + 0.5 and not boss:
        found.append('long (%.2f s, MM6-MM8 %s max %.2f)' % (m['seconds'], slot, bounds[slot]['max_seconds']))
    if m['seconds'] < SHORT_SECONDS:
        found.append('short (%.2f s)' % m['seconds'])
    if slot in ONE_SHOTS and m['tail_db'] > m['active_db'] - CUT_DB:
        found.append('cut (last 20 ms at %.1f dB against %.1f active)' % (m['tail_db'], m['active_db']))
    if m['dc'] > DC_LIMIT:
        found.append('dc (%.3f)' % m['dc'])
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--all', action='store_true', help='list every Xeen sound with its numbers')
    parser.add_argument('--reference', action='store_true', help='print the MM6-MM8 bounds')
    parser.add_argument('--assets', default=None, help='an asset root other than assets_dev (a hard-link copy)')
    args = parser.parse_args()
    if args.assets:
        set_assets(args.assets)

    index = sound_files()
    xeen_rows = descriptors(XEEN / 'data_tables' / 'monster_descriptors.txt', XEEN_IDS)
    engine_rows = descriptors(ASSETS / 'engine' / 'data_tables' / 'monster_descriptors.txt')
    paths = set()
    for rows in (xeen_rows, engine_rows):
        for _name, sounds in rows.values():
            for sid in sounds:
                entry = index.get(sid)
                if entry and entry[1] is not None:
                    paths.add(entry[1])
    measured = measure_all(sorted(paths))
    bounds = reference_bounds(index, measured)
    if args.reference:
        for key, value in bounds.items():
            print('%-18s %s' % (key, value))

    bosses = boss_ids()
    errors = 0
    seen = {}
    for rid, (name, sounds) in sorted(xeen_rows.items()):
        for slot, sid in zip(SLOTS, sounds):
            entry = index.get(sid)
            if sid == 0:
                continue
            if entry is None or entry[1] is None:
                problems = ['missing (id %d: %s)' % (sid, 'no row' if entry is None else 'no file %s.wav' % entry[0])]
                origin, label, m = '?', str(sid), None
            else:
                label, path, origin = entry
                m = measured[path]
                problems = faults(slot, m, bounds, origin, rid in bosses)
            key = (sid, slot)
            if key in seen:
                seen[key][1].append(rid)
                continue
            seen[key] = (problems, [rid])
            if problems:
                errors += 1
            if problems or args.all:
                numbers = ''
                if m and 'error' not in m:
                    numbers = ('%.2fs %dHz/%dch active %.1f peak %.1f centroid %.0f body %2.0f%% tail %.1f'
                               % (m['seconds'], m['rate'], m['channels'], m['active_db'], m['peak_db'],
                                  m['centroid'], 100 * m['body'], m['tail_db']))
                print('%s %5d %-24s %-6s %-26s %s %s' % ('ERROR' if problems else 'ok   ', rid, name, slot,
                                                           label[:26], numbers, '; '.join(problems)))
    for (sid, slot), (problems, rids) in seen.items():
        if problems and len(rids) > 1:
            print('       sound %d (%s) also on rows %s' % (sid, slot, ', '.join(str(r) for r in rids[1:])))
    print('%d Xeen rows, %d distinct row sounds, %d with a fault' % (len(xeen_rows), len(seen), errors))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
