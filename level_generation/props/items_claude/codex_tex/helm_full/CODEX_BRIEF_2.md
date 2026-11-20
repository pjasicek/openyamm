# Codex brief: paint the views of the Full Helm (MM6) 3D model (texture source), part 2

Scope: image generation only. Write ONLY into `level_generation/props/items_claude/codex_tex/helm_full/`. Do not edit
any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design of the
item, three-quarter view: the design, colour and material authority), `icon_x8.png` (the original game icon) and
one `guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_back.png` over `guide_back.png` (the item seen from the back)

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
band, opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the
surface materials of the design reference onto that shape: blackened dark-grey steel plates with subtle hammered texture and light wear on the edges, brass/gold trim on the rim and band edges, small round dark-steel rivets, a dark (near black) interior visible through the face slit.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections (show metal as its base colour with only a
faint sheen), no rim light, no background, no floor.

Write `generation_runs_2.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light with no shadows or hot highlights; transparent background.
