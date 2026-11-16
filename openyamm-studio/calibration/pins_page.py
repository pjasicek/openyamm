#!/usr/bin/env python3
"""Writes the pins page of the Map Studio: output/studio_review/pins.html (S5_BROWSER_EDITOR.md 2.10, slice S5a1).

Every project's review pins (review/pins.yml, read through `oymap pins list --json`) with the user's own picture from
the game (the before), the thread of replies with the agents' pictures (the after), and the status: open, claimed,
resolved, accepted, declined. Open pins first. This is where the user reads the answers to the pins he made with
`pin <text>` in the game until the browser's Pins panel exists (slice S5a3).

    python3 openyamm-studio/calibration/pins_page.py [--oymap <binary>] [--project <folder>]... [--out <folder>]

Without --project the projects are found under devdocs/map_studio/briefs, devdocs/xeen/briefs and output/studio_cal
(those with a review/pins.yml). The pictures are copied beside the page (pins_img/), so the page is one folder of
static files that reads nothing from the network.
"""
import argparse
import html
import json
import os
import shutil
import subprocess
from pathlib import Path

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
ROOTS = ['devdocs/map_studio/briefs', 'devdocs/xeen/briefs', 'output/studio_cal']
SKIP = {'.oymap', 'build', 'node_modules', '.git', 'renders', 'shots', 'compare', 'ingame', 'mount', 'root', 'run'}
STATUS_ORDER = {'open': 0, 'claimed': 1, 'resolved': 2, 'declined': 3, 'accepted': 4}


def find_projects(root, depth=4):
    found = []
    for folder, dirs, files in os.walk(root):
        level = Path(folder).relative_to(root).parts
        dirs[:] = [d for d in sorted(dirs) if d not in SKIP and not d.startswith('.') and len(level) < depth]
        if 'project.yml' in files and (Path(folder) / 'review' / 'pins.yml').exists():
            found.append(Path(folder))
            dirs[:] = []
    return found


def card_name(project):
    for line in (project / 'project.yml').read_text(encoding='utf-8').splitlines():
        if line.startswith('name:'):
            return line.split(':', 1)[1].strip().strip('"')
    return project.name


def picture(project, relative, images, key):
    """Copies a pin picture beside the page; the link, or None when it is not on this machine."""
    if not relative:
        return None
    source = project / relative
    if not source.exists():
        return None
    target = images / f'{key}{source.suffix or ".png"}'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return f'{images.name}/{target.name}'


def figure(link, caption):
    if link is None:
        return f'<div class="missing">{html.escape(caption)}: not on this machine</div>'
    return (f'<figure><a href="{html.escape(link)}"><img src="{html.escape(link)}" alt="{html.escape(caption)}"></a>'
            f'<figcaption>{html.escape(caption)}</figcaption></figure>')


def pin_section(project, slug, pin, images):
    status = pin.get('status', 'open')
    key = f'{slug}_{pin["id"].split(":", 1)[-1]}'
    where = []
    if pin.get('on'):
        where.append(f'on {pin["on"]}' + (f' ({pin["file"]})' if pin.get('file') else ''))
    if pin.get('map'):
        where.append(f'{pin["map"]} ({pin.get("world", "?")})')
    pose = pin.get('pose')
    if pose:
        position = ', '.join(str(value) for value in pose.get('position', []))
        where.append(f'stood at {position}, yaw {pose.get("yaw_radians", "?")} rad, pitch '
                     f'{pose.get("pitch_degrees", "?")} degrees')
    elif pin.get('at'):
        where.append('at ' + ', '.join(str(value) for value in pin['at']))
    meta = ', '.join(part for part in [pin.get('author'), pin.get('source'), pin.get('created')] if part)
    claimed = f' by {pin["claimed_by"]}' if pin.get('claimed_by') else ''
    pictures = [figure(picture(project, pin.get('picture'), images, key), 'before (the pin\'s own picture)')]
    replies = []
    for number, reply in enumerate(pin.get('replies', []), start=1):
        pictures += [figure(picture(project, path, images, f'{key}_r{number}_{index}'), f'after (reply {number})')
                     for index, path in enumerate(reply.get('pictures', []), start=1)]
        replies.append(
            f'<li><b>{html.escape(reply.get("author", "?"))}</b>'
            + (f' <span class="status {html.escape(reply["status"])}">{html.escape(reply["status"])}</span>'
               if reply.get('status') else '')
            + (f' <span class="meta">{html.escape(reply.get("created", ""))}</span>' if reply.get('created') else '')
            + f'<div>{html.escape(reply.get("text", ""))}</div></li>')
    return (
        f'<article class="pin {html.escape(status)}" id="{html.escape(key)}">'
        f'<h3><span class="status {html.escape(status)}">{html.escape(status)}{html.escape(claimed)}</span> '
        f'{html.escape(pin["id"])}</h3>'
        f'<p class="text">{html.escape(pin.get("text", ""))}</p>'
        f'<p class="meta">{html.escape(meta)}' + (f'<br>{html.escape("; ".join(where))}' if where else '') + '</p>'
        f'<div class="pictures">{"".join(pictures)}</div>'
        + (f'<ol class="replies">{"".join(replies)}</ol>' if replies else '')
        + '</article>')


