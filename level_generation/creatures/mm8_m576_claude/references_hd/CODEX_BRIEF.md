# Triton HD body references

Scope: built-in image generation for the five body masters; no Meshy submission until the five-view gate and motion selection pass.
Inputs: ../references_native/standing_five_views.png is original native geometry/identity evidence; ../references_native/palette_tiers.png is original palette evidence. Base tier is green, palette 577. Later views also use the selected primary.
Output: unresized, true-alpha 1024x1536 PNGs: 00_three_quarter, 01_front, 02_back, 03_left, 04_right. One full figure per image, same A-pose, soft studio light, near-orthographic. Left profile points the face image-left; right profile points image-right.

Identity: lean athletic but broad-shouldered aquatic male humanoid, long scaled legs, narrow waist, erect posture, green-teal skin. Angular stern hairless fish-humanoid face, small yellow-green eyes, a single median fin/spine crest swept back with short side fins. Dark charcoal rigid breastplate sections with pale silver-green edges, inverted V pale upper collar and X-shaped back straps, narrow vertical violet-blue chest inset. Pointed shoulder plates with swept fins/spikes, upper-arm bands; green ridged/scaled forearms and legs with outer elbow and outer thigh fins, narrow long bare feet. Preserve native coverage: no boots, trousers, skirt, cape, beard or added armour. Native tiny digits and crest ray count are ambiguous; infer five humanlike fingers and coherent connected fin rays, record inference.

Body pose: arms 35 degrees from vertical, separated open fingers, palms forward, legs separated. No trident in BODY masters, it is a REQUIRED separate rigid prop later, carried in anatomical LEFT hand. No shield. Keep all fin tips and feet inside canvas. No background, shadow, floor, text or props.

Gate: inspect identity/proportions, palette, armour boundaries, asymmetry, fingers, crest consistency, true alpha, frame margins and matching poses across every view. Save generation_runs.json with full prompt, input/output hashes, selected state and reason; selected_views_review.png after all five pass. No native enlargement goes to Meshy.
