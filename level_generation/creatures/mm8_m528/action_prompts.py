import json
from process import ROOT
batches=json.loads((ROOT/'batches.json').read_text())
details={
 'native_a_v0_1':'The first FIVE cells have a very bright white flashing core, with a broad white-yellow luminous area obscuring much of the dark smoke. Match each native flash area and brightness closely; do not replace it with the quiet identity\'s dark core and single horizontal streak. Preserve the native orange-brown outer core rim where visible. Last TWO cells return to a dark flattened core and have cool blue-violet/white tiny electrical sparks mixed with the ivory filaments; preserve those blue-violet accents.',
 'native_a_v0_2':'The native flattened smoky core rotates/bobs while pale ivory electrical filaments move around it. Early cells retain small cool blue-violet accents in the electrical sparks; preserve them. Preserve each native core location, aspect and sparse changing sparks.',
 'native_d_v0_0':'This is the native death sequence. Cells 1-2 retain the dark smoky core; cell 3 has a white/tan inner flash; cell 4 blooms into an irregular bright tan-white burst; cells 5-6 break into native rounded brown smoke puffs with bright white-tan centers. Preserve these transformations and the exact individual puff locations. Do not put an intact quiet core or central streak into cells where the native core has broken apart.',
 'native_d_v0_1':'These are native dissipating death smoke frames. Preserve the separate irregular rounded BROWN smoke puffs with their tan/white glowing centers, each puff\'s position and progressive reduction in opacity/mass. Native pale electrical wisps fade away between the puffs. Last cell has ONLY a few sparse small electrical wisps and no intact smoky core. Do not turn puffs into rocks, create a continuous sphere or add the identity\'s core/streak.',
 'native_d_v0_2':'These final native death frames contain ONLY a few sparse, tiny pale ivory electrical wisps which fade to a last tiny glint. Preserve their exact relative sizes and positions, the mostly EMPTY canvas, and the number of clusters in each cell. No core, smoke ball, horizontal streak or full Wisp may be added. Do not enlarge these remnants to fill their cells.',
}
for key,b in batches.items():
 if key=='identity':continue
 detail=details.get(key,'Preserve the native dark charcoal smoke, pale gold-white horizontal streak and individual ragged pale ivory electrical filaments. Preserve the exact silhouette and changing distribution of wisps in every native frame; no orange/red tint on these pale filaments.')
 prompt=f'''Use case: identity-preserve. Restore native Might and Magic VIII Will-o'-Wisp animation sprites into fine detailed raster artwork.
Input 1: authoritative native artwork, colors, pose, brightness, occupied area, layout and individual frame differences. Input 2: accepted restored identity, supporting fine-detail/material treatment only; never force its pose or quiet-state brightness onto different native action frames.
Exact layout: {b['columns']} columns by {b['rows']} rows, {len(b['frames'])} occupied equal square cells in row-major order: {', '.join(b['frames'])}. Unoccupied cells remain empty. Maintain each original pose at the same relative scale and position inside its native cell. No individual recentering or silhouette size normalization.
{detail}
Reconstruct coherent fine smoke and branching electrical detail instead of enlarged square pixel blocks. Preserve the original visual mass, every light/dark pattern, sparse/disconnected features and native colors. No faces, eyes, equipment, chrome sphere, added halo or ground shadow. No duplicated poses, labels, text or grid. Keep all native margins and all sparks within their own cell.
Use perfectly flat pure magenta RGB(255,0,255) in every empty background pixel, with no gradient, checkerboard, shadows, glow bleeding onto the background or magenta bounce. Preserve the native warm and cool foreground colors.
'''
 (ROOT/f'prompts/{key}_v3.txt').write_text(prompt)
print('Prepared action-specific prompts preserving native flashes, cool sparks and disintegrating smoke.')