PAGE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Map Studio pins</title>
<style>
:root { --bg: #f6f5f2; --fg: #1d1d1b; --muted: #6b6a66; --card: #ffffff; --line: #dddad3;
  --open: #b4471f; --claimed: #8a6d00; --resolved: #2f6db3; --accepted: #2e7d4a; --declined: #6b6a66; }
@media (prefers-color-scheme: dark) { :root { --bg: #161615; --fg: #ecebe7; --muted: #a3a29d; --card: #20201e;
  --line: #3a3935; --open: #f08a5d; --claimed: #e0c050; --resolved: #7fb0f0; --accepted: #7fd09a; --declined: #a3a29d; } }
body { background: var(--bg); color: var(--fg); font: 15px/1.45 system-ui, sans-serif; margin: 0 auto;
  max-width: 1100px; padding: 16px; }
h1 { font-size: 22px; } h2 { font-size: 18px; margin-top: 32px; border-bottom: 1px solid var(--line); }
h3 { font-size: 15px; margin: 0 0 6px; }
.pin { background: var(--card); border: 1px solid var(--line); border-radius: 6px; padding: 12px; margin: 12px 0; }
.status { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.status.open { color: var(--open); } .status.claimed { color: var(--claimed); }
.status.resolved { color: var(--resolved); } .status.accepted { color: var(--accepted); }
.status.declined { color: var(--declined); }
.text { font-size: 16px; margin: 4px 0; } .meta { color: var(--muted); font-size: 13px; margin: 4px 0; }
.pictures { display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0; }
figure { margin: 0; max-width: 100%; } img { max-width: 520px; width: 100%; border-radius: 4px; display: block; }
figcaption { color: var(--muted); font-size: 12px; } .missing { color: var(--muted); font-size: 13px; }
.replies { margin: 6px 0 0; padding-left: 20px; } .replies li { margin: 6px 0; }
</style></head><body>
<h1>Map Studio pins</h1>
<p class="meta">The notes made with <code>pin &lt;text&gt;</code> in the game, filed with <code>oymap pins import</code>,
and what the agents did about them. Open pins first. Accept or reopen with
<code>oymap pins accept|reopen &lt;project&gt; &lt;pin&gt; --text ...</code>.</p>
@SUMMARY@
@PROJECTS@
</body></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--oymap', default=str(studio / 'build/oymap'))
    parser.add_argument('--project', action='append', default=[])
    parser.add_argument('--out', default=str(repo / 'output/studio_review'))
    arguments = parser.parse_args()
    out = Path(arguments.out)
    images = out / 'pins_img'
    projects = [Path(p).resolve() for p in arguments.project]
    if not projects:
        for root in ROOTS:
            if (repo / root).is_dir():
                projects += find_projects(repo / root)
    sections = []
    totals = {}
    for project in projects:
        listed = subprocess.run([arguments.oymap, 'pins', 'list', str(project), '--json'], capture_output=True,
                                text=True)
        if listed.returncode != 0:
            sections.append(f'<h2>{html.escape(str(project))}</h2><p class="missing">'
                            f'{html.escape(listed.stderr.strip())}</p>')
            continue
        pins = json.loads(listed.stdout)['pins']
        if not pins:
            continue
        pins.sort(key=lambda pin: STATUS_ORDER.get(pin.get('status', 'open'), 9))
        slug = str(project.relative_to(repo) if project.is_relative_to(repo) else project).replace('/', '_')
        for pin in pins:
            totals[pin.get('status', 'open')] = totals.get(pin.get('status', 'open'), 0) + 1
        shown = project.relative_to(repo) if project.is_relative_to(repo) else project
        sections.append(f'<h2>{html.escape(card_name(project))} <span class="meta">{html.escape(str(shown))}</span></h2>'
                        + ''.join(pin_section(project, slug, pin, images) for pin in pins))
    summary = ', '.join(f'{count} {status}' for status, count in
                        sorted(totals.items(), key=lambda item: STATUS_ORDER.get(item[0], 9))) or 'no pins yet'
    out.mkdir(parents=True, exist_ok=True)
    page = PAGE.replace('@SUMMARY@', f'<p><b>{html.escape(summary)}</b></p>').replace('@PROJECTS@', ''.join(sections))
    (out / 'pins.html').write_text(page, encoding='utf-8')
    print(out / 'pins.html')


if __name__ == '__main__':
    main()
