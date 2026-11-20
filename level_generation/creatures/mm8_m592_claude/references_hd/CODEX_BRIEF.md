# MM8 Plane Guardian HD references

Scope: generate faithful reference images into references_hd only. The full production task continues separately.
Authority: references/anatomy_details.png and the original native action sheets; enlarged pixels provide anatomical evidence only.

Five unresized RGBA body masters: 00_three_quarter.png, 01_front.png, 02_back.png, 03_left.png, 04_right.png.
Target 1024x1536 portrait. Left profile faces image right; right profile faces image left.
The selected primary fixes proportions, materials and the adapted A-pose. Preserve that identity in all views.
Head turnaround: front, three-quarter, profile and back, bust only; request 1254 square, record actual output dimensions.

Use primary_prompt.txt as the primary brief. Record every exact prompt, input SHA256, returned path, dimensions,
selection and review in generation_runs.json. Check three claws per hand, three short toes, fanged muzzle, low
head, gold mane continuing down the back, bent legs, no tail/horns/wings/equipment, alpha and uncropped framing.
Only generated selected HD masters may be sent to Meshy; never native/restored/enlarged sprite evidence.
