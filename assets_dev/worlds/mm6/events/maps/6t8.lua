-- Temple of the Snake
-- generated from legacy EVT/STR

SetMapMetadata({
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
    textureNames = {"t1swbd", "t1swbu"},
    spriteNames = {},
    castSpellIds = {32},
    timers = {
    { eventId = 22, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 24, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(1, "Switch", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SetTexture(635, "t1swbu")
    SetValue(MapVar(4), 1)
end, "Switch")

RegisterEvent(2, "Legacy event 2", function()
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

RegisterEvent(5, "Legacy event 5", function()
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
        evt.DamagePlayer(5, 5, 200)
        SetValue(MapVar(7), 1)
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(12, "Chest", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.DamagePlayer(5, 0, 200)
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

RegisterEvent(16, "Legacy event 16", function()
    evt.DamagePlayer(6, 0, 40)
end)

RegisterEvent(17, "Legacy event 17", function()
    evt.DamagePlayer(6, 5, 40)
end)

RegisterEvent(18, "Legacy event 18", function()
    evt.DamagePlayer(6, 5, 50)
end)

RegisterEvent(19, "Legacy event 19", function()
    evt.DamagePlayer(6, 1, 50)
end)

RegisterEvent(20, "Legacy event 20", function()
    evt.DamagePlayer(6, 0, 50)
end)

RegisterEvent(21, "Legacy event 21", function()
    evt.StatusText("A teleporter!")
    evt.MoveToMap(3264, -1336, 513, 192, 0, 0, 0, 0)
end)

RegisterEvent(22, "Legacy event 22", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.SetTexture(643, "t1swbd")
        evt.SetTexture(639, "t1swbd")
    end
end)

RegisterEvent(23, "Legacy event 23", function()
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

RegisterEvent(24, "Legacy event 24", function()
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
    evt.MoveToMap(9230, 7102, 64, 512, 0, 0, 0, 0, "outb2.odm")
end, "Exit")

