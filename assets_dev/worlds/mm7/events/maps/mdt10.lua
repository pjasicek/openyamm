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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(536)) then -- Rescue Alice Hargreaves from William's Tower in the Deyja Moors then talk to Sir Charles Quixote.
        evt.SetMonGroupBit(57, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(57, MonsterBits.Hostile, 1)
    end
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(151, "Legacy event 151", function()
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
    evt.MoveToMap(-5066, -19323, 3073, 512, 0, 0, 0, 0, "\t7out05.odm")
end, "Leave to tower")

