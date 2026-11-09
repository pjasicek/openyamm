# Visual review — mfp

Reviewed native action references, ten raw sheets, all 59 registered base frames and mask overlays, all three
standing appearances, native/enhanced pose contacts, light/dark contour patches and representative viewer frames.
The long segmented braid, forehead jewelry, gold bangles, short blouse, patterned wrap skirt and flat sandals
remain recognizable across views. The attack retains its right-hand knife and braid swing; hit/fidget/death keep
empty hands. The collapse and outstretched prone body retain native floor placement and width.

The cyan matte protects the intentionally pink/magenta skirt. Extraction, edge RGB unmixing and narrow-contour
cleanup remove its visible cyan fringe without changing alpha during final RGB cleanup. Every cleaned, cropped
and atlas-extracted frame has zero candidates above the configured spill threshold; inspected worst patches on
light/dark backgrounds show no obvious cyan halo. The blouse-only mask leaves skin, jewelry, skirt and blade
unchanged in red/blue variants. All frames were checked via the combined mask contact.

Browser captures show the blue mirrored profile walk, red attack with mask overlay and green prone body against
black. Their native and restored baselines agree. Original timing and frame stepping are available in review.html.

Remaining approximations: reconstructed facial details and skirt motifs vary subtly between poses; the restored
skin and cloth have warmer, softer shading than the native near-black shadows. The braid trajectory is similar
but not pixel-identical, especially during collapse. The fidget remains deliberately subtle. Alpha is inferred from
a matte, not original 3D coverage. These are accepted offline restoration limits.
