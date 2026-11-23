"""Read a World of Xeen `.m` song into note events, following the game's own driver (see
output/xeen_music/README.md for the format, read from the `admus` disassembly).

Each of the music channels 0-6 is one monophonic FM voice: a note sounds from its note-on until the channel's next
note-off or note-on. Channel 8 holds General MIDI percussion (raw drum numbers: 36 kick, 38 snare, 42 hi-hat, 49 crash,
54 tambourine, 61-62 bongos ...) that the FM drivers never play. Velocities are the original sequence's; the FM driver ignores them.
"""
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MUSIC_DIR = REPO / "reference/mm4_5_world_of_xeen/unpacked/music"
TICK_HZ = 1193182 / 0x4006            # the driver's timer: about 72.80 Hz
DRUM_CHANNEL = 8
LEVEL_CONTROLLER = 0                  # the MIDI (MT-32) mix: channel volume 0-127. The FM mixes are 2 (AdLib) and 5
                                      # (Sound Blaster), attenuations 0-63 that switch off parts FM could not carry.
SEMITONE = (0, 0, 2, 4, 5, 7, 9, 11)  # note bits 0-2: scale degree 1-7 of C major; bits 3-4: natural, sharp, flat
NOTE_NAMES = "C C# D Eb E F F# G Ab A Bb B".split()


@dataclass
class Note:
    channel: int
    start: int                        # ticks
    end: int
    pitch: int                        # MIDI note number
    velocity: int
    instrument: int                   # the channel's current instrument slot (program change 0xC)


@dataclass
class Song:
    name: str
    notes: list = field(default_factory=list)
    levels: list = field(default_factory=list)   # (tick, channel, MIDI channel volume 0-127)
    instruments: dict = field(default_factory=dict)
    pass_ticks: int = 0
    loops: bool = True

    @property
    def seconds(self):
        return self.pass_ticks / TICK_HZ


def song_path(text):
    path = Path(text)
    if path.exists():
        return path
    candidate = MUSIC_DIR / text
    return candidate if candidate.suffix else candidate.with_suffix(".m")


def pitch_of(note_byte):
    degree = note_byte & 0x1F
    row, index = divmod(degree, 8)
    return 12 * ((note_byte >> 5) + 1) + SEMITONE[index] + (0, 1, -1)[row]


def note_name(pitch):
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12 - 1}"


def read_song(text):
    path = song_path(text)
    d = path.read_bytes()
    song = Song(name=f"{path.parent.name}/{path.stem}")
    pos, stack, tick = 0, [], 0
    sounding = {}                     # channel -> (start, pitch, velocity, instrument)
    program = {}

    def stop(channel):
        if channel in sounding:
            start, pitch, velocity, instrument = sounding.pop(channel)
            if tick > start:
                song.notes.append(Note(channel, start, tick, pitch, velocity, instrument))

    steps = 0
    while True:
        steps += 1
        if steps > 2_000_000 or pos >= len(d):
            raise RuntimeError(f"{song.name}: runaway stream at {pos:#x}")
        byte = d[pos]
        pos += 1
        command, channel = byte >> 4, byte & 0x0F
        if command == 0x0:
            stack.append(pos + 2)
            pos = d[pos] | (d[pos + 1] << 8)
        elif command == 0x1:
            count = channel or d[pos]
            if not channel:
                pos += 1
            tick += count
        elif command == 0x2:
            song.instruments[channel] = d[pos:pos + 26]
            pos += 26
        elif command in (0x4, 0x5):
            pos += 2
        elif command == 0x6:
            pos += 1
        elif command == 0x8:
            pos += 1
            stop(channel)
        elif command == 0x9:
            # The percussion channel stores raw General MIDI drum numbers (36 kick, 38 snare, 42 hi-hat, 49 crash
            # ...); the music channels store octave and scale step.
            pitch = d[pos] if channel == DRUM_CHANNEL else pitch_of(d[pos])
            velocity = d[pos + 1]
            pos += 2
            stop(channel)
            sounding[channel] = (tick, pitch, velocity, program.get(channel, 0))
        elif command == 0xA:
            if d[pos] == LEVEL_CONTROLLER:
                song.levels.append((tick, channel, d[pos + 1]))
            pos += 2
        elif command == 0xB:
            while d[pos] != 0xF7:
                pos += 1
            pos += 1
        elif command == 0xC:
            program[channel] = d[pos] & 0x0F
            pos += 1
        elif command == 0xE:
            pos += 3
        elif byte == 0xFF and stack:
            pos = stack.pop()
        else:                         # 0xFF at the top level loops to the start; 0xF0-0xFE stop the song
            song.loops = byte == 0xFF
            for ch in list(sounding):
                stop(ch)
            break
    song.pass_ticks = tick
    song.notes = [n for n in song.notes if n.channel <= 6 or n.channel == DRUM_CHANNEL]
    song.notes.sort(key=lambda n: (n.start, n.channel))
    return song


def patch_traits(patch):
    """What an FM instrument slot sounds like, from its OPL bytes: sustaining or decaying, attack speed, the
    carrier's frequency multiple (an octave shift of the heard pitch)."""
    car_char, car_ad, car_sr = patch[5], patch[7], patch[8]
    mult = car_char & 0x0F
    octave = {0: -1, 1: 0, 2: 1, 3: 1, 4: 2}.get(mult, 2)
    return {"sustains": bool(car_char & 0x20), "attack": car_ad >> 4, "decay": car_ad & 0x0F,
            "sustain_level": car_sr >> 4, "release": car_sr & 0x0F, "octave": octave}
