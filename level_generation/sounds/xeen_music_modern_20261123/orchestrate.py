#!/usr/bin/env python3
"""First orchestration of a Xeen song: a General MIDI instrument, placement and reverb send for every channel,
chosen from what the channel plays (register, note lengths, how busy it is, its FM patch). Writes
orchestration/<face>_<name>.yml unless one exists (hand-tuned files are never overwritten; --force rewrites).

    python orchestrate.py xeen/town dark/outday1 ...   |   python orchestrate.py --all
"""
import argparse
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from xeen_song import DRUM_CHANNEL, MUSIC_DIR, TICK_HZ, patch_traits, read_song  # noqa: E402

SCIFI = {"dark/sf05", "dark/sf09", "dark/scifi1", "dark/scifi2", "intro/sf17"}
# General MIDI programs, 0-based.
ORCH = {"bass_short": 33, "bass_long": 43, "pad": 49, "pad2": 61, "arpeggio": 46, "bells": 9, "pluck": 45,
        "lead_high": 73, "lead_mid": 68, "lead_low": 60, "counter_high": 40, "counter_mid": 71, "counter_low": 42}
SYNTH = {"bass_short": 38, "bass_long": 39, "pad": 89, "pad2": 95, "arpeggio": 98, "bells": 98, "pluck": 98,
         "lead_high": 81, "lead_mid": 80, "lead_low": 87, "counter_high": 82, "counter_mid": 86, "counter_low": 87}
NAMES = {33: "fingered bass", 43: "contrabass", 49: "slow strings", 61: "brass section", 46: "harp",
         9: "glockenspiel", 45: "pizzicato strings", 73: "flute", 68: "oboe", 60: "french horn", 40: "violin",
         71: "clarinet", 42: "cello", 38: "synth bass 1", 39: "synth bass 2", 89: "warm pad", 95: "sweep pad",
         98: "crystal", 81: "saw lead", 80: "square lead", 87: "bass+lead", 82: "calliope", 86: "fifths lead"}


def unit_stats(song, notes, transpose=2):
    pitches = [n.pitch + transpose for n in notes]
    sustain_votes = sum(1 for n in notes if n.instrument in song.instruments
                        and patch_traits(song.instruments[n.instrument])["sustains"])
    lengths = [(n.end - n.start) / TICK_HZ for n in notes]
    return {"n": len(notes), "median": statistics.median(pitches), "range": max(pitches) - min(pitches),
            "length": statistics.median(lengths), "sounding": sum(lengths) / song.seconds,
            "sustains": sustain_votes > len(notes) / 2, "rate": len(notes) / song.seconds}


def classify(s):
    if s["median"] < 45:
        return "bass_short" if s["length"] < 0.5 else "bass_long"
    if s["length"] > 1.2:
        return "pad"
    if s["median"] >= 84 and s["sounding"] < 0.35:
        return "bells"
    if s["range"] >= 24 and s["length"] < 0.3 and s["rate"] > 1.5:
        return "arpeggio"
    if s["length"] < 0.2 and not s["sustains"]:
        return "pluck"
    return None


def orchestrate(name):
    """Units are a channel's notes per FM instrument (identical patches merged): a channel that switches from a
    bass sound to a lead sound gets two instruments."""
    song = read_song(name)
    palette = SYNTH if name in SCIFI else ORCH
    units = {}
    for ch in range(7):
        notes = [n for n in song.notes if n.channel == ch]
        by_patch = {}
        for n in notes:
            patch = bytes(song.instruments.get(n.instrument, b"")[:11])
            by_patch.setdefault(patch, []).append(n)
        for group in by_patch.values():
            if len(group) >= 4:
                units[(ch, tuple(sorted({n.instrument for n in group})))] = unit_stats(song, group)
    roles = {u: classify(s) for u, s in units.items()}
    lines = sorted((u for u, r in roles.items() if r is None), key=lambda u: -units[u]["sounding"] * units[u]["n"])
    for i, u in enumerate(lines):
        register = "high" if units[u]["median"] >= 69 else "mid" if units[u]["median"] >= 57 else "low"
        roles[u] = f"{'lead' if i == 0 else 'counter'}_{register}"
    pads = [u for u, r in roles.items() if r == "pad"]
    for u in pads[1:]:
        roles[u] = "pad2"

    side = [-0.4, 0.4, -0.25, 0.25, -0.5, 0.5, 0.15]

    def settings(role, i):
        program = palette[role]
        pan = 0.0 if role.startswith(("bass", "lead")) else side[i % len(side)]
        width = 0.9 if role.startswith("pad") else 0.25 if role.startswith("bass") else 0.6
        reverb = 0.06 if role.startswith("bass") else 0.4 if role.startswith(("pad", "bells")) else 0.28
        gain = -3 if role.startswith(("pad", "arpeggio")) else -6 if role == "bells" else 0
        return program, f"program: {program}, pan: {pan}, width: {width}, reverb: {reverb}, gain_db: {gain}"

    def note(role, program, s):
        return (f"{role}: {NAMES.get(program, program)}; median {s['median']:.0f}, {s['length']:.2f} s notes, "
                f"sounding {s['sounding']:.0%}")

    out = [f"# {name}: first orchestration by orchestrate.py (hand-tune freely; it is never overwritten).",
           f"# {song.seconds:.1f} s a pass. GM programs are 0-based; drums: 0 standard kit, 48 orchestral.",
           "# A channel's `slots` give the notes it plays with those FM instrument slots their own instrument.",
           f"reverb: {{seconds: {2.0 if name in SCIFI else 2.4}, level: 0.32}}", "channels:"]
    for ch in range(7):
        mine = sorted((u for u in units if u[0] == ch), key=lambda u: -units[u]["n"])
        if not mine:
            continue
        main = mine[0]
        program, text = settings(roles[main], ch)
        out.append(f"  {ch}:   # {note(roles[main], program, units[main])}")
        out.append(f"    {{{text}}}".replace("{", "", 1).rsplit("}", 1)[0] if False else f"    {text.replace(', ', chr(10) + '    ')}")
        others = [u for u in mine[1:] if roles[u] != roles[main]]
        if others:
            out.append("    slots:")
            for u in others:
                p, t = settings(roles[u], ch + 3)
                for slot in u[1]:
                    out.append(f"      {slot}: {{{t}}}   # {note(roles[u], p, units[u])}")
    drums = [n.pitch for n in song.notes if n.channel == DRUM_CHANNEL]
    if drums:
        orchestral = set(drums) <= {35, 36, 38, 40, 41, 43, 45, 47, 48, 49, 50, 52, 55, 57}
        kit = 48 if orchestral and name not in SCIFI else 0
        out.append(f"  8:   # drums ({'orchestral' if kit == 48 else 'standard'} kit), notes {sorted(set(drums))}")
        out.append(f"    program: {kit}\n    pan: 0.0\n    width: 0.5\n    reverb: 0.15\n    gain_db: -3")
    return "\n".join(out) + "\n"


def all_songs():
    return sorted(f"{p.parent.name}/{p.stem}" for p in MUSIC_DIR.glob("*/*.m"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("songs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    (HERE / "orchestration").mkdir(exist_ok=True)
    for name in all_songs() if args.all else args.songs:
        path = HERE / "orchestration" / f"{name.replace('/', '_')}.yml"
        if path.exists() and not args.force:
            continue
        path.write_text(orchestrate(name))
        print(path.name)


if __name__ == "__main__":
    main()
