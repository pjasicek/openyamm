#!/usr/bin/env python3
"""Compares what two co-op games printed at each beat of tools/coop_two_machines/run.sh session.

    compare_states.py <host console lines> <guest console lines>

A beat begins at a game's `coop say <host|guest> at <label>` and holds the lines of `coop show`, `coop net`,
`actor count`, `time` and `coop check` that follow. The guest is player 1 in the host's game and player 0 in its own.
Prints one line per beat and what differs; ends with status 1 when anything does.
"""
import re
import sys

PLACE_TOLERANCE = 64  # world units: a walking player's place is news a moment old
TIME_TOLERANCE_MINUTES = 10


def beats(path, side):
    result = {}
    label = None
    for line in open(path, errors='replace'):
        line = line.rstrip()
        marker = re.match(r'> coop say (host|guest) at (\S+)', line)
        if marker:
            label = marker.group(2) if marker.group(1) == side else None
            if label:
                result[label] = []
            continue
        if label and not line.startswith('Average FPS'):
            result[label].append(line)
    return result


def read(lines, side):
    """What a beat's lines say: the guest's character, the host's character, the monsters, the day."""
    facts = {}
    own = r'player 0 \(local\) at (-?\d+) (-?\d+) (-?\d+) hp (-?\d+)/(\d+) gold (\d+)( down)?'
    for line in lines:
        if side == 'host':
            mine = re.match(own, line)
            if mine:
                facts['host place'] = tuple(int(v) for v in mine.group(1, 2, 3))
                facts['host hp'] = int(mine.group(4))
            other = re.match(r'player 1 at (-?\d+) (-?\d+) (-?\d+) hp (-?\d+)/(\d+) gold (\d+)( down)?', line)
            if other:
                facts['guest place'] = tuple(int(v) for v in other.group(1, 2, 3))
        else:
            mine = re.match(own, line)
            if mine:
                facts['guest place'] = tuple(int(v) for v in mine.group(1, 2, 3))
            other = re.match(r'player 0 .* hp (-?\d+)/(\d+) at (-?\d+) (-?\d+) (-?\d+)', line)
            if other:
                facts['host place'] = tuple(int(v) for v in other.group(3, 4, 5))
                facts['host hp'] = int(other.group(1))
        count = re.match(r'181 Pirate: (.*)', line)
        if count:
            facts['pirates'] = count.group(1)
        check = re.match(r'player (\d) (\w+) is (-?\d+)', line)
        if check:
            facts['guest ' + check.group(2)] = int(check.group(3))
        date = re.match(r'Current date: (.*)', line)
        if date:
            facts['time'] = date.group(1).split(' (')[0].strip()
        net = re.match(r'(joined as player \d+|hosting), map revision (\d+)', line)
        if net:
            facts['map revision'] = int(net.group(2))
    return facts


def clock_minutes(text):
    """Minutes of the day from '... 9:14 AM', or None."""
    clock = re.search(r'(\d+):(\d\d) ?([AP]M)', text)
    if not clock:
        return None
    hour = int(clock.group(1)) % 12 + (12 if clock.group(3) == 'PM' else 0)
    return hour * 60 + int(clock.group(2))


def differs(name, a, b):
    if a is None or b is None:
        return True
    if name == 'time':
        # The date the same; the clock within what the games' two prints are apart (a game minute is half a second).
        minutes = clock_minutes(a), clock_minutes(b)
        day = [re.sub(r'\d+:\d\d ?[AP]M', '', v) for v in (a, b)]
        return day[0] != day[1] or None in minutes or abs(minutes[0] - minutes[1]) > TIME_TOLERANCE_MINUTES
    if name.endswith('place'):
        return max(abs(x - y) for x, y in zip(a, b)) > PLACE_TOLERANCE
    return a != b


def main():
    host = beats(sys.argv[1], 'host')
    guest = beats(sys.argv[2], 'guest')
    bad = 0
    for label in host:
        if label not in guest:
            print(f'{label:14} the guest printed nothing')
            bad += 1
            continue
        h = read(host[label], 'host')
        g = read(guest[label], 'guest')
        names = sorted(set(h) | set(g))
        wrong = [n for n in names if differs(n, h.get(n), g.get(n))]
        same = ', '.join(f'{n} {h[n]}' for n in names if n not in wrong
                         and n in ('guest hp', 'guest gold', 'guest bag_items', 'guest down', 'time', 'pirates',
                                   'map revision'))
        print(f'{label:14} {"same" if not wrong else "DIFFERS"}: {same}')
        for n in wrong:
            print(f'{"":14}   {n}: host says {h.get(n)}, guest says {g.get(n)}')
        bad += len(wrong)
    for label in guest:
        if label not in host:
            print(f'{label:14} the host printed nothing')
            bad += 1
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
