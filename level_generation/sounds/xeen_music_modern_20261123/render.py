#!/usr/bin/env python3
"""Render a World of Xeen song with sampled instruments instead of the FM chip: every note of the original, an
instrument chosen per channel (orchestration/<face>_<name>.yml), played by FluidSynth from a General MIDI
soundfont, with performance and mix added here: velocity shaping, slight timing looseness, swells on held notes,
stereo placement, a synthetic hall reverb, gentle compression and a seamless loop.

    python render.py xeen/town [--passes 2] [--out out/]       -> out/xeen_town.wav and .mp3

Needs FluidSynth (output/xeen_music_modern/third_party/fs_install/bin/fluidsynth, built from source), the
soundfont (output/xeen_music_modern/soundfonts/MuseScore_General.sf2, MIT), and numpy, scipy, mido, pyyaml,
pedalboard, ffmpeg.
"""
import argparse
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import mido
import numpy as np
import yaml
from scipy.signal import butter, fftconvolve, sosfilt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from xeen_song import DRUM_CHANNEL, REPO, TICK_HZ, patch_traits, read_song  # noqa: E402

TOOLS = REPO / "output/xeen_music_modern"
FLUIDSYNTH = TOOLS / "third_party/fs_install/bin/fluidsynth"
SOUNDFONT = TOOLS / "soundfonts/MuseScore_General.sf2"
RATE = 48000
PPQ = 480
BPM = 120.0                           # MIDI time only: 1 s = 960 MIDI ticks
# Every song decodes a whole tone below the composer's MT-32 recordings and every arrangement (town G major against
# F major here, outdoors D minor against C minor, end game B-flat against A-flat): play them in the composed keys.
TRANSPOSE = 2
FOLD = 1.0                            # seconds of crossfade at the loop point
SUSTAINED = set(range(40, 80)) | set(range(16, 24)) | {48, 49, 50, 51, 52, 53, 54}


def seconds_to_midi(t):
    return int(round(t * PPQ * BPM / 60.0))


def performance(song, channel, cfg, passes, rng, transpose, keep=lambda n: True):
    """(start_s, end_s, pitch, velocity) for a channel over `passes` passes, humanised."""
    notes = [n for n in song.notes if n.channel == channel and keep(n)]
    if not notes:
        return []
    velocities = [n.velocity for n in notes]
    lo, hi = min(velocities), max(velocities)
    remap = cfg.get("velocity")                 # [low, high]: spread the channel's velocities over this range
    octave = cfg.get("octave", 0)
    # The MT-32 played the same note data at its written pitch; the FM patches' frequency multiples only shape
    # the chip's timbre. patch_octave: true plays the FM-heard octave instead.
    use_patch_octave = cfg.get("patch_octave", False) and channel != DRUM_CHANNEL
    jitter = cfg.get("jitter_ms", 4 if channel == DRUM_CHANNEL else 7) / 1000.0
    legato = cfg.get("legato_ms", 40 if cfg.get("program", 0) in SUSTAINED else 0) / 1000.0
    out = []
    pass_s = song.seconds
    for p in range(passes):
        phrase = 0.0
        for n in notes:
            start = n.start / TICK_HZ + p * pass_s
            end = n.end / TICK_HZ + p * pass_s
            shift = 0
            if use_patch_octave and n.instrument in song.instruments:
                shift = 12 * patch_traits(song.instruments[n.instrument])["octave"]
            pitch = n.pitch + shift + 12 * octave + transpose if channel != DRUM_CHANNEL else n.pitch
            if channel != DRUM_CHANNEL:
                pitch = cfg.get("map", {}).get(pitch, pitch)
            if remap:
                span = (n.velocity - lo) / (hi - lo) if hi > lo else 0.7
                base = remap[0] + span * (remap[1] - remap[0])
            else:                               # the original sequence's velocity
                base = max(cfg.get("velocity_floor", 20), n.velocity)
            phrase = 0.96 * phrase + rng.gauss(0, 1.2)
            velocity = base + phrase + rng.gauss(0, 3)
            t = max(0.0, start + max(-2 * jitter, min(2 * jitter, rng.gauss(0, jitter))))
            out.append((t, max(t + 0.03, end + legato), int(pitch), int(max(1, min(127, velocity)))))
    return out


