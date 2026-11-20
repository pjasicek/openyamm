#!/usr/bin/env python3
"""Where a thread's CPU time goes, from a perf capture, without perf report (see tools/PERF_PROFILING.md).

Reads the text written by

    perf script -i capture.data --no-inline -F tid,ip,sym > capture.txt

and prints, for one thread, each function's inclusive and own share. `--no-inline` matters: without it perf resolves
inlined frames through addr2line, which takes minutes at full CPU on this binary.

    perf_stacks.py capture.txt                         threads by share, then the busiest thread's functions
    perf_stacks.py capture.txt --thread 1              the second busiest thread (the main thread, as a rule)
    perf_stacks.py capture.txt --thread 1 --under renderGameplayHudArt
                                                       only what that function calls
    perf_stacks.py capture.txt --thread 1 --children GameplaySoloHud::renderHud
                                                       its direct callees, each with what they call
    perf_stacks.py capture.txt --thread 1 --callers tolower
                                                       who calls it, four frames up
    perf_stacks.py a.txt --thread 1 --frame-us 726     shares as microseconds of a frame (the thread's busy time per
                                                       frame, e.g. FramePerf's avg_render_callback_us)
"""
import argparse
import collections
import re
import sys


def clean(symbol):
    symbol = re.sub(r'\+0x[0-9a-f]+$', '', symbol)
    symbol = symbol.replace('(anonymous namespace)::', '').replace('OpenYAMM::', '')
    return re.sub(r'\(.*', '', symbol)[:100] or '[unknown]'


def load(path):
    """Samples per thread id; each sample is its stack, innermost frame first."""
    samples = collections.defaultdict(list)
    stack = None
    for line in open(path, errors='replace'):
        if not line.strip():
            continue
        if not line[0].isspace():
            stack = []
            samples[line.split()[0]].append(stack)
            continue
        match = re.match(r'\s+[0-9a-f]+\s+(.*)$', line)
        if match and stack is not None:
            stack.append(clean(match.group(1)))
    return samples


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path')
    parser.add_argument('--thread', type=int, default=0, help='thread by share of samples, 0 the busiest')
    parser.add_argument('--under', help='count only frames called by the outermost function containing this text')
    parser.add_argument('--children', help='group by the direct callees of the function containing this text')
    parser.add_argument('--callers', help='list the call chains above the function containing this text')
    parser.add_argument('--top', type=int, default=40)
    parser.add_argument('--frame-us', type=float, default=0.0, help="the thread's busy microseconds per frame")
    args = parser.parse_args()

    samples = load(args.path)
    order = sorted(samples, key=lambda thread: -len(samples[thread]))
    total = sum(len(stacks) for stacks in samples.values())
    if not total:
        sys.exit('no samples: was the file written by perf script -F tid,ip,sym?')
    print('threads:', ', '.join(f'{index}: tid {thread} {100 * len(samples[thread]) / total:.1f}%'
                                for index, thread in enumerate(order[:5])))
    stacks = samples[order[args.thread]]
    count = len(stacks)

    def share(value):
        return f'{value * args.frame_us / count:7.1f}us' if args.frame_us else f'{100 * value / count:6.2f}%'

    if args.callers:
        chains = collections.Counter()
        for stack in stacks:
            for index, frame in enumerate(stack):
                if args.callers in frame:
                    chains[' <- '.join(stack[index + 1:index + 5])] += 1
                    break
        for chain, value in chains.most_common(args.top):
            print(share(value), chain)
        return

    if args.children:
        callees = collections.Counter()
        for stack in stacks:
            matches = [index for index, frame in enumerate(stack) if args.children in frame]
            if matches:
                callees[stack[matches[-1] - 1] if matches[-1] > 0 else '(itself)'] += 1
        print(share(sum(callees.values())), 'in all')
        for callee, value in callees.most_common(args.top):
            print(share(value), callee)
        return

    inclusive = collections.Counter()
    own = collections.Counter()
    for stack in stacks:
        if args.under:
            matches = [index for index, frame in enumerate(stack) if args.under in frame]
            if not matches or matches[-1] == 0:
                continue
            stack = stack[:matches[-1]]
        if stack:
            own[stack[0]] += 1
        for frame in set(stack):
            inclusive[frame] += 1
    print('inclusive    own      function')
    for frame, value in inclusive.most_common(args.top):
        print(share(value), share(own.get(frame, 0)), frame)


if __name__ == '__main__':
    main()
