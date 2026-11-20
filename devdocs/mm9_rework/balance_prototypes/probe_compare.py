"""Compare openyamm_balance_probe results, each MM9 chapter against the matching MM7 stage. Usage: probe_compare.py <out.tsv>"""
import csv, sys
rows = {(x['world'], int(x['stage'])): x for x in csv.DictReader(open(sys.argv[1]), delimiter='\t')}
f = lambda x, k: float(x[k])
for s in range(1, 6):
    a, b = rows[('mm7', s)], rows[('mm9', s)]
    print(f"ch{s}: party L{b['party_level']} (MM7 L{a['party_level']}), pack {f(b,'pack'):.2f} ({f(a,'pack'):.2f}) | "
          f"clear {f(b,'clear_seconds'):5.1f}s vs {f(a,'clear_seconds'):5.1f}s x{f(b,'clear_seconds')/f(a,'clear_seconds'):.2f} | "
          f"damage {100*f(b,'damage_share'):5.1f}% vs {100*f(a,'damage_share'):5.1f}% x{f(b,'damage_share')/f(a,'damage_share'):.2f} | "
          f"deaths/pack {f(b,'deaths'):.2f} vs {f(a,'deaths'):.2f}")