def write_midi(path, events, program, channel_no, swell, volumes, end_s):
    mid = mido.MidiFile(ticks_per_beat=PPQ)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    if channel_no != 9:
        bank = program // 128
        track.append(mido.Message("control_change", channel=channel_no, control=0, value=bank, time=0))
        track.append(mido.Message("program_change", channel=channel_no, program=program % 128, time=0))
    else:
        track.append(mido.Message("program_change", channel=9, program=program % 128, time=0))
    track.append(mido.Message("control_change", channel=channel_no, control=91, value=0, time=0))
    track.append(mido.Message("control_change", channel=channel_no, control=93, value=0, time=0))
    timeline = [(seconds_to_midi(t), 0, mido.Message("control_change", channel=channel_no, control=7,
                                                      value=int(v))) for t, v in volumes]
    for start, end, pitch, velocity in events:
        timeline.append((seconds_to_midi(start), 1, mido.Message("note_on", channel=channel_no, note=pitch,
                                                                     velocity=velocity)))
        timeline.append((seconds_to_midi(end), 0, mido.Message("note_off", channel=channel_no, note=pitch)))
        length = end - start
        if swell and length > 0.6:     # a held note grows and settles: CC11 expression
            steps = int(length / 0.05)
            for i in range(steps):
                x = i / steps
                value = 88 + 24 * np.sin(np.pi * min(1.0, x / 0.7)) * (1 if x < 0.7 else 0.6) + 8 * x
                timeline.append((seconds_to_midi(start + i * 0.05), 2,
                                 mido.Message("control_change", channel=channel_no, control=11,
                                              value=int(min(127, value)))))
            timeline.append((seconds_to_midi(end) + 1, 2,
                             mido.Message("control_change", channel=channel_no, control=11, value=100)))
    # FluidSynth stops at the file's last event: a last controller at the end keeps releases and rests.
    timeline.append((seconds_to_midi(end_s), 3, mido.Message("control_change", channel=channel_no, control=110,
                                                             value=0)))
    timeline.sort(key=lambda e: (e[0], e[1]))
    now = 0
    for when, _, message in timeline:
        track.append(message.copy(time=max(0, when - now)))
        now = max(now, when)
    mid.save(path)


