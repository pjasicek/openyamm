# Material pass, MM6 batch

Converted GLBs for review; **nothing is installed**. Inputs are the pre-pass sources in
`../backup_pre_material_pass/` (the three pilots are already installed and copied from `../pilot/`).
Install after review with `tools/install_model.py material_pass/batch/<name>.glb --world mm6`; revert
with `../revert.sh [name ...]`. Contact sheets: `contact_sheet_*.png` (old / new, front, neutral key and
dim indoor light).

Processed 33, skipped 56 of 89.

## Processed

| Model | Class maps | Keep classes | Metal (median sRGB luminance per material) | Flags |
|---|---|---|---|---|
| mm6_arc1 | mm6_arc1_codex/textures/arc1_material_classes.png | arc1_metal_rough_retex: skin, cloth | no metal | - |
| mm6_arc1_bow | mm6_arc1_codex/textures/bow/material_classes_1k.png | - | metal_rough_1k_bow: 85 | - |
| mm6_bar1 (pilot) | material_pass/pilot/bar1_head_material_classes.png<br>mm6_bar1_claude/textures/bar1_material_classes.png | *: skin | bar1_metal_rough_1k_head_atlas: 161-166 | - |
| mm6_ckt (partly) | mm6_ckt_claude/textures/ckt_material_classes.png | - | no metal | - |
| mm6_cob | mm6_cob_claude/textures/cob_material_classes.png | - | no metal | - |
| mm6_drag | mm6_drag_reduce_claude/textures/drag_body_material_classes.png<br>mm6_drag_reduce_claude/textures/drag_head_material_classes.png | drag_body_metal_rough_2k_head_atlas: skin | no metal | - |
| mm6_drg1 | mm6_drg1_claude/textures/drg1_body_material_classes.png<br>mm6_drg1_claude/textures/drg1_head_material_classes.png<br>mm6_drg1_claude/textures/drg1_wings_material_classes.png | drg1_body_metal_rough_2k: skin; drg1_head_metal_rough_2k: skin; drg1_wings_metal_rough_2k: skin | no metal | - |
| mm6_dwa1 | mm6_dwa1_codex/textures/dwa1_head_material_classes_1k.png<br>mm6_dwa1_codex/textures/dwa1_material_classes_1k.png | - | dwa1_metal_rough_1k_head_atlas: 71 | - |
| mm6_dwa1_axe | mm6_dwa1_codex/textures/axe/material_classes_1k.png | - | metal_rough_1k_axe: 57 | - |
| mm6_fgt | mm6_fgt_claude/textures/fgt_head_material_classes.png<br>mm6_fgt_claude/textures/fgt_material_classes.png | fgt_metal_rough_1k_head_atlas: skin, fur, cloth | fgt_metal_rough_1k_head_atlas: 91-98 | - |
| mm6_gob2 (pilot) | mm6_gob2_reduce_claude/textures/gob2_head_material_classes.png<br>mm6_gob2_reduce_claude/textures/gob2_material_classes.png | - | gob2_metal_rough_1k_head_atlas: 116 | - |
| mm6_hrp | mm6_hrp_claude/textures/hrp_body_material_classes.png<br>mm6_hrp_claude/textures/hrp_head_material_classes.png<br>mm6_hrp_claude/textures/hrp_wings_material_classes.png | hrp_head_metal_rough_1k: skin, fur; hrp_body_metal_rough_1k: skin, fur; hrp_wings_metal_rough_1k: fur | no metal | - |
| mm6_hyd | mm6_hyd_claude/textures/hyd_body_material_classes.png<br>mm6_hyd_claude/textures/hyd_head_material_classes.png | - | no metal | - |
| mm6_jak1 | mm6_jak1_codex/textures/jak1_body_material_classes.png<br>mm6_jak1_codex/textures/jak1_head_material_classes.png | body_metal_rough_head_atlas: skin | body_metal_rough_head_atlas: 132 | - |
| mm6_jak1_staff | mm6_jak1_codex/textures/staff/material_classes_1k.png | Staff_round4_metal_rough: cloth | Staff_round4_metal_rough: 31 | HookedStaff_A: metal median luminance 31 (very dark) |
| mm6_kni (pilot) | mm6_kni_reduce_claude/textures/kni_material_classes.png | - | kni_body_mr_1k: 51-52 | - |
| mm6_kni_sword | mm6_kni_codex/textures/sword_round1/material_classes_1k.png | - | metal_rough_1k: 98 | - |
| mm6_lzd_bow | mm6_lzd_codex/textures/bow/material_classes_1k.png | - | metal_rough_bow: 51 | - |
| mm6_med | mm6_med_claude/textures/med_body_material_classes.png<br>mm6_med_claude/textures/med_head_material_classes.png | med_body_metal_rough_1k_head_atlas: skin, cloth | med_body_metal_rough_1k_head_atlas: 169-170 | - |
| mm6_mep | mm6_mep_codex/textures/mep_head_material_classes.png<br>mm6_mep_codex/textures/mep_material_classes.png | - | no metal | - |
| mm6_mep_staff | mm6_mep_codex/textures/mep_staff_material_classes.png | - | no metal | - |
| mm6_mer1 | mm6_mer1_codex/textures/mer1_body_material_classes.png<br>mm6_mer1_codex/textures/mer1_head_material_classes.png | MerchantHeadL0_A_specular_roughness_metal: skin, fur; MerchantHandsL0_A_specular_roughness_metal: skin, cloth; MerchantL0_A_specular_roughness_metal: skin, cloth | MerchantL0_A_specular_roughness_metal: 19-62<br>MerchantHandsL0_A_specular_roughness_metal: 191 | MerchantL0_B: metal median luminance 19 (very dark)<br>MerchantL0_C: metal median luminance 26 (very dark)<br>MerchantL1_B: metal median luminance 19 (very dark)<br>MerchantL1_C: metal median luminance 26 (very dark)<br>MerchantL2_B: metal median luminance 19 (very dark)<br>MerchantL2_C: metal median luminance 26 (very dark)<br>MerchantL3_B: metal median luminance 19 (very dark)<br>MerchantL3_C: metal median luminance 26 (very dark) |
| mm6_mfp_knife | mm6_mfp_codex/textures/knife/material_classes.png | knife_metal_rough: skin | no metal | - |
| mm6_min1 | mm6_min1_codex/textures/min1_body_material_classes.png<br>mm6_min1_codex/textures/min1_head_material_classes.png | - | min1_body_metal_rough_head_atlas: 129 | - |
| mm6_min1_axe | mm6_min1_codex/textures/axe_material_classes.png | - | axe_metal_rough_axe: 71 | - |
| mm6_natf | mm6_natf_codex/textures/natf_body_material_classes.png<br>mm6_natf_codex/textures/natf_head_material_classes.png | - | Body_l0_r0.7800_natf_body_metal_rough_head_atlas: 128 | - |
| mm6_natf_shield | mm6_natf_codex/textures/natf_shield_material_classes.png | - | no metal | - |
| mm6_natm | mm6_natm_claude/textures/natm_head_material_classes.png<br>mm6_natm_reduce_claude/textures/natm_material_classes.png | natm_metal_rough_1k_head_atlas: skin, fur, cloth | natm_metal_rough_1k_head_atlas: 94 | - |
| mm6_ogr | mm6_ogr_claude/textures/ogr_head_material_classes.png<br>mm6_ogr_claude/textures/ogr_material_classes.png | ogr_material_response_head_atlas: cloth | ogr_material_response_head_atlas: 156 | - |
| mm6_ooz | mm6_ooz_claude/textures/ooz_material_classes.png | - | no metal | - |
| mm6_seas | mm6_seas_claude/textures/seas_material_classes.png | - | no metal | - |
| mm6_ske | mm6_ske_claude/textures/ske_head_material_classes.png<br>mm6_ske_claude/textures/ske_material_classes.png | - | no metal | - |
| mm6_wyrm | mm6_drr1_claude/textures/wyrm_head_material_classes.png<br>mm6_drr1_claude/textures/wyrm_material_classes.png | wyrm_metal_rough_1k: skin; wyrm_head_metal_rough_1k: skin | no metal | - |

