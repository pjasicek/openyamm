import os
import csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
_rows = list(csv.DictReader(open(ROOT + '/devdocs/maw/data/balance_golden.csv')))
def spell_ratio(cfg, L):
    best = min((r for r in _rows if r['config'] == cfg and r['party_count'] == '1' and r['austerity'] == '0'),
               key=lambda r: abs(int(r['level'])-L))
    return float(best['spell_power'])/float(best['power'])
