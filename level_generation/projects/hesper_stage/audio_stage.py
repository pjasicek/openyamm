"""The stage's Hesper sounds (audio.yml): the picked WAVs of the ElevenLabs workspace as worlds/hesper/audio/hesper,
sounds.txt rows for the names a table refers to by number, and the staged monsters' descriptor sound columns.
Called by stage.py after its monster section, which writes the world's monster_descriptors.txt each run.

sounds.txt is rewritten from assets_dev each run (its stage copy holds no other stage rows).
"""
import csv
import shutil
import subprocess

import yaml

BLOCK = range(60000, 61000)                    # descriptor sound ids are 16-bit
# The descriptor columns (# InternalName Height Radius MovementSpeed ToHitRadius TintColor AttackSoundId DeathSoundId
# WinceSoundId AwareSoundId ...).
SOUND_COLUMNS = {'attack': 7, 'death': 8, 'wince': 9, 'bored': 10}   # 10: AwareSoundId, played as idle fidget


def install(root, project, dev, assets, world):
    config = yaml.safe_load((project / 'audio.yml').read_text())
    source = root / config['source']
    target = world / 'audio' / 'hesper'
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    installed = []
    for name in config['install']:
        wav = source / 'out' / name / f'{name}.wav'
        if not wav.exists():
            raise SystemExit(f'audio.yml names {name}, but {wav} is missing: run tools/run_elevenlabs.sh process')
        assert not (dev / 'engine/audio' / f'{name}.wav').exists(), name   # the merged audio tree's names are unique
        shutil.copy2(wav, target / f'{name}.wav')
        installed.append(name)

    sound_ids = config.get('sound_ids', {})
    native = (dev / 'engine/data_tables/sounds.txt').read_bytes()
    native_text = native.decode('latin-1')
    taken = {line.split('\t')[1] for line in native_text.splitlines()
             if len(line.split('\t')) > 1 and line.split('\t')[1].isdigit()}
    names = {line.split('\t')[0].lower() for line in native_text.splitlines()}
    rows = []
    for name, sound_id in sound_ids.items():
        assert sound_id in BLOCK and str(sound_id) not in taken and name in installed, (name, sound_id)
        assert name.lower() not in names, name
        rows.append(f'{name}\t{sound_id}\tswap\t3D\tHesper (stage)\n')
    assert len(set(sound_ids.values())) == len(sound_ids)
    if not native.endswith(b'\n'):
        native += b'\n'
    (assets / 'engine/data_tables/sounds.txt').write_bytes(native + ''.join(rows).encode('ascii'))

    descriptors_path = world / 'data_tables/monster_descriptors.txt'
    with descriptors_path.open(newline='') as stream:
        descriptors = list(csv.reader(stream, delimiter='\t'))
    by_id = {row[0]: row for row in descriptors if row and row[0].isdigit()}
    voiced = []
    for monster_id, sounds in (config.get('monsters') or {}).items():
        row = by_id.get(str(monster_id))
        if row is None:                                 # not staged (monsters.yml): nothing to voice yet
            continue
        for role, name in sounds.items():
            row[SOUND_COLUMNS[role]] = str(sound_ids[name])
        voiced.append(monster_id)
    with descriptors_path.open('w', newline='') as stream:
        csv.writer(stream, delimiter='\t', lineterminator='\n').writerows(descriptors)
    # The maps' music tracks: MP3s encoded from the picks (only when the pick is newer), and the Track column (29th,
    # index 28) of the maps' rows in the stage copy of map_stats.txt, which stage.py's map section has written.
    music = world / 'music'
    music.mkdir(exist_ok=True)
    tracks = config.get('music') or {}
    for path in music.glob('*.mp3'):
        if int(path.stem) not in tracks:
            path.unlink()
    for track, name in tracks.items():
        mp3 = music / f'{track}.mp3'
        assert not (dev / 'engine/music' / mp3.name).exists(), (track, name)
        encoded = source / 'out' / name / f'{name}.mp3'       # a music job's own MP3 (elevenlabs_gen.py process)
        if encoded.exists():
            shutil.copy2(encoded, mp3)
            continue
        wav = source / 'out' / name / f'{name}.wav'            # a sound used as a track: encoded here
        if not wav.exists():
            raise SystemExit(f'audio.yml music {track}: neither {encoded} nor {wav} exists')
        if not mp3.exists() or mp3.stat().st_mtime < wav.stat().st_mtime:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-codec:a', 'libmp3lame', '-b:a', '320k',
                            str(mp3)], check=True)
    map_stats = assets / 'engine/data_tables/map_stats.txt'
    lines = map_stats.read_bytes().split(b'\n')
    set_tracks = {}
    for index, line in enumerate(lines):
        cells = line.split(b'\t')
        name = cells[2].decode('latin-1').strip().lower() if len(cells) > 28 else ''
        track = (config.get('map_tracks') or {}).get(name)
        if track is not None and cells[0].strip().isdigit():
            assert track in tracks, (name, track)
            cells[28] = str(track).encode()
            lines[index] = b'\t'.join(cells)
            set_tracks[name] = track
    map_stats.write_bytes(b'\n'.join(lines))
    return {'installed': len(installed), 'sound_ids': len(rows), 'voiced_monsters': sorted(voiced),
            'music': {str(k): v for k, v in tracks.items()}, 'map_tracks': set_tracks}
