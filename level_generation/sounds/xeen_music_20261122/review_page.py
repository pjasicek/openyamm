#!/usr/bin/env python3
"""The review page for Xeen's music batch (lane AU): review/index.html with every theme's installed MP3, its prompt,
length and loop point, and a "loop seam" clip per theme (the loop's last 10 s run straight into its first 10 s, the
wrap the game plays at the join). Run after `tools/run_elevenlabs.sh process jobs.yml`.

    python3 level_generation/sounds/xeen_music_20261122/review_page.py

Writes review/index.html and review/audio/<id>.mp3 (a copy of out/<id>/<id>.mp3) and review/audio/<id>_seam.mp3.
The page references only review/audio/, so the folder can be published as is (an Artifact with its files).
"""
import html
import json
from pathlib import Path
import shutil
import subprocess

import yaml

ROOT = Path(__file__).resolve().parent
SEAM_SECONDS = 10.0


def probe_seconds(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(path)],
                            capture_output=True, text=True, check=True)
    return float(json.loads(result.stdout)['format']['duration'])


def make_seam(master, target, seconds):
    """The loop's tail then its head, joined sample-exact from the FLAC master (the fold already made the wrap
    continuous), encoded like the game's tracks."""
    length = probe_seconds(master)
    graph = (f'[0:a]atrim=start={length - SEAM_SECONDS:.6f},asetpts=PTS-STARTPTS[tail];'
             f'[0:a]atrim=end={SEAM_SECONDS:.6f},asetpts=PTS-STARTPTS[head];[tail][head]concat=n=2:v=0:a=1[out]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(master), '-filter_complex', graph, '-map', '[out]',
                    '-codec:a', 'libmp3lame', '-b:a', '320k', str(target)], check=True)


def clock(seconds):
    return f'{int(seconds // 60)}:{seconds % 60:04.1f}'


def main():
    jobs = yaml.safe_load((ROOT / 'jobs.yml').read_text())
    defaults = jobs.get('defaults', {})
    picks = yaml.safe_load((ROOT / 'picks.yml').read_text()) or {}
    ledger = json.loads((ROOT / 'ledger.json').read_text())
    review = ROOT / 'review'
    audio_dir = review / 'audio'
    audio_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    for raw in jobs['jobs']:
        job = {**defaults, **raw}
        entry = picks.get(job['id'])
        if not entry:
            continue
        variant = next(v for v in entry['variants'] if v['file'] == entry['picked'])
        out = ROOT / 'out' / job['id']
        master = out / f"{job['id']}.flac"
        shutil.copyfile(out / f"{job['id']}.mp3", audio_dir / f"{job['id']}.mp3")
        make_seam(master, audio_dir / f"{job['id']}_seam.mp3", SEAM_SECONDS)
        if (out / 'take1.mp3').exists():
            shutil.copyfile(out / 'take1.mp3', audio_dir / f"{job['id']}_take1.mp3")
        loop_seconds = probe_seconds(master)
        credits = sum(max(r['credits'], r.get('estimate', 0)) for r in ledger['requests'] if r['job'] == job['id'])
        fade = variant.get('fade_cut_s')
        loop_note = (f"The download ran {variant['raw_seconds']:.1f} s"
                     + (f"; its last {fade} s faded out and were cut" if fade else '')
                     + f"; the last {job['crossfade']} s are folded into the opening, so the loop is "
                     f"{loop_seconds:.1f} s and wraps from {clock(loop_seconds)} straight back to 0:00.")
        arc = ' / '.join(f'{v:+.0f}' for v in variant['arc_db'])
        cards.append(f'''
<article class="theme" id="{html.escape(job['id'])}">
  <header>
    <h2>{html.escape(job['title'])}</h2>
    <span class="len">{clock(loop_seconds)}</span>
  </header>
  <p class="use">{html.escape(job['use'])}</p>
  <div class="players">
    <div class="player"><span class="label">Full loop</span>
      <audio id="full-{job['id']}" controls loop preload="none" src="audio/{job['id']}.mp3"></audio></div>
    <div class="player"><span class="label">Loop seam: last {SEAM_SECONDS:.0f} s, then the first {SEAM_SECONDS:.0f} s
      (the join is at 0:{SEAM_SECONDS:02.0f})</span>
      <audio id="seam-{job['id']}" controls preload="none" src="audio/{job['id']}_seam.mp3"></audio></div>
  </div>
  {f'<div class="player"><span class="label">Take 1, replaced (for comparison)</span><audio id="take1-{job["id"]}" controls loop preload="none" src="audio/{job["id"]}_take1.mp3"></audio></div>' if (out / 'take1.mp3').exists() else ''}
  <p class="loop">{html.escape(loop_note)}</p>
  {f'<p class="note">{html.escape(entry["listening"])}</p>' if entry.get('listening') else ''}
  <dl class="facts">
    <div><dt>Level by quarter</dt><dd>{arc} dB</dd></div>
    <div><dt>Spread</dt><dd>{variant['level_spread_db']} dB</dd></div>
    <div><dt>Texture</dt><dd>{variant['onsets_per_minute']} onsets/min</dd></div>
    <div><dt>Brightness</dt><dd>{variant['centroid_hz']} Hz</dd></div>
    <div><dt>Score</dt><dd>{variant['score']}</dd></div>
    <div><dt>Credits</dt><dd>{credits:,}</dd></div>
  </dl>
  <details><summary>Prompt</summary><p class="prompt">{html.escape(job['prompt'])}</p></details>
  <p class="file"><code>out/{job['id']}/{job['id']}.mp3</code></p>
</article>''')
    spent = sum(max(r['credits'], r.get('estimate', 0)) for r in ledger['requests'])
    page = TEMPLATE.replace('{{CARDS}}', '\n'.join(cards)).replace('{{COUNT}}', str(len(cards))) \
        .replace('{{CREDITS}}', f'{spent:,}')
    (review / 'index.html').write_text(page)
    print(f'{review / "index.html"}: {len(cards)} themes')


