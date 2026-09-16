-- Temple of the Snake
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {16, 17, 18, 19, 20, 24},
    onLoad = {23},
    onLeave = {},
    openedChestIds = {
    [6] = {1},
    [7] = {2},
    [8] = {3},
    [9] = {4},
    [10] = {5},
    [11] = {6},
    [12] = {7},
    [13] = {8},
    [14] = {9},
    },
    contextActions = {
    [1] = { kind = "use_switch", source = "title" },
    [2] = { kind = "open_door", source = "opcode" },
    [3] = { kind = "use_switch", source = "title" },
    [4] = { kind = "use_switch", source = "title" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [7] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [8] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [9] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [10] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [11] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [12] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [13] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [14] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [16] = { kind = "secret_event", source = "heuristic", hidden = true },
    [17] = { kind = "secret_event", source = "heuristic", hidden = true },
    [18] = { kind = "secret_event", source = "heuristic", hidden = true },
    [19] = { kind = "secret_event", source = "heuristic", hidden = true },
    [20] = { kind = "secret_event", source = "heuristic", hidden = true },
    [21] = { kind = "teleport", source = "heuristic" },
    [50] = { kind = "leave_dungeon", source = "opcode", targetMap = "outb2.odm", targetName = "Blackshire" },
    },
    textureNames = {"t1swbd", "t1swbu"},
    spriteNames = {},
    castSpellIds = {32},
    timers = {
    { eventId = 22, sourceEventId = 22, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 5 },
    { eventId = 24, sourceEventId = 24, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 5 },
    },
})

RegisterEvent(1, "Switch", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SetTexture(635, "t1swbu")
    SetValue(MapVar(4), 1)
end, "Switch")

RegisterEvent(2, nil, function()
    evt.SetDoorState(2, DoorAction.Close)
end)

RegisterEvent(3, "Switch", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    SetValue(MapVar(3), 1)
    evt.SetTexture(643, "t1swbu")
    evt.SetTexture(639, "t1swbu")
end, "Switch")

RegisterEvent(4, "Switch", function()
    evt.SetDoorState(4, DoorAction.Trigger)
    evt.SetTexture(647, "t1swbu")
    SetValue(MapVar(5), 1)
end, "Switch")

RegisterEvent(5, nil, function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetTexture(635, "t1swbd")
    SetValue(MapVar(6), 1)
end)

RegisterEvent(6, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(7, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(8, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(9, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(10, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(11, "Chest", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.DamagePlayer(Players.All, const.Damage.Magic, 200)
        SetValue(MapVar(7), 1)
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(12, "Chest", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.DamagePlayer(Players.All, const.Damage.Fire, 200)
        SetValue(MapVar(8), 1)
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(13, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(16, nil, function()
    evt.DamagePlayer(6, const.Damage.Fire, 40)
end)

RegisterEvent(17, nil, function()
    evt.DamagePlayer(6, const.Damage.Magic, 40)
end)

RegisterEvent(18, nil, function()
    evt.DamagePlayer(6, const.Damage.Magic, 50)
end)

RegisterEvent(19, nil, function()
    evt.DamagePlayer(6, const.Damage.Air, 50)
end)

RegisterEvent(20, nil, function()
    evt.DamagePlayer(6, const.Damage.Fire, 50)
end)

RegisterEvent(21, nil, function()
    evt.StatusText("A teleporter!")
    evt.MoveToMap(3264, -1336, 513, 192, 0, 0, 0, 0)
end)

RegisterEvent(22, nil, function()
    if IsAtLeast(MapVar(3), 1) then
        evt.SetTexture(643, "t1swbd")
        evt.SetTexture(639, "t1swbd")
    end
end)

RegisterEvent(23, nil, function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetTexture(635, "t1swbu")
    end
    if IsAtLeast(MapVar(5), 1) then
        evt.SetTexture(647, "t1swbu")
    end
    if IsAtLeast(MapVar(6), 1) then
        evt.SetTexture(635, "t1swbd")
    end
end)

RegisterEvent(24, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.CastSpell(32, 7, 1, -3306, -1285, 640, -2000, -1285, 640) -- Ice Blast
end)

RegisterEvent(25, "Cage", function()
    if IsQBitSet(QBit(1227)) then return end -- NPC
    SetQBit(QBit(1227)) -- NPC
    SetQBit(QBit(1702)) -- Replacement for NPCs ¹108 ver. 6
    evt.SpeakNPC(893) -- Emmanuel Cravitz
end, "Cage")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(9230, 7102, 64, 512, 0, 0, 0, 0, "outb2.odm") -- Blackshire
end, "Exit")

