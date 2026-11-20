-- Relocate persistent storage behind the tavern without moving saved inventories.
-- The bridge retains its original loot definitions in the previously unused ids 0/19.
local containers = {
    [76] = {0, "Chest"},
    [77] = {19, "Chest"},
    [501] = {2, "Storage"},
    [502] = {3, "Storage"},
}

for eventId, container in pairs(containers) do
    local chestId, name = container[1], container[2]
    RegisterEvent(eventId, name, function()
        evt.OpenChest(chestId)
    end, name)
    evt.meta.map.openedChestIds[eventId] = {chestId}
    evt.meta.map.contextActions[eventId] = {
        kind = "open_chest", source = "opcode", chestIds = {chestId},
    }
end

RegisterEvent(503, "Storage", nil, "Storage")
