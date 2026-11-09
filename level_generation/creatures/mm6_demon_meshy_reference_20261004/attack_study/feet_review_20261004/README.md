# Native MM6 demon attack: feet and lower legs

Examined all six original attack frames, `dmnatka0` through `dmnatkf0`, at their unchanged native placement.
Each hold is 125 ms; the cycle is 750 ms. Anatomical right is **screen left** in this frontal view.

**The feet are not completely stationary.** They remain in the same general stance without a clear step,
but the right foot changes its projected orientation noticeably during the attack. The later poses support a
small inward pivot and leg adjustment, rather than six identical locked foot transforms.

| Native poses | Observation |
| --- | --- |
| A | Right foot points outward toward screen left; left foot is more frontal. |
| B–C | Right ankle/foot shifts a few pixels toward screen right. Left foot remains very similar. |
| D–E | Right foot becomes narrower and more forward-facing; its visible claws shift inward. The hips/legs adjust as the torso dips and twists. This supports modest knee/ankle flex, but the single frontal view cannot establish exact joint angles. |
| F | Right foot returns toward its initial outward orientation. Left foot retains its stance. |

Within the isolated foot band at native y=310–329, the right-foot silhouette widths are **54, 53, 53, 45, 46,
55 pixels** for A–F. The left-foot widths are **46, 46, 46, 47, 46, 46 pixels**. The right-foot change affects
the alpha silhouette as well as the visible claws, so it is more than a lighting change. Small left-foot
outline/claw differences and shading changes remain; that foot is not pixel-identical across the cycle either.

There is no clear lifted whole foot, relocated stance, walking step, or deliberate toe curling. The sprites end
at y=329 and show no independent floor, so exact sole contact and hidden heel motion cannot be proven.
Do not infer a specific ankle/knee rotation axis or degree value from this one view.

For the 3D attack, retain ground support and the overall footprint, allow the right foot to pivot slightly with
the body turn, and allow modest leg flex to accommodate the dip. Avoid treating every foot bone as immobile;
also avoid inventing a step or animating the long claws independently. This is a source finding and an
authoring recommendation; **the existing 3D animation has not been changed in this check**.

## Evidence

- [Aligned original feet](native_feet_aligned.png): common crop and 6× nearest-neighbor enlargement.
- [Aligned lower body](native_legs_aligned.png): includes hips, knees, ankles and feet.
- [Silhouette comparison against A](native_feet_silhouette_comparison.png): cyan is A only, orange is the current frame only.
- [Exact native-timing playback](native_legs_playback.png): APNG, six 125 ms frames.
- [GIF playback](native_legs_playback.gif): alternating 120/130 ms holds for GIF's timing limit, 750 ms total.
- [Pixel measurements and source verification](pixel_measurements.json).

The native PNGs match the preserved original BMPs exactly in colour and index-zero alpha, and all six BMP
hashes match the original source manifest. All offsets are `[0,46,354,330]` on a 354×330 logical canvas.
Nothing was independently fitted, recentered, restored or synthesized for these comparisons. Central tail
movement and stray hand claws in the wider crops are not foot movement. Run `analyze_native_feet.py` to
reproduce the diagnostic plates and measurements; it reads the originals without changing them.
