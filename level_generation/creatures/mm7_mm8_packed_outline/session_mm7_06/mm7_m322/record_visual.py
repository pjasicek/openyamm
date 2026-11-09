"""Record only evidence explicitly inspected during this local session."""
import argparse
import datetime
import session_workflow as w


def record(family, paths, note):
    root = w.SESSION / family
    target = root / 'review/visual_log.json'
    log = w.read(target) if target.exists() else {'reviewer': 'Codex', 'inspected': {}}
    for relative in paths:
        path = root / relative
        log['inspected'][w.rel(path)] = dict(sha256=w.sha(path), note=note,
            reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    w.write(target, log)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    parser.add_argument('note')
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    record(args.family, args.paths, args.note)
