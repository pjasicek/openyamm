"""Rebuild from retained selected generations; renewed visual acceptance is required."""
import json
import process, calibrate, tone, materials, package, review_evidence
for key, record in json.loads((process.ROOT/'generation.json').read_text())['batches'].items():
    refs=[r['path'] for r in record['references']]
    process.run(key, record['raw']['path'].split('/')[-1], record['prompt']['path'].split('/')[-1],
                refs[1] if len(refs)>1 else None)
calibrate.run()
tone.run()
materials.run()
package.run()
review_evidence.run()
