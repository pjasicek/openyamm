#!/usr/bin/env python3
"""Local comparison page: each original Xeen reference (90 s clips, git-ignored) beside the generated sound-alike
and the theme it would replace. Open review/compare.html from disk; never publish it (the references are not ours).
"""
import html
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REFS = {
    "xeen_alike_cloudside_overworld": ["cloudside_overworld_mt32", "cloudside_overworld_arr"],
    "xeen_alike_darkside_overworld": ["darkside_overworld_arr", "darkside_overworld_woods_arr"],
    "xeen_alike_cloudside_town": ["cloudside_town_arr", "cloudside_town_mt32"],
    "xeen_alike_darkside_town": ["darkside_town_day2_arr", "darkside_town_day3_arr"],
    "xeen_alike_castle": ["castle_mt32", "castle_mm5_arr"],
    "xeen_alike_dungeon": ["dungeon_castle_mt32", "cavern_town_mt32", "dungeon_mm5_arr"],
    "xeen_alike_ancients": ["ancients_scifi5_arr", "ancients_scifi1_arr"],
    "xeen_alike_finale": ["finale_endgame_mt32", "finale_ending_arr"],
}


def player(label, src):
    return (f'<div class="p"><span>{html.escape(label)}</span>'
            f'<audio controls preload="none" src="{html.escape(src)}"></audio></div>')


def main():
    jobs = yaml.safe_load((HERE / "jobs.yml").read_text())["jobs"]
    rows = []
    for job in jobs:
        jid = job["id"]
        out = HERE / "out" / jid
        takes = sorted(out.glob("xeen_alike_*.mp3")) if out.exists() else []
        cells = [player(f"original: {r}", f"../work/ref_clips/{r}.mp3") for r in REFS[jid]]
        cells += [player(f"new: {t.name}", f"../out/{jid}/{t.name}") for t in takes] or ["<i>not generated</i>"]
        current = REPO / "assets_dev/worlds/xeen/music" / f"{job['replaces']}.mp3"
        cells.append(player(f"current {job['replaces']}", str(Path("../../../..") / current.relative_to(REPO))))
        analysis = "".join(
            f"<li>{html.escape((HERE / 'work/analysis' / f'{r}.md').read_text().splitlines()[2][2:])}</li>"
            for r in REFS[jid] if (HERE / "work/analysis" / f"{r}.md").exists())
        rows.append(f"<section><h2>{html.escape(job['title'])}</h2>{''.join(cells)}"
                    f"<details><summary>prompt and measurements</summary><p>{html.escape(job['prompt'])}</p>"
                    f"<ul>{analysis}</ul></details></section>")
    page = ("<!doctype html><meta charset=utf-8><title>Xeen sound-alikes</title><style>"
            "body{font:15px system-ui;max-width:1100px;margin:2em auto;background:#16161a;color:#ddd}"
            "section{border-top:1px solid #444;padding:.6em 0}.p{display:flex;gap:1em;align-items:center;margin:.3em 0}"
            ".p span{width:330px}audio{width:620px}details p{color:#aaa}</style>"
            "<h1>Xeen sound-alikes: original beside new</h1><p>Local only: the originals are 90 s clips of the "
            "downloaded references and must not be published.</p>" + "".join(rows))
    (HERE / "review").mkdir(exist_ok=True)
    (HERE / "review" / "compare.html").write_text(page)
    print(HERE / "review" / "compare.html")


if __name__ == "__main__":
    main()
