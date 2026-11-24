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
    contextActions = {
    [3] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [177] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [178] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [179] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [180] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [181] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [182] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [183] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [184] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [185] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [186] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [187] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [188] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [189] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [190] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [191] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [192] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [193] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [194] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [195] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [376] = { kind = "secret_event", source = "heuristic", hidden = true },
    [416] = { kind = "enter_house", source = "opcode", houseId = 215, targetName = "Lord Markham's Chamber" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out13.odm", targetName = "Tatalia" },
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {15},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(616)) then -- Go to Colony Zod in the Land of the Giants and slay Xenofex then return to Resurectra in Castle Lambent in Celeste.
        evt.SetSprite(2, 0, "0")
    end
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
    end
end)

RegisterEvent(2, nil, function()
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 56, 1, true) then -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A; at least 1 matching actor defeated
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
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

RegisterEvent(6, nil, function()
    evt.PlaySound(42317, 3, 227)
end)

RegisterEvent(176, "Cabinet", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        SetValue(MapVar(6), 2)
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(177, "Cabinet", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        SetValue(MapVar(6), 2)
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        SetValue(MapVar(6), 2)
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        SetValue(MapVar(6), 2)
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        SetValue(MapVar(6), 2)
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, nil, function()
    if not IsQBitSet(QBit(724)) then -- Vase - I lost it
        SetQBit(QBit(724)) -- Vase - I lost it
    end
    if IsQBitSet(QBit(653)) then return end -- Only give Markham's vase once (Markham's manor, Thief promo).
    AddValue(InventoryItem(1426), 1426) -- Vase
    SetQBit(QBit(653)) -- Only give Markham's vase once (Markham's manor, Thief promo).
    evt.SetSprite(2, 0, "0")
    evt.CastSpell(15, 20, 3, -1132, 1001, 374, 0, 0, 0) -- Sparks
end)

RegisterEvent(416, "Lord Markham's Chamber", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.EnterHouse(215) -- Lord Markham's Chamber
        return
    end
    evt.StatusText("This Door has Been Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Lord Markham's Chamber")

RegisterEvent(451, nil, function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(622) -- Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, nil, function()
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Initiate of the Sword, spawn Fighter Plate A, spawn Swordsman A
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, nil, function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Lord Markham's Manor", function()
    evt.MoveToMap(11012, -14936, 384, 512, 0, 0, 0, 8, "7out13.odm") -- Tatalia
end, "Leave Lord Markham's Manor")

