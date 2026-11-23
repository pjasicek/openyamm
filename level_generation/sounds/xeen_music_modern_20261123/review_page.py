#!/usr/bin/env python3
"""Local listening page: per song the AdLib render of the game's data (output/xeen_music), the new render
(out/), and where downloaded, the MT-32 recording or an arrangement (../xeen_music_alike_20261123/work/ref_clips,
git-ignored). Open review/index.html from disk.
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ADLIB = REPO / "output/xeen_music/all"
REFS = HERE.parent / "xeen_music_alike_20261123/work/ref_clips"
SONGS = [  # (song, what it is in the game, Xeen slot, reference clip)
    ("xeen/town", "Clouds towns (Vertigo)", "92003", "cloudside_town_mt32"),
    ("xeen/outdoors", "Clouds outdoors", "92001", "cloudside_overworld_mt32"),
    ("dark/newbrigh", "Darkside towns, main menu", "92004", "darkside_town_day2_arr"),
    ("xeen/castle", "Clouds castles", "92005", "castle_mt32"),
    ("xeen/dungeon", "Clouds dungeons, towers", "92006", "dungeon_castle_mt32"),
    ("xeen/cavern", "Clouds caverns, mines", "92006 (alt)", "cavern_town_mt32"),
    ("dark/sf05", "Darkside sci-fi places", "92007", "ancients_scifi5_arr"),
    ("xeen/endgame", "Clouds ending", "92008", "finale_endgame_mt32"),
    ("dark/outday1", "Darkside outdoors (day 1)", "92002", None),
    ("dark/outday2", "Darkside outdoors (day 2)", "92002 (alt)", None),
    ("dark/outday4", "Darkside outdoors (day 4)", "92002 (alt)", None),
    ("intro/outday3", "Dragon Pharaoh / World of Xeen ending", "92002 (alt)", "darkside_overworld_arr"),
]


def rel(path):
    return str(Path("..") / path.relative_to(HERE)) if HERE in path.parents else \
        str(Path("../../../..") / path.relative_to(REPO))


def player(label, path):
    if not path.exists():
        return f'<div class="p"><span>{html.escape(label)}</span><i>missing</i></div>'
    return (f'<div class="p"><span>{html.escape(label)}</span>'
            f'<audio controls preload="none" src="{html.escape(rel(path))}"></audio></div>')


def main():
    checks = {}
    check_file = HERE / "work" / "checks.json"
    if check_file.exists():
        checks = json.loads(check_file.read_text())
    rows = []
    for song, use, slot, ref in SONGS:
        stem = song.replace("/", "_")
        cells = [player("new render", HERE / "out" / f"{stem}.mp3"),
                 player("AdLib (game data, chip emulated)", ADLIB / f"{song}.mp3")]
        if ref:
            cells.append(player(f"recording: {ref} (90 s)", REFS / f"{ref}.mp3"))
        orch = HERE / "orchestration" / f"{stem}.yml"
        check = checks.get(song, "")
        rows.append(f"<section><h2>{html.escape(song)} <small>{html.escape(use)}; slot {slot}</small></h2>"
                    f"{''.join(cells)}<p class=c>{html.escape(check)}</p>"
                    f"<details><summary>orchestration</summary><pre>{html.escape(orch.read_text())}</pre>"
                    f"</details></section>")
    listed = {song for song, *_ in SONGS}
    others = sorted(f"{m.stem.split('_', 1)[0]}/{m.stem.split('_', 1)[1]}" for m in (HERE / "out").glob("*.mp3"))
    rows.append("<h2>Every other song</h2>")
    for song in (o for o in others if o not in listed):
        stem = song.replace("/", "_")
        rows.append(f"<section><h3>{html.escape(song)}</h3>"
                    f"{player('new render', HERE / 'out' / f'{stem}.mp3')}"
                    f"{player('AdLib', ADLIB / f'{song}.mp3')}<p class=c>{html.escape(checks.get(song, ''))}</p>"
                    f"<details><summary>orchestration</summary><pre>"
                    f"{html.escape((HERE / 'orchestration' / f'{stem}.yml').read_text())}</pre></details></section>")
    page = ("<!doctype html><meta charset=utf-8><title>Xeen music, modern instruments</title><style>"
            "body{font:15px system-ui;max-width:1100px;margin:2em auto;background:#16161a;color:#ddd}"
            "section{border-top:1px solid #444;padding:.6em 0}small{color:#999;font-weight:normal}"
            ".p{display:flex;gap:1em;align-items:center;margin:.3em 0}.p span{width:330px}audio{width:640px}"
            "pre{font-size:12px;color:#aaa}.c{color:#9c9;font-size:13px}</style>"
            "<h1>Xeen music: the original notes, modern instruments</h1>"
            "<p>Every note comes from the game's own song files. The instruments are a sampled General MIDI set "
            "(MuseScore General, MIT), with performance, stereo placement and a hall added. Keys follow the "
            "composer's MT-32 recordings (a whole tone above the decoded data). Local page: the recordings are "
            "downloaded references, not ours.</p>" + "".join(rows))
    (HERE / "review").mkdir(exist_ok=True)
    (HERE / "review" / "index.html").write_text(page)
    print(HERE / "review" / "index.html")


if __name__ == "__main__":
    main()
