#!/usr/bin/env python3
"""Build the Xeen world's generated data from its sources.

    python3 tools/xeen/build_world.py            write assets_dev/worlds/xeen/data_tables/, relations.yml, modifiers.yml
    python3 tools/xeen/build_world.py --check    compare with the files on disk, write nothing (exit 1 on a difference)
    python3 tools/xeen/build_world.py --rows     print the monster rows for the map lanes (markdown) and stop
    python3 tools/xeen/build_world.py --skip gen_quests   leave a module out (a lane's work in progress);
                                                 its tables are then left as they are on disk
    python3 tools/xeen/build_world.py --only gen_towns    write only the files this module adds to (the modules before
                                                 it run for their ids, nothing after it runs; a file shared with
                                                 an earlier module, readable_items.txt, carries both modules' rows)

Write mode takes an exclusive lock (assets_dev/worlds/xeen/.build_world.lock, flock) and waits for it, so two lanes'
writes never interleave; it writes nothing when any check reports an error. --check and --rows take no lock.

Sources: assets_dev/worlds/xeen/source/ (maps.yml is the orchestrator's; monsters.yml, items.yml, treasure.yml and
map_rows.yml are A2's; towns/ A4's; quests/ and npcs/ A3's). Each module below adds tables to one BuildContext
(tools/xeen/xeenlib.py); the driver checks every id against world.yml's idRanges, the engine tables and the other
worlds' contributions, and stops on any problem before it writes anything. Modules run in this order, so a later one
can read what an earlier one put in ctx.shared (gen_quests reads the item ids gen_items made; gen_towns the topic
ids gen_quests made). A module file that does not exist yet is skipped.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import xeenlib  # noqa: E402

MODULES = ['gen_monsters', 'gen_items', 'gen_maps', 'gen_quests', 'gen_towns']


def run_modules(ctx: xeenlib.BuildContext, skip: list[str], only: str | None = None):
    for name in MODULES:
        if only and MODULES.index(name) > MODULES.index(only):
            print(f'  {name}: not run (--only {only})')
            continue
        if name in skip:
            print(f'  {name}: skipped (--skip)')
            continue
        if not (Path(__file__).resolve().parent / f'{name}.py').exists():
            print(f'  {name}: not present, skipped')
            continue
        module = importlib.import_module(name)
        if not hasattr(module, 'build'):
            ctx.current_module = ''
            ctx.warn(f'{name} has no build(ctx) yet (devdocs/xeen/lanes/A2.md, "Generator interface"): skipped')
            continue
        ctx.current_module = name
        module.build(ctx)
    ctx.current_module = ''
    readable = ctx.shared.get('readable_items') or {}
    table = ctx.tables.get('readable_items.txt')
    written = {xeenlib.parse_int(str(row[0])) for row in (table.rows if table else [])}
    missing = [f'{key} ({item_id})' for item_id, key in sorted(readable.items()) if item_id not in written]
    if missing and 'gen_quests' not in skip and (not only or only == 'gen_quests'):
        ctx.warn(f"readable items without a text from A3 (readable_items.txt): {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='compare with the files on disk; write nothing')
    parser.add_argument('--rows', action='store_true', help='print the monster rows for the map lanes')
    parser.add_argument('--skip', action='append', default=[], choices=MODULES, help='leave this module out')
    parser.add_argument('--only', choices=MODULES, help='write only the files this module adds to')
    args = parser.parse_args()
    if args.only and args.only in args.skip:
        xeenlib.fail(f'--only {args.only} and --skip {args.only} contradict')

    lock = None
    if not args.check and not args.rows:
        # One writer at a time: a second write run waits here until the first has finished writing.
        lock = open(xeenlib.WORLD / '.build_world.lock', 'w')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('waiting for another build_world.py write run (.build_world.lock) ...', flush=True)
            fcntl.flock(lock, fcntl.LOCK_EX)

    try:
        ctx = xeenlib.BuildContext(xeenlib.World())
        run_modules(ctx, args.skip, args.only)
        ctx.ensure_contribution_tables(keep_existing=bool(args.skip or args.only))
        problems = ctx.check()
    except xeenlib.BuildError as error:
        xeenlib.fail(str(error))

    for warning in ctx.warnings:
        print(f'warning: {warning}')
    if problems:
        for problem in problems:
            print(f'error: {problem}', file=sys.stderr)
        xeenlib.fail(f'{len(problems)} problem(s); nothing written')

    if args.rows:
        print(ctx.shared.get('rows_for_map_lanes', '(no monster rows)'))
        return

    outputs = ctx.outputs()
    if args.only:
        outputs = {path: content for path, content in outputs.items() if args.only in ctx.writers.get(path, set())}
        shared = sorted(path.name for path in outputs if len(ctx.writers.get(path, set())) > 1)
        if shared:
            print(f"  shared with an earlier module (written with its rows too): {', '.join(shared)}")
    # A skipped module's files are left alone: only a full build removes files nobody writes any more.
    stale = [] if args.skip or args.only else [path for path in sorted(xeenlib.DATA_TABLES.glob('*'))
                                               if path not in outputs and xeenlib.is_generated(path)]
    changed = []
    for path, content in sorted(outputs.items()):
        old = path.read_text(encoding='utf-8') if path.exists() else None
        if old != content:
            changed.append(path)

    for path in changed:
        print(f"  {'differs' if args.check else 'wrote'}: {path.relative_to(xeenlib.ROOT)}")
    for path in stale:
        print(f"  {'stale' if args.check else 'removed'}: {path.relative_to(xeenlib.ROOT)}")
    rows = sum(len(table.rows) for table in ctx.tables.values())
    print(f'{len(ctx.tables)} tables, {rows} rows, {len(ctx.texts)} other files; '
          f"{len(changed)} {'differ' if args.check else 'changed'}, {len(stale)} stale")

    if args.check:
        sys.exit(1 if changed or stale else 0)

    for path in changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        # A new file renamed over the old one: assets_dev files may share their inode with hard-link scratch roots
        # (cp -al), which must keep the content they were made with.
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(outputs[path], encoding='utf-8')
        temporary.chmod(0o644)
        temporary.replace(path)
    for path in stale:
        path.unlink()


if __name__ == '__main__':
    main()
