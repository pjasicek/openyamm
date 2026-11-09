"""Rebuild from accepted raw sheets without automatically accepting changed artwork."""
import json
import process
import refine_tone
import materials
import package
import review_evidence

for key, record in json.loads((process.ROOT/'generation.json').read_text())['batches'].items():
    identity = None if key == 'identity' else 'raw/identity_v2.png'
    process.run(key, record['raw']['path'].split('/')[-1],
                record['prompt']['path'].split('/')[-1], identity)
refine_tone.run()
materials.run()
package.run()
review_evidence.run()
