-- Lord Markham's Manor
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
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {15},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(616)) then -- Go to Colony Zod in the Land of the Giants and slay Xenofex then return to Resurectra in Castle Lambent in Celeste.
        evt.SetSprite(2, 0, "0")
    end
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    end
end)

RegisterEvent(2, "Legacy event 2", function()
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 1, false) then -- actor group 56; at least 1 matching actor defeated
        SetValue(MapVar(6), 2)
    end
end)

RegisterEvent(3, "Door", function()
    if not IsAtLeast(MapVar(6), 2) then
        if not IsAtLeast(MapVar(6), 1) then
            SetValue(MapVar(6), 1)
            evt.SpeakNPC(622) -- Guard
            return
        end
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
    end
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Legacy event 6", function()
    evt.PlaySound(42317, 3, 227)
end)

RegisterEvent(176, "Cabinet", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(177, "Cabinet", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, "Legacy event 376", function()
    if not IsQBitSet(QBit(724)) then -- Vase - I lost it
        SetQBit(QBit(724)) -- Vase - I lost it
    end
    if IsQBitSet(QBit(653)) then return end -- Only give Markham's vase once (Markham's manor, Thief promo).
    AddValue(InventoryItem(1426), 1426) -- Vase
    SetQBit(QBit(653)) -- Only give Markham's vase once (Markham's manor, Thief promo).
    evt.SetSprite(2, 0, "0")
    evt.CastSpell(15, 20, 3, -1132, 1001, 374, 0, 0, 0) -- Sparks
end)

RegisterEvent(416, "Enter Lord Markham's Chamber", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.EnterHouse(215) -- Lord Markham's Chamber
        return
    end
    evt.StatusText("This Door has Been Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Enter Lord Markham's Chamber")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(622) -- Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Lord Markham's Manor", function()
    evt.MoveToMap(11012, -14936, 384, 512, 0, 0, 0, 0, "7out13.odm")
end, "Leave Lord Markham's Manor")