def fluid_render(midi_path, seconds):
    with tempfile.NamedTemporaryFile(suffix=".raw") as raw:
        subprocess.run([str(FLUIDSYNTH), "-ni", "-q", "-R", "0", "-C", "0", "-g", "0.6", "-r", str(RATE),
                        "-O", "s16", "-T", "raw", "-E", "little", "-F", raw.name, str(SOUNDFONT), str(midi_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       env={**os.environ, "LD_LIBRARY_PATH": str(FLUIDSYNTH.parent.parent / "lib")})
        audio = np.fromfile(raw.name, dtype="<i2").reshape(-1, 2).astype(np.float32) / 32768.0
    need = int(seconds * RATE)
    if len(audio) < need:
        audio = np.vstack([audio, np.zeros((need - len(audio), 2), np.float32)])
    return audio[:need]


def hall_ir(seconds=2.4, predelay=0.022, seed=7):
    """A stereo hall impulse response: sparse early reflections, then decorrelated noise decaying to -60 dB over
    `seconds`, darkening as it decays."""
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    ir = np.zeros((n, 2), np.float32)
    for side in range(2):
        noise = rng.standard_normal(n) * np.exp(-6.91 * t / seconds)
        early = int(0.08 * RATE)
        noise[:early] *= np.linspace(0.2, 1.0, early)
        lo = sosfilt(butter(1, 2500, "lowpass", fs=RATE, output="sos"), noise)
        mix = np.clip(t / seconds * 1.6, 0, 1)
        ir[:, side] = (1 - mix) * noise + mix * lo
        for _ in range(10):
            k = int(rng.uniform(0.006, 0.07) * RATE)
            ir[k, side] += rng.uniform(0.3, 0.7) * rng.choice([-1, 1])
    ir = np.vstack([np.zeros((int(predelay * RATE), 2), np.float32), ir])
    return ir / np.sqrt((ir ** 2).sum(axis=0).mean())


def pan(audio, position, width):
    """Equal-power placement of a stereo stem: position -1 (left) .. 1 (right), width 0 (mono) .. 1."""
    mid = audio.mean(axis=1)
    side = (audio[:, 0] - audio[:, 1]) * 0.5 * width
    angle = (position + 1) * np.pi / 4
    left = mid * np.cos(angle) * np.sqrt(2) + side
    right = mid * np.sin(angle) * np.sqrt(2) - side
    return np.stack([left, right], axis=1)


def render(name, out_dir, passes, seed):
    song = read_song(name)
    stem_name = name.replace("/", "_")
    cfg_path = HERE / "orchestration" / f"{stem_name}.yml"
    cfg = yaml.safe_load(cfg_path.read_text())
    rng = random.Random(seed)
    tail = 4.0
    total = song.seconds * passes + tail
    mix = np.zeros((int(total * RATE), 2), np.float32)
    send = np.zeros_like(mix)
    with tempfile.TemporaryDirectory() as tmp:
        for key, ch_cfg in cfg["channels"].items():
            channel = int(key)
            if ch_cfg.get("mute"):
                continue
            volumes = [(t / TICK_HZ + p * song.seconds, min(127, v)) for p in range(passes)
                       for t, ch, v in song.levels if ch == channel]
            # A channel switches FM instruments as it goes; `slots` gives some of them their own instrument.
            slot_cfgs = {int(k): v for k, v in (ch_cfg.get("slots") or {}).items()}
            groups = [({**ch_cfg, "slots": None}, lambda n, s=set(slot_cfgs): n.instrument not in s)]
            groups += [({**ch_cfg, **sub, "slots": None}, lambda n, k=k: n.instrument == k)
                       for k, sub in slot_cfgs.items()]
            for index, (g_cfg, keep) in enumerate(groups):
                if g_cfg.get("mute"):
                    continue
                events = performance(song, channel, g_cfg, passes, rng, cfg.get("transpose", TRANSPOSE), keep)
                if not events:
                    continue
                program = g_cfg.get("program", 0)
                midi_channel = 9 if channel == DRUM_CHANNEL else 0
                midi_path = Path(tmp) / f"ch{channel}_{index}.mid"
                write_midi(midi_path, events, program, midi_channel, g_cfg.get("swell", program in SUSTAINED),
                           volumes, total)
                audio = fluid_render(midi_path, total)
                audio = pan(audio, g_cfg.get("pan", 0.0), g_cfg.get("width", 0.6))
                audio *= 10 ** (g_cfg.get("gain_db", 0.0) / 20)
                mix += audio
                send += audio * g_cfg.get("reverb", 0.25)
    reverb = cfg.get("reverb", {})
    ir = hall_ir(reverb.get("seconds", 2.4), reverb.get("predelay", 0.022))
    wet = np.stack([fftconvolve(send[:, i], ir[:, i])[:len(send)] for i in range(2)], axis=1)
    mix = mix + wet * reverb.get("level", 0.35)
    mix = sosfilt(butter(2, 30, "highpass", fs=RATE, output="sos"), mix, axis=0)
    # Compression and limiting run over the whole render, so their state is continuous across the loop point.
    from pedalboard import Compressor, Limiter, Pedalboard
    board = Pedalboard([Compressor(threshold_db=-20, ratio=2.0, attack_ms=30, release_ms=250),
                        Limiter(threshold_db=-1.5, release_ms=120)])
    body = mix[int(song.seconds * RATE):int(2 * song.seconds * RATE)] if song.loops and passes >= 3 else mix
    mix = mix * (10 ** (-17 / 20) / max(float(np.sqrt((body ** 2).mean())), 1e-9))
    mix = board(mix.T.astype(np.float32), RATE).T
    if song.loops and passes >= 3:
        # The second pass, which opens with the first pass's reverb and releases. Its opening is crossfaded from
        # the third pass's opening (the same music that follows the second pass's last sample) into its own, so
        # the end runs into the start without a click.
        start, length, fold = int(song.seconds * RATE), int(song.seconds * RATE), int(FOLD * RATE)
        segment = mix[start:start + length + fold]
        mix = segment[:length].copy()
        ramp = np.linspace(0.0, 1.0, fold, dtype=np.float32)[:, None]
        mix[:fold] = segment[length:length + fold] * (1 - ramp) + segment[:fold] * ramp
    else:
        mix = mix[:int((song.seconds + (0 if song.loops else tail)) * RATE)]
    # Settle at Xeen's music level (-17 dBFS RMS) with the peak at most -1 dBFS.
    mix *= min(10 ** (-17 / 20) / max(float(np.sqrt((mix ** 2).mean())), 1e-9),
               10 ** (-1 / 20) / max(float(np.abs(mix).max()), 1e-9))
    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / f"{stem_name}.wav"
    import soundfile as sf
    sf.write(wav, mix, RATE, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-b:a", "320k",
                    str(wav.with_suffix(".mp3"))], check=True)
    peak = float(np.abs(mix).max())
    print(f"{song.name}: {len(mix) / RATE:.1f} s, peak {20 * np.log10(peak):.1f} dBFS, "
          f"RMS {20 * np.log10(np.sqrt((mix ** 2).mean())):.1f} dBFS -> {wav.with_suffix('.mp3')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("songs", nargs="+")
    ap.add_argument("--out", type=Path, default=HERE / "out")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    for song in args.songs:
        render(song, args.out, args.passes, args.seed)


if __name__ == "__main__":
    main()