Partly processed (images without a class map left unchanged):

- mm6_ckt: no class map for ckt_head_metal_rough_1k

## Skipped

| Model | Reason |
|---|---|
| mm6_aie1 | no metallic-roughness texture (unlit/effect or factor-only materials) |
| mm6_arc1_arrow | metal_rough_1k_arrow: no class map |
| mm6_bar1_sword | bar1_metal_rough_1k_sword: no class map |
| mm6_bat | no class map in the producing or related projects |
| mm6_bh | no class map in the producing or related projects |
| mm6_bld | bld_metal_rough_1k_head_atlas: no class map |
| mm6_cdr1 | cdr1r_body_metal_rough_2k: class map does not fit the UVs (39.1% of island texels far from a class); cdr1r_head_metal_rough_2k: class map does not fit the UVs (32.9% of island texels far from a class) |
| mm6_cle | cle_metal_rough_1k_head_atlas: class map does not fit the UVs (8.1% of island texels far from a class) |
| mm6_cle_staff | cle_metal_rough_1k_staff: no class map |
| mm6_demon | no class map in the producing or related projects |
| mm6_djn | djn_metal_rough_atlas: class map does not fit the UVs (33.6% of island texels far from a class) |
| mm6_dru1 | dru1_metal_rough_1k_head_atlas: class map does not fit the UVs (44.5% of island texels far from a class) |
| mm6_ert | no class map in the producing or related projects |
| mm6_fgt_mace | fgt_mace_metal_rough_1k_mace: no class map |
| mm6_fie1 | no metallic-roughness texture (unlit/effect or factor-only materials) |
| mm6_figc | no class map in the producing or related projects |
| mm6_figc_axe | no class map in the producing or related projects |
| mm6_figc_shield | no class map in the producing or related projects |
| mm6_fmp | no class map in the producing or related projects |
| mm6_gar | no class map in the producing or related projects |
| mm6_gob2_sword | gob2_metal_rough_1k_sword: no class map |
| mm6_gst | no class map in the producing or related projects |
| mm6_gua | gua_metal_rough_1k_head_atlas: class map does not fit the UVs (20.5% of island texels far from a class) |
| mm6_gua_halberd | gua_metal_rough_1k_halberd: no class map |
| mm6_lch | lch_metal_rough_1k_head_atlas: class map does not fit the UVs (56.3% of island texels far from a class) |
| mm6_lzd | metal_rough: no class map; metal_rough_head_atlas: no class map |
| mm6_mer1_club | mm6_mer1_club_mr_shared_atlas: no class map |
| mm6_mfp | mfp_metal_rough_head_atlas: class map does not fit the UVs (40.2% of island texels far from a class) |
| mm6_mnk1 | mnk1_orm_1k: class map does not fit the UVs (22.9% of island texels far from a class) |
| mm6_natf_blade | ForearmBlade_l0_r0.7500_blade_metal_rough_forearmblade: no class map; ForearmBlade_l1_r0.2500_blade_metal_rough_forearmblade: no class map; ForearmBlade_blade_metal_rough_forearmblade: no class map |
| mm6_natm_buckler | natm_buckler_metal_rough_buckler: class map does not fit the UVs (35.1% of island texels far from a class) |
| mm6_natm_spear | natm_spear_metal_rough_spear: class map does not fit the UVs (60.5% of island texels far from a class) |
| mm6_nobl | nobl_metal_rough_atlas_final: class map does not fit the UVs (41.5% of island texels far from a class) |
| mm6_nobl_sword | nobl_metal_rough_1k_sword: no class map |
| mm6_ogr_sword | ogr_material_response_sword: no class map |
| mm6_pfem | no class map in the producing or related projects |
| mm6_pman | no class map in the producing or related projects |
| mm6_pman_v2 | no class map in the producing or related projects |
| mm6_pmn2 | no class map in the producing or related projects |
| mm6_pmn2_artifact_staff | no metallic-roughness texture (unlit/effect or factor-only materials) |
| mm6_pmn2_staff | no project GLB with the same bytes |
| mm6_qfi | no class map in the producing or related projects |
| mm6_rat | no class map in the producing or related projects |
| mm6_rea | no metallic-roughness texture (unlit/effect or factor-only materials) |
| mm6_rob1 | no project GLB with the same bytes |
| mm6_ske_sword | no project GLB with the same bytes |
| mm6_sor1 | no class map in the producing or related projects |
| mm6_sor1_staff | no class map in the producing or related projects |
| mm6_spi1 | no class map in the producing or related projects |
| mm6_thf | thf_body_metal_rough_1k: class map does not fit the UVs (28.0% of island texels far from a class) |
| mm6_ttn | ttn_metal_rough_1k_head_atlas: class map does not fit the UVs (32.3% of island texels far from a class) |
| mm6_wdm | no class map in the producing or related projects |
| mm6_wel | no class map in the producing or related projects |
| mm6_wel_trident | no class map in the producing or related projects |
| mm6_wwf | wwf_metal_rough_1k_head_atlas: class map does not fit the UVs (40.3% of island texels far from a class) |
| mm6_wyrm_remains | no metallic-roughness texture (unlit/effect or factor-only materials) |

