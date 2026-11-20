# MM8 Lizardman Warrior HD references

Image generation scope: write only into this references_hd folder; no Meshy submissions at this stage. Native inputs in ../.. /references: identity.png (original five-view anatomy), native_variants.png (palettes 405/406/407), native_a_v0.png (equipment and attack). Base is tier A/405, green mantle.

Generate five separate unresized 1024×1536 RGBA images: 00_three_quarter.png, 01_front.png, 02_back.png, 03_left.png (creature left profile, muzzle toward image left), 04_right.png (right profile, muzzle toward image right). Use the selected primary as identity input for the other four. Same A-pose, anatomy, materials and proportions throughout. Sword omitted only for the body generation and remains required for delivery.

Inspect each against native: head/muzzle/crest, skin and mantle palette, slim legs, three main toes, long tail, mantle and bracers, clear limb gaps, complete margins and alpha. Native hands are closed/occluded: five digits are a labelled reconstruction, not a recovered count. Never submit native/enlarged/restored frames to Meshy. Save prompts, input SHA256, actual return paths, selected/rejected reasons in generation_runs.json.

Primary prompt: see 00_prompt.txt.
