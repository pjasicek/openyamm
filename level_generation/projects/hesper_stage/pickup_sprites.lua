-- The pickups' decoration swaps (common/pickups.lua), each with its sprite name written out. A map loads only the
-- models of the decorations it places and of the literal SetSprite targets in its own script and overlays
-- (game/maps/DecorationModelManifest.cpp, mapEventSpriteNames), not the shared events/common file's computed ones,
-- so stage.py installs this file as the overlay events/maps/<map>_pickups.lua of every map that calls
-- HesperPickups.setup. Once the engine also reads the world's common scripts for SetSprite targets (the
-- integrator's engine queue), this table can move into common/pickups.lua.
HesperPickupSprites = {
    hes_stim_canister_red = function(id) evt.SetSprite(id, 1, "hes_stim_canister_red") end,
    hes_stim_canister_yellow = function(id) evt.SetSprite(id, 1, "hes_stim_canister_yellow") end,
    hes_stim_canister_blue = function(id) evt.SetSprite(id, 1, "hes_stim_canister_blue") end,
    hes_stim_canister_orange = function(id) evt.SetSprite(id, 1, "hes_stim_canister_orange") end,
    hes_stim_canister_green = function(id) evt.SetSprite(id, 1, "hes_stim_canister_green") end,
    hes_stim_canister_purple = function(id) evt.SetSprite(id, 1, "hes_stim_canister_purple") end,
    hes_stim_canister_white = function(id) evt.SetSprite(id, 1, "hes_stim_canister_white") end,
    hes_stim_canister_empty = function(id) evt.SetSprite(id, 1, "hes_stim_canister_empty") end,
    hes_serum_vat_red = function(id) evt.SetSprite(id, 1, "hes_serum_vat_red") end,
    hes_serum_vat_yellow = function(id) evt.SetSprite(id, 1, "hes_serum_vat_yellow") end,
    hes_serum_vat_blue = function(id) evt.SetSprite(id, 1, "hes_serum_vat_blue") end,
    hes_serum_vat_orange = function(id) evt.SetSprite(id, 1, "hes_serum_vat_orange") end,
    hes_serum_vat_green = function(id) evt.SetSprite(id, 1, "hes_serum_vat_green") end,
    hes_serum_vat_purple = function(id) evt.SetSprite(id, 1, "hes_serum_vat_purple") end,
    hes_serum_vat_white = function(id) evt.SetSprite(id, 1, "hes_serum_vat_white") end,
    hes_serum_vat_empty = function(id) evt.SetSprite(id, 1, "hes_serum_vat_empty") end,
    hes_colony_satchel_open = function(id) evt.SetSprite(id, 1, "hes_colony_satchel_open") end,
    hes_scrap_bundle_open = function(id) evt.SetSprite(id, 1, "hes_scrap_bundle_open") end,
}
