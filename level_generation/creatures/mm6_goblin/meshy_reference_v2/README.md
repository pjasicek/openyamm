# Meshy main / left / back / right upload set

Use this set instead of v1. Prepared with built-in imagegen on 2026-09-23; no Meshy job submitted.
Main, back and right reuse the selected v1 art. Left is a new opposite-side view, preserving the asymmetric
pouch/earring placement rather than mirroring the right-side image.

| Meshy slot | File | Visible direction |
| --- | --- | --- |
| Main large upload area | `main.png` | Front, facing camera |
| Left | `left.png` | Nose and toes point left; anatomical left side, no near-side pouch or earrings |
| Back | `back.png` | Rear |
| Right | `right.png` | Nose and toes point right; anatomical right side with pouch and earrings |

All four PNGs are 1024×1536. Upload individual images to their matching slots. The ZIP contains the four images,
these instructions and both prompt files. The previous three-quarter image is not part of this set.

## Settings for the supplied screenshot (`test_img/2019.png`)

- Keep **High Detail → Meshy 7.1 – Flagship**.
- Turn **Multi-view ON**.
- Turn **Image Enhancement OFF**.
- Turn **Pose ON**, then choose **A-Pose**.
- For a cheaper first shape check, choose **Standard** if available. The screenshot currently selects
  **Ultra 2K** and shows **25 credits**; check the actual quote after changing settings.
- **Texture OFF** is appropriate for that initial geometry review. Texture the accepted model before rigging.
- Keep **Split OFF** for the initial body experiment.

No general text field appears in the screenshot: the images drive this generation. `meshy_prompt.txt` is optional
general guidance if another panel offers it. `texture_prompt.txt` is for a texture prompt field later.

The body is deliberately unarmed; attach the original sword separately after modeling/rigging.
Visual review checked view direction, complete figure, main costume/pose and pouch/earring sidedness. Small
jewelry/rivet details remain approximate, including two visible hoops in the right profile versus three in the
main image. Use main as the identity reference. These are AI reconstruction references, not calibrated views
rendered from an existing mesh. Inspect the resulting 3D likeness before further paid processing.

Source provenance for reused views: `../meshy_reference_v1/sources.json` and `../meshy_reference_v1/prompts/`.
Exact new left-view prompt: `prompts/left.txt`. Selected file hashes: `sources.json`.