TEMPLATE = '''<title>Xeen Music Themes</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Layout: one reading column of theme cards; each card a score sheet with two players. */
:root {
  --bg: #f3f1ec; --panel: #fbfaf7; --ink: #1f2430; --muted: #5d6473; --line: #d9d5cb; --accent: #2f5f8a;
  --display: "Cormorant Garamond", Georgia, serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15181f; --panel: #1c2029; --ink: #e6e3dc; --muted: #a2a8b5; --line: #323846; --accent: #8fb6dd;
  color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #15181f; --panel: #1c2029; --ink: #e6e3dc; --muted: #a2a8b5; --line: #323846; --accent: #8fb6dd;
  color-scheme: dark }
body { background: var(--bg); color: var(--ink); font-family: var(--body); font-size: 16px; line-height: 1.55; }
main { max-width: 46rem; margin: 0 auto; padding-block: 2.5rem 4rem;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 1.5rem; }
h1 { font-family: var(--display); font-weight: 600; font-size: 2.4rem; line-height: 1.1; margin: 0; text-wrap: balance; }
.lede { color: var(--muted); margin: 0; max-width: 65ch; }
.theme { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 1.25rem 1.25rem 1rem;
  display: grid; gap: .7rem; min-width: 0; }
.theme header { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; }
h2 { font-family: var(--display); font-weight: 600; font-size: 1.6rem; margin: 0; text-wrap: balance; }
.len { font-family: var(--mono); font-size: .9rem; color: var(--accent); font-variant-numeric: tabular-nums; }
.use { margin: 0; color: var(--muted); }
.players { display: grid; gap: .6rem; }
.player { display: grid; gap: .25rem; }
.label { font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
audio { width: 100%; }
.loop { margin: 0; font-size: .95rem; }
.note { margin: 0; font-size: .95rem; padding-left: .8rem; border-left: 2px solid var(--line); color: var(--muted); }
.facts { display: grid; grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr)); gap: .5rem 1rem; margin: 0; }
.facts div { min-width: 0; }
.facts dt { font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.facts dd { margin: 0; font-family: var(--mono); font-size: .85rem; font-variant-numeric: tabular-nums; }
details summary { cursor: pointer; color: var(--accent); font-weight: 600; }
details summary:focus-visible, audio:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.prompt { margin: .4rem 0 0; font-size: .95rem; }
.file { margin: 0; font-size: .8rem; color: var(--muted); overflow-wrap: anywhere; }
code { font-family: var(--mono); }
</style>
<main>
  <h1>Xeen Music Themes</h1>
  <p class="lede">{{COUNT}} new themes for the World of Xeen, made with Eleven Music: one take each, instrumental,
  150 s asked, folded into seamless loops (5 s crossfade, levelled to &minus;17 dBFS RMS) and encoded as 320 kbit/s
  MP3, the format the game plays. The full player loops, so you can hear the wrap in place; the seam clip plays just
  the join. Credits for the batch: {{CREDITS}} (estimated at 900 per minute; the API reports no cost for music).
  Nothing is installed yet.</p>
{{CARDS}}
</main>
'''

if __name__ == '__main__':
    main()
