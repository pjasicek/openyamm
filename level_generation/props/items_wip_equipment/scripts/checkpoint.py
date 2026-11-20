"""Refresh the equipment-only progress counters and CSV from retained receipts and decisions."""
import csv
import json
from pathlib import Path

project = Path(__file__).resolve().parents[1]
ledger = json.loads((project / 'ledger.json').read_text())
jobs = json.loads((project / 'meshy/creature_3d_progress.json').read_text())['meshy']['jobs']
budget = json.loads((project / 'budget_request.json').read_text())
handoff = json.loads((project / 'handoff.json').read_text())
spent = sum(job.get('consumed_credits', 0) for job in jobs.values())
committed = sum(job.get('reserved_credits', 0) for job in jobs.values())
assert spent <= committed <= budget['approved_credits'] == 415
for entry in ledger:
    entry['master_ready'] = (project / 'meshy' / entry['geometry_design'] / 'references_hd/00_three_quarter.png').exists()
    if entry.get('final_decision'):
        continue
    if entry['replacement_installed']:
        entry['next_action'] = 'Native review pending' if entry.get('native_review_pending') else 'Retain reviewed replacement'
    elif entry['icon'] == '7item116':
        entry['next_action'] = 'Repair authored shin plate/lining geometry; no paid retry approved'
    elif (project / 'work/codex_tex' / (entry['design'] + '.blend')).exists():
        entry['next_action'] = 'Review geometry, then guide paint and material masks'
    elif entry['geometry_design'] + '_st_v1' in jobs:
        entry['next_action'] = 'Poll/download Smart Topology, then prepare and review geometry'
    elif entry['master_ready']:
        entry['next_action'] = 'Review HD master, then submit approved 5-credit Smart Topology job'
    else:
        entry['next_action'] = 'Generate and review HD master within approved shape list'
budget.update(spent_credits=spent, reserved_credits=committed)
handoff.update(spent_meshy_credits=spent, reserved_meshy_credits=committed, submitted_jobs=len(jobs),
               hd_masters_ready=len(list((project / 'meshy').glob('equipment_*/references_hd/00_three_quarter.png'))),
               shapes_downloaded=sum(bool(job.get('downloads')) for job in jobs.values()),
               replaced=sum(entry['replacement_installed'] for entry in ledger),
               kept=sum(entry['decision'] == 'keep' for entry in ledger),
               deferred=sum(entry['decision'] == 'deferred' for entry in ledger),
               installed_models=[entry['icon'] for entry in ledger if entry['replacement_installed']])
if handoff.get('status') not in ('stopped_at_user_request', 'coordinator_finish_complete'):
    handoff['pending'] = ['Review all candidate geometry; repair or record specific deferrals',
                          'Paint exact guides/material masks, bake and visually review remaining candidates',
                          'Install accepted owned exports separately; finish representative native checks']
for filename, data in [('ledger.json', ledger), ('budget_request.json', budget), ('handoff.json', handoff)]:
    (project / filename).write_text(json.dumps(data, indent=2) + '\n')
fields = ['icon', 'decision', 'replacement_installed', 'master_ready', 'reason', 'next_action', 'design',
          'geometry_design', 'review_sheet', 'binding_length']
with (project / 'ledger.csv').open('w', newline='') as output:
    writer = csv.DictWriter(output, fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(ledger)
print({key: handoff[key] for key in ['replaced', 'deferred', 'hd_masters_ready', 'submitted_jobs',
                                     'shapes_downloaded', 'spent_meshy_credits', 'reserved_meshy_credits']})