## Flags (metal median luminance below 40 or above 230)

- mm6_jak1_staff: HookedStaff_A: metal median luminance 31 (very dark)
- mm6_mer1: MerchantL0_B: metal median luminance 19 (very dark); MerchantL0_C: metal median luminance 26 (very dark); MerchantL1_B: metal median luminance 19 (very dark); MerchantL1_C: metal median luminance 26 (very dark); MerchantL2_B: metal median luminance 19 (very dark); MerchantL2_C: metal median luminance 26 (very dark); MerchantL3_B: metal median luminance 19 (very dark); MerchantL3_C: metal median luminance 26 (very dark)

## Notes

- Pilots keep the coordinator's decisions (bar1: keep skin; gob2 and kni: table values). The batch rule alone
  would also keep the knight's hair (old mask 0.25) and the barbarian's fur and leather (0.1-0.35).
- The barbarian's head class map was derived (`bar1_head_classes.py`,
  `../pilot/bar1_head_material_classes.png`).
- The output is compacted: mm6_mep and mm6_mep_staff lose LOD materials and images no primitive referenced.
- "No class map" covers models whose producing project and related projects have none; a skipped fit means the
  map was made for another UV layout (an earlier mesh, a re-UV after reduction or an unusual atlas packing).
- Models found by bytes in no project (mm6_pmn2_staff, mm6_rob1, mm6_ske_sword) are skipped, as instructed.
