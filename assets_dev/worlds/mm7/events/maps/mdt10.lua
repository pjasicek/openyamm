-- William Setag's Tower
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
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
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "opcode" },
    [151] = { kind = "open_door", source = "opcode" },
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
    [376] = { kind = "open_door", source = "title" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out05.odm", targetName = "Deyja" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(536)) then -- Rescue Alice Hargreaves from William's Tower in the Deyja Moors then talk to Sir Charles Quixote.
        evt.SetMonGroupBit(57, MonsterBits.Invisible, 0) -- actor group 57: Master of the Sword, spawn Fighter Plate A
        evt.SetMonGroupBit(57, MonsterBits.Hostile, 1) -- actor group 57: Master of the Sword, spawn Fighter Plate A
    end
end)

RegisterNoOpEvent(2, nil)

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, nil, function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(151, nil, function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, "Door", function()
    if not IsQBitSet(QBit(537)) then -- Mini-dungeon Area 5. Rescued/Captured Alice Hargreaves.
        if IsQBitSet(QBit(1685)) then -- Replacement for NPCs ¹54 ver. 7
            return
        elseif IsQBitSet(QBit(536)) then -- Rescue Alice Hargreaves from William's Tower in the Deyja Moors then talk to Sir Charles Quixote.
            if not HasItem(1461) then -- William's Tower Key
                evt.FaceAnimation(FaceAnimation.DoorLocked)
                evt.StatusText("The Door is Locked")
                return
            end
            evt.SpeakNPC(393) -- Alice Hargreaves
        else
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            evt.StatusText("The Door is Locked")
        end
    return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    evt.StatusText("The Door is Locked")
end, "Door")

RegisterEvent(501, "Leave to tower", function()
    evt.MoveToMap(-5066, -19323, 3073, 512, 0, 0, 0, 9, "7out05.odm") -- Deyja
end, "Leave to tower")

