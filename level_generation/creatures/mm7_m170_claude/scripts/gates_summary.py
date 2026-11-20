"""Print review/gates_<tag>.json compactly. Args: <tag>"""
import json, sys, os
d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', f'gates_{sys.argv[1]}.json')))
for clip, w in d.items():
    print(clip.ljust(9), ' '.join(f"{k}={v['value']:.2f}@{v['frame']:.0f}" if isinstance(v, dict) else f'{k}={v}' for k, v in w.items() if 'twist' not in k))
