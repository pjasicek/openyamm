# Day of the Gods front halo

The Day of the Gods overlay now shows the front, lower arc of the gold halo. The far arc that previously crossed
the skull's crown has been removed. The original atlas UV rectangle and 128-square panel placement remain unchanged.

![Native game comparison: before on the left, after on the right](comparison_native.png)

The mounted asset is [obsidian_buff_skull_effects.png](../../../assets_dev/engine/icons_x2/obsidian_buff_skull_effects.png).
The edit used built-in imagegen. Its [exact accepted prompt](prompts.json) requests removal of the upper semicircle
while retaining the original front arc's registration, tilt, thickness, gold material and soft glow.
The first isolated-arc return was rejected because it changed scale and thickness; the accepted edit used the
complete atlas as its target to hold the layout steady.

Only the returned halo rectangle `[29, 603, 501, 898]` was copied into the runtime atlas. All 1,433,624 pixels outside
that rectangle are identical to the prior runtime asset, including eyes, garland, Torch Light and Feather Fall.
The atlas is still 1536 × 1024 RGBA with 0644 permissions. [Validation](validation.json) records exact pixel bounds
and asset hashes. [The original atlas](skull_effects_before.png) and
[the complete accepted return](skull_effects_imagegen_return.png) are retained here.

Native captures use the normal desktop executable and engine PNG readback at 1600 × 900 with isolated MM6 saves:
[before](native_day_only_before.png), [after](native_day_only_after.png), and
[with Stoneskin](native_stoneskin_after.png). The runs use NVIDIA OpenGL 3.3 through SDL Wayland.
The private fixtures change only buff durations in a copy of the existing all-buffs fixture; normal saves remain untouched.

No renderer or gameplay code changed. Reload the game to refresh the cached atlas.
