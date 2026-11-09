-- Authored pickups test room behaviour. build_pickups_test.py embeds this file after its generated tables and before
-- the registrations. The pickups are the shared Lua's (hesper_stage/common/pickups.lua); the room is not one of the
-- Hesper loot classes' maps, so it names its treasure level (5, an H2 dungeon's).
local handlers = {}

handlers[1] = function()
end

HesperPickups.setup({treasure = 5, canisters = {701}, vats = {702}, satchels = {751, 752, 753}, bundles = {754}})
