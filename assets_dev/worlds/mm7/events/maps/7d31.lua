-- Fort Riverstride
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [177] = {1},
    [178] = {2},
    [179] = {3},
    [180] = {4},
    [181] = {5},
    [182] = {6},
    [183] = {7},
    [184] = {8},
    [185] = {9},
    [186] = {10},
    [187] = {11},
    [188] = {12},
    [189] = {13},
    [190] = {14},
    [191] = {15},
    [192] = {16},
    [193] = {17},
    [194] = {18},
    [195] = {19},
    [196] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 15, 24},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    elseif IsQBitSet(QBit(612)) then -- Chose the path of Dark
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    else
        return
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(14, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(15, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(16, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(26, DoorAction.Open)
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.CastSpell(15, 7, 4, -3200, -544, -496, -3200, -544, 0) -- Sparks
    evt.SetDoorState(30, DoorAction.Open)
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(34, DoorAction.Open)
    evt.SetDoorState(35, DoorAction.Open)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(36, DoorAction.Open)
    evt.SetDoorState(37, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(38, DoorAction.Open)
    evt.SetDoorState(39, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(40, DoorAction.Open)
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(42, DoorAction.Open)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(43, DoorAction.Open)
    evt.SetDoorState(44, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(45, DoorAction.Open)
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(49, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(48, DoorAction.Close)
    evt.SetDoorState(50, DoorAction.Close)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Vault", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(606)) then -- Give false Riverstride plans to Eldrich Parson in Castle Navan in the Tularean Forest.
        return
    elseif IsQBitSet(QBit(592)) then -- Gave plans to elfking
        return
    elseif IsQBitSet(QBit(594)) then -- Gave false plans to elfking (betray)
        return
    elseif IsQBitSet(QBit(604)) then -- Fort Riverstride. Opened chest with plans
        return
    else
        evt.SetDoorState(60, DoorAction.Open)
        evt.SetDoorState(61, DoorAction.Trigger)
        evt.ForPlayer(Players.All)
        SetQBit(QBit(604)) -- Fort Riverstride. Opened chest with plans
        return
    end
end, "Vault")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(182, "Cabinet", function()
    evt.OpenChest(6)
end, "Cabinet")

RegisterEvent(183, "Cabinet", function()
    evt.OpenChest(7)
end, "Cabinet")

RegisterEvent(184, "Cabinet", function()
    evt.OpenChest(8)
end, "Cabinet")

RegisterEvent(185, "Cabinet", function()
    evt.OpenChest(9)
end, "Cabinet")

RegisterEvent(186, "Cabinet", function()
    evt.OpenChest(10)
end, "Cabinet")

RegisterEvent(187, "Cabinet", function()
    evt.OpenChest(11)
end, "Cabinet")

RegisterEvent(188, "Cabinet", function()
    evt.OpenChest(12)
end, "Cabinet")

RegisterEvent(189, "Cabinet", function()
    evt.OpenChest(13)
end, "Cabinet")

RegisterEvent(190, "Cabinet", function()
    evt.OpenChest(14)
end, "Cabinet")

RegisterEvent(191, "Cabinet", function()
    evt.OpenChest(15)
end, "Cabinet")

RegisterEvent(192, "Cabinet", function()
    evt.OpenChest(16)
end, "Cabinet")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(196, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(612) -- Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
    evt.PlaySound(42317, -2304, 640)
    evt.PlaySound(42317, 256, 256)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(454, "Lever", function()
    evt.SetDoorState(53, DoorAction.Trigger)
    evt.CastSpell(24, 10, 4, 448, 400, -208, 448, 586, -527) -- Poison Spray
    evt.CastSpell(24, 10, 4, 0, 400, -208, 0, 586, -527) -- Poison Spray
    evt.CastSpell(24, 10, 4, -448, 400, -208, -448, 586, -527) -- Poison Spray
end, "Lever")

RegisterEvent(455, "Legacy event 455", function()
    evt.CastSpell(6, 10, 4, -1152, 1344, -288, 1152, 1472, -288) -- Fireball
    evt.CastSpell(6, 10, 4, 1152, 1344, -288, -1152, 1472, -288) -- Fireball
end)

RegisterEvent(501, "Leave Fort Riverstride", function()
    evt.MoveToMap(11270, -2144, 1601, 1536, 0, 0, 0, 0, "7out03.odm")
end, "Leave Fort Riverstride")

RegisterEvent(502, "Leave Fort Riverstride", function()
    evt.MoveToMap(10531, -1536, 513, 0, 0, 0, 0, 0, "7out03.odm")
end, "Leave Fort Riverstride")

