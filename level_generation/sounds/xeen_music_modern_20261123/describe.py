#!/usr/bin/env python3
"""What each channel of a Xeen song plays, to orchestrate it: notes, range, median pitch, note lengths, how much
of the song it sounds, polyphony-free density, its instruments' FM traits, its level, and an ASCII activity line
(one character per 8 s: . silent, - sparse, = busy, # dense).
    python describe.py xeen/town [dark/outday1 ...]
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xeen_song import TICK_HZ, note_name, patch_traits, read_song  # noqa: E402


def describe(name):
    song = read_song(name)
    print(f"== {song.name}: {song.seconds:.1f} s a pass, {'loops' if song.loops else 'ends'}, {len(song.notes)} notes")
    for channel in sorted({n.channel for n in song.notes}):
        notes = [n for n in song.notes if n.channel == channel]
        lengths = [(n.end - n.start) / TICK_HZ for n in notes]
        pitches = [n.pitch for n in notes]
        covered = sum(lengths) / max(song.seconds, 1e-6)
        slots = sorted({n.instrument for n in notes})
        traits = []
        for s in slots:
            if s in song.instruments:
                t = patch_traits(song.instruments[s])
                traits.append(f"i{s}:{'sus' if t['sustains'] else 'dec'} a{t['attack']} d{t['decay']} "
                              f"o{t['octave']:+d}")
        levels = [v for _, ch, v in song.levels if ch == channel]
        bins = int(song.seconds // 8) + 1
        counts = [0] * bins
        for n in notes:
            counts[min(bins - 1, int(n.start / TICK_HZ // 8))] += 1
        line = "".join("." if c == 0 else "-" if c < 6 else "=" if c < 20 else "#" for c in counts)
        vel = sorted(n.velocity for n in notes)
        print(f" ch{channel}: {len(notes):4d} notes {note_name(min(pitches))}-{note_name(max(pitches))} "
              f"median {note_name(int(statistics.median(pitches)))}; length med {statistics.median(lengths):.2f} s "
              f"max {max(lengths):.1f}; sounding {covered:.0%}; vel {vel[0]}-{vel[-1]} med {vel[len(vel)//2]}; "
              f"level {min(levels) if levels else '-'}-{max(levels) if levels else '-'}")
        print(f"      {' '.join(traits)}  |{line}|")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        describe(arg)
