-- Lair of the Wolf
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {74},
    onLeave = {},
    openedChestIds = {
    [40] = {1},
    [41] = {2},
    [42] = {3},
    [43] = {4},
    [44] = {5},
    [45] = {6},
    [46] = {7},
    [62] = {8},
    [63] = {9},
    [64] = {10},
    [65] = {11},
    },
    textureNames = {"d7wl1ctr2", "paladn01"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Wooden Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(3, "Wooden Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(4, "Wooden Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(5, "Wooden Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(6, "Wooden Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(7, "Wooden Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(8, "Magic Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Magic Door")

RegisterEvent(9, "Legacy event 9", function()
    evt.SetDoorState(9, DoorAction.Close)
end)

RegisterEvent(10, "Legacy event 10", function()
    evt.SetDoorState(10, DoorAction.Close)
end)

RegisterEvent(11, "Wooden Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(12, "Legacy event 12", function()
    evt.SetDoorState(12, DoorAction.Close)
end)

RegisterEvent(13, "Legacy event 13", function()
    evt.SetDoorState(13, DoorAction.Close)
end)

RegisterEvent(14, "Wooden Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(15, "Wooden Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(16, "Wooden Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(17, "Wooden Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(18, "Wooden Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(19, "Wooden Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(20, "Wooden Door", function()
    evt.SetDoorState(20, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(21, "Wooden Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(22, "Wooden Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(23, "Wooden Door", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(24, "Wooden Door", function()
    evt.SetDoorState(24, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(25, "Wooden Door", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(26, "Legacy event 26", function()
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(34, DoorAction.Open)
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(12, DoorAction.Open)
end)

RegisterEvent(28, "Legacy event 28", function()
    evt.SetDoorState(10, DoorAction.Open)
end)

RegisterEvent(29, "Legacy event 29", function()
    evt.SetDoorState(8, DoorAction.Open)
    evt.SummonMonsters(1, 1, 2, -3019, -7145, 1313, 0, 0) -- encounter slot 1 "Werewolf" tier A, count 2, pos=(-3019, -7145, 1313), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 4, -3019, -7391, 1313, 0, 0) -- encounter slot 2 "Nobleman" tier B, count 4, pos=(-3019, -7391, 1313), actor group 0, no unique actor name
    evt.PlaySound(42699, 0, 0)
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
    local randomStep = PickRandomOption(29, 7, {7, 9, 11, 13})
    if randomStep == 7 then
        evt.FaceExpression(29)
        return
    elseif randomStep == 9 then
        evt.FaceExpression(30)
        return
    elseif randomStep == 11 then
        evt.FaceExpression(39)
        return
    elseif randomStep == 13 then
        evt.FaceExpression(13)
        return
    end
end)

RegisterEvent(30, "Wooden Door", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(31, "Legacy event 31", function()
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end)

RegisterEvent(32, "Legacy event 32", function()
    evt.SetDoorState(32, DoorAction.Close)
end)

RegisterEvent(33, "Legacy event 33", function()
    evt.SetDoorState(33, DoorAction.Close)
end)

RegisterEvent(34, "Switch", function()
    evt.SetDoorState(34, DoorAction.Trigger)
    evt.SetDoorState(9, DoorAction.Trigger)
end, "Switch")

RegisterEvent(35, "Wooden Door", function()
    evt.SetDoorState(35, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(36, "Wooden Door", function()
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(37, "Wooden Door", function()
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(39, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(38, "Wooden Door", function()
    evt.SetDoorState(28, DoorAction.Close)
    evt.SetDoorState(29, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(39, "Wooden Door", function()
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(40, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(41, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(46, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(47, "Legacy event 47", function()
    evt.MoveToMap(4747, -16024, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(48, "Legacy event 48", function()
    evt.MoveToMap(4439, -9086, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(49, "Legacy event 49", function()
    evt.MoveToMap(2427, -19303, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(50, "Legacy event 50", function()
    evt.MoveToMap(2673, -11904, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.MoveToMap(8583, -16348, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.MoveToMap(8827, -9341, 1825, 0, 0, 0, 0, 0)
end)

RegisterEvent(54, "Wolf Altar", function()
    if HasItem(2079) or IsQBitSet(QBit(1044)) then -- Pearl of Purity
        evt.SetTexture(5083, "d7wl1ctr2")
        evt.SetTexture(5084, "d7wl1ctr2")
        evt.SetTexture(5085, "d7wl1ctr2")
        evt.SetTexture(5081, "d7wl1ctr2")
        evt.SetTexture(5082, "d7wl1ctr2")
        SetQBit(QBit(1041)) -- 17 D17, given when wolf altar is destroyed.
        evt.SetDoorState(53, DoorAction.Close)
    end
end, "Wolf Altar")

RegisterEvent(55, "Legacy event 55", function()
    if IsQBitSet(QBit(1059)) then return end -- 35 D17 Brought back Black Pearl and Ghost will no longer show up.
    evt.SetFacetBit(5286, 16384, 0)
    evt.SetTexture(5286, "paladn01")
end)

RegisterEvent(56, "Legacy event 56", function()
    if IsQBitSet(QBit(1044)) then -- 20 D17, given when party digs up tiger statue quest item.
        return
    elseif IsQBitSet(QBit(1166)) then -- NPC
        AddValue(Hour, 900)
        evt.StatusText("You find a Pearl.")
        AddValue(InventoryItem(2079), 2079) -- Pearl of Purity
        SetQBit(QBit(1044)) -- 20 D17, given when party digs up tiger statue quest item.
    else
        return
    end
end)

RegisterEvent(58, "Exit", function()
    evt.MoveToMap(-13100, 2028, 161, 640, 0, 0, 0, 0, "outb2.odm")
end, "Exit")

RegisterEvent(59, "Legacy event 59", function()
    evt.SummonMonsters(1, 1, 1, -130, -2922, 1, 0, 0) -- encounter slot 1 "Werewolf" tier A, count 1, pos=(-130, -2922, 1), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 2, 122, -2922, 1, 0, 0) -- encounter slot 1 "Werewolf" tier B, count 2, pos=(122, -2922, 1), actor group 0, no unique actor name
    evt.PlaySound(42699, 0, 0)
    local randomStep = PickRandomOption(59, 4, {4, 6, 8, 10})
    if randomStep == 4 then
        evt.FaceExpression(29)
        return
    elseif randomStep == 6 then
        evt.FaceExpression(30)
        return
    elseif randomStep == 8 then
        evt.FaceExpression(39)
        return
    elseif randomStep == 10 then
        evt.FaceExpression(13)
        return
    end
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.SetDoorState(14, DoorAction.Open)
    evt.SetDoorState(15, DoorAction.Open)
    evt.SummonMonsters(1, 1, 2, 4302, -3134, -511, 0, 0) -- encounter slot 1 "Werewolf" tier A, count 2, pos=(4302, -3134, -511), actor group 0, no unique actor name
    evt.SummonMonsters(1, 2, 1, 4490, -3087, -511, 0, 0) -- encounter slot 1 "Werewolf" tier B, count 1, pos=(4490, -3087, -511), actor group 0, no unique actor name
    evt.PlaySound(42699, 0, 0)
    local randomStep = PickRandomOption(61, 6, {6, 8, 10, 12})
    if randomStep == 6 then
        evt.FaceExpression(29)
        return
    elseif randomStep == 8 then
        evt.FaceExpression(30)
        return
    elseif randomStep == 10 then
        evt.FaceExpression(39)
        return
    elseif randomStep == 12 then
        evt.FaceExpression(13)
        return
    end
end)

RegisterEvent(62, "Crate", function()
    evt.OpenChest(8)
end, "Crate")

RegisterEvent(63, "Crate", function()
    evt.OpenChest(9)
end, "Crate")

RegisterEvent(64, "Crate", function()
    evt.OpenChest(10)
end, "Crate")

RegisterEvent(65, "Crate", function()
    evt.OpenChest(11)
end, "Crate")

RegisterEvent(67, "Legacy event 67", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SummonMonsters(1, 1, 1, -130, -2922, 1, 0, 0) -- encounter slot 1 "Werewolf" tier A, count 1, pos=(-130, -2922, 1), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 6, 122, -2922, 1, 0, 0) -- encounter slot 2 "Nobleman" tier B, count 6, pos=(122, -2922, 1), actor group 0, no unique actor name
    evt.PlaySound(42699, 0, 0)
    local randomStep = PickRandomOption(67, 5, {5, 7, 9, 11})
    if randomStep == 5 then
        evt.FaceExpression(29)
        return
    elseif randomStep == 7 then
        evt.FaceExpression(30)
        return
    elseif randomStep == 9 then
        evt.FaceExpression(39)
        return
    elseif randomStep == 11 then
        evt.FaceExpression(13)
        return
    end
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SummonMonsters(1, 1, 1, -3019, -7145, 1313, 0, 0) -- encounter slot 1 "Werewolf" tier A, count 1, pos=(-3019, -7145, 1313), actor group 0, no unique actor name
    evt.SummonMonsters(2, 2, 6, -3019, -7391, 1313, 0, 0) -- encounter slot 2 "Nobleman" tier B, count 6, pos=(-3019, -7391, 1313), actor group 0, no unique actor name
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
    evt.PlaySound(42699, 0, 0)
    local randomStep = PickRandomOption(68, 7, {7, 9, 11, 13})
    if randomStep == 7 then
        evt.FaceExpression(29)
        return
    elseif randomStep == 9 then
        evt.FaceExpression(30)
        return
    elseif randomStep == 11 then
        evt.FaceExpression(39)
        return
    elseif randomStep == 13 then
        evt.FaceExpression(13)
        return
    end
end)

RegisterEvent(73, "Crate", function()
    evt.StatusText("Empty")
end, "Crate")

RegisterEvent(74, "Legacy event 74", function()
    if IsQBitSet(QBit(1041)) then -- 17 D17, given when wolf altar is destroyed.
        evt.SetTexture(5083, "d7wl1ctr2")
        evt.SetTexture(5084, "d7wl1ctr2")
        evt.SetTexture(5085, "d7wl1ctr2")
        evt.SetTexture(5081, "d7wl1ctr2")
        evt.SetTexture(5082, "d7wl1ctr2")
    end
end)

RegisterEvent(90, "Legacy event 90", function()
    if IsQBitSet(QBit(1059)) then return end -- 35 D17 Brought back Black Pearl and Ghost will no longer show up.
    SetQBit(QBit(1166)) -- NPC
    evt.SpeakNPC(1080) -- Ghost of Balthasar
end)

