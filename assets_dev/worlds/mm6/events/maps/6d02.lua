-- Abandoned Temple
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {30},
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [12] = {1},
    [26] = {2, 4},
    [27] = {3},
    [28] = {5},
    [29] = {6},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "title" },
    [2] = { kind = "open_door", source = "title" },
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [11] = { kind = "teleport", source = "heuristic" },
    [12] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [25] = { kind = "open_door", source = "title" },
    [26] = { kind = "open_chest", source = "opcode", chestIds = {2, 4} },
    [27] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [28] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [29] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [31] = { kind = "teleport", source = "heuristic" },
    [35] = { kind = "secret_event", source = "heuristic", hidden = true },
    [50] = { kind = "leave_dungeon", source = "opcode", targetMap = "oute3.odm", targetName = "New Sorpigal" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 15},
    timers = {
    { eventId = 30, sourceEventId = 30, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 10 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Teleporter", function()
    evt.MoveToMap(247, 2331, -740, 1088, 0, 0, 0, 0)
end, "Teleporter")

RegisterEvent(12, nil, function()
    evt.OpenChest(1)
end)

RegisterEvent(14, nil, function()
    if IsQBitSet(QBit(1056)) then return end -- 32 D02, given when kid is rescued
    evt.SpeakNPC(980) -- Angela Dawson
    SetQBit(QBit(1704)) -- Replacement for NPCs ¹195 ver. 6
    SetQBit(QBit(1056)) -- 32 D02, given when kid is rescued
end)

RegisterEvent(16, "Cage", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.GiveItem(1, ItemType.Ring_)
end, "Cage")

RegisterEvent(17, "Cage", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    evt.GiveItem(1, 41)
end, "Cage")

RegisterEvent(18, "Cage", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    evt.GiveItem(1, ItemType.Weapon_)
end, "Cage")

RegisterEvent(19, "Cage", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    evt.GiveItem(2, ItemType.Ring_)
end, "Cage")

RegisterEvent(20, "Cage", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    evt.GiveItem(2, 41)
end, "Cage")

RegisterEvent(21, "Cage", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    evt.GiveItem(2, ItemType.Weapon_)
end, "Cage")

RegisterEvent(22, "Cage", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(8), 1)
    evt.GiveItem(2, ItemType.Scroll_)
    evt.CastSpell(6, 8, 1, 7808, 8960, -1768, 0, 0, 0) -- Fireball
end, "Cage")

RegisterEvent(23, "Cage", function()
    if IsAtLeast(MapVar(9), 1) then return end
    SetValue(MapVar(9), 1)
    evt.GiveItem(2, ItemType.Scroll_)
    evt.CastSpell(6, 8, 1, 7808, 8960, -1768, 0, 0, 0) -- Fireball
end, "Cage")

RegisterEvent(25, "Door", function()
    evt.StatusText("You've Rescued a child!  How patriarchal of you")
end, "Door")

RegisterEvent(26, "Chest", function()
    if not IsAtLeast(MapVar(3), 1) then
        if not IsQBitSet(QBit(1058)) then -- 34 D02, given when temple of Baa relic is found
            SetValue(MapVar(3), 1)
            evt.OpenChest(2)
            SetQBit(QBit(1058)) -- 34 D02, given when temple of Baa relic is found
            return
        end
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(2)
    SetQBit(QBit(1058)) -- 34 D02, given when temple of Baa relic is found
end, "Chest")

RegisterEvent(27, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(29, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(30, nil, function()
    evt.CastSpell(15, 10, 1, 11040, 6384, -176, 11040, 6384, 0) -- Sparks
    evt.CastSpell(15, 10, 1, 11040, 6384, -192, 15033, 5785, -256) -- Sparks
    evt.CastSpell(15, 10, 1, 11040, 6384, -200, 11188, 4279, -256) -- Sparks
    evt.CastSpell(15, 10, 1, 11040, 6485, -369, 7967, 6446, -256) -- Sparks
end)

RegisterEvent(31, "Teleporter", function()
    evt.MoveToMap(16519, -18589, 753, 1024, 50, 0, 0, 0)
end, "Teleporter")

RegisterEvent(35, nil, function()
    if IsAtLeast(MapVar(31), 1) then return end
    SetValue(MapVar(31), 1)
    evt.GiveItem(4, ItemType.Ring_)
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-21468, -263, 193, 1536, 0, 0, 0, 0, "oute3.odm") -- New Sorpigal
end, "Exit")

