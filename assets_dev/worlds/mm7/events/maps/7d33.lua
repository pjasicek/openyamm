-- Castle Gryphonheart
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {2},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"chb1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    elseif IsQBitSet(QBit(612)) then -- Chose the path of Dark
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    else
        return
    end
end)

RegisterEvent(2, "Legacy event 2", function()
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 1, false) or evt.CheckMonstersKilled(ActorKillCheck.Group, 55, 1, false) then -- actor group 56; at least 1 matching actor defeated
        SetValue(MapVar(6), 2)
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(6, DoorAction.Open)
end)

RegisterEvent(5, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Legacy event 9", function()
    evt.SetDoorState(11, DoorAction.Open)
end)

RegisterEvent(10, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
end, "Door")

RegisterEvent(11, "Legacy event 11", function()
    evt.SetDoorState(1, DoorAction.Open)
end)

RegisterEvent(12, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Bookcase", function()
    if IsAtLeast(MapVar(51), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(196, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(51), 1)
    end
end, "Bookcase")

RegisterEvent(197, "Bookcase", function()
    if IsAtLeast(MapVar(52), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(197, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(52), 1)
    end
end, "Bookcase")

RegisterEvent(198, "Bookcase", function()
end, "Bookcase")

RegisterEvent(376, "Door", function()
    if not IsQBitSet(QBit(537)) then -- Mini-dungeon Area 5. Rescued/Captured Alice Hargreaves.
        if IsQBitSet(QBit(1685)) then -- Replacement for NPCs ¹54 ver. 7
            evt.StatusText("The Door is Locked")
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        elseif IsQBitSet(QBit(538)) then -- Capture Alice Hargreaves from her residence in Castle Gryphonheart and return her to William's Tower in the Deyja Moors.
            evt.EnterHouse(1158) -- Alice Hargreaves
        else
            evt.StatusText("The Door is Locked")
            evt.FaceAnimation(FaceAnimation.DoorLocked)
        end
    return
    end
    evt.StatusText("The Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Door")

RegisterEvent(377, "Portrait", function()
    if IsQBitSet(QBit(776)) then return end -- Took Roland Painting
    evt.SetTexture(15, "chb1")
    AddValue(InventoryItem(1425), 1425) -- Roland Ironfist Painting
    SetQBit(QBit(776)) -- Took Roland Painting
end, "Portrait")

RegisterEvent(378, "Portrait", function()
    if IsQBitSet(QBit(777)) then return end -- Took Archi Painting
    evt.SetTexture(16, "chb1")
    AddValue(InventoryItem(1424), 1424) -- Archibald Ironfist Painting
    SetQBit(QBit(777)) -- Took Archi Painting
end, "Portrait")

RegisterEvent(416, "Enter the Throne Room", function()
    if IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        if not IsAtLeast(MapVar(6), 2) then
            evt.EnterHouse(217) -- Throne Room
            return
        end
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    evt.StatusText("The Door is Locked")
end, "Enter the Throne Room")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(616) -- Castle Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(454, "Legacy event 454", function()
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Castle Gryphonheart", function()
    evt.MoveToMap(-486, 9984, 2401, 1024, 0, 0, 0, 0, "7out03.odm")
end, "Leave Castle Gryphonheart")

RegisterEvent(502, "Leave Castle Gryphonheart", function()
    if not HasItem(1462) then -- Catherine's Key
        evt.StatusText("The Door is Locked")
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(1050, 9991, 2913, 1024, 0, 0, 0, 0, "7out03.odm")
end, "Leave Castle Gryphonheart")

