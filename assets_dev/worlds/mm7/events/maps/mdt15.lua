-- The Small House
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
    if IsQBitSet(QBit(759)) then return end -- Control Cube only once
    evt.SetMonsterItem(0, 1477, 1)
    evt.SetMonsterItem(0, 866, 1)
    evt.SetMonsterItem(1, 1477, 1)
    evt.SetMonsterItem(1, 866, 1)
    SetQBit(QBit(759)) -- Control Cube only once
end)

RegisterEvent(2, "Legacy event 2", function()
    if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 0, 0, false) then -- OE actor 0; all matching actors defeated
        if evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 1, 0, false) then -- OE actor 1; all matching actors defeated
            SetQBit(QBit(631)) -- Killed Evil MM3 Person
        end
        SetQBit(QBit(746)) -- Control Cube - I lost it
    end
    SetQBit(QBit(630)) -- Killed Good MM3 Person
    SetQBit(QBit(746)) -- Control Cube - I lost it
end)

RegisterEvent(176, "Door", function()
    evt.OpenChest(1)
end, "Door")

RegisterEvent(177, "Door", function()
    evt.OpenChest(2)
end, "Door")

RegisterEvent(178, "Door", function()
    evt.OpenChest(3)
end, "Door")

RegisterEvent(179, "Door", function()
    evt.OpenChest(4)
end, "Door")

RegisterEvent(180, "Door", function()
    evt.OpenChest(5)
end, "Door")

RegisterEvent(181, "Door", function()
    evt.OpenChest(6)
end, "Door")

RegisterEvent(182, "Door", function()
    evt.OpenChest(7)
end, "Door")

RegisterEvent(183, "Door", function()
    evt.OpenChest(8)
end, "Door")

RegisterEvent(184, "Door", function()
    evt.OpenChest(9)
end, "Door")

RegisterEvent(185, "Door", function()
    evt.OpenChest(10)
end, "Door")

RegisterEvent(186, "Door", function()
    evt.OpenChest(11)
end, "Door")

RegisterEvent(187, "Door", function()
    evt.OpenChest(12)
end, "Door")

RegisterEvent(188, "Door", function()
    evt.OpenChest(13)
end, "Door")

RegisterEvent(189, "Door", function()
    evt.OpenChest(14)
end, "Door")

RegisterEvent(190, "Door", function()
    evt.OpenChest(15)
end, "Door")

RegisterEvent(191, "Door", function()
    evt.OpenChest(16)
end, "Door")

RegisterEvent(192, "Door", function()
    evt.OpenChest(17)
end, "Door")

RegisterEvent(193, "Door", function()
    evt.OpenChest(18)
end, "Door")

RegisterEvent(194, "Door", function()
    evt.OpenChest(19)
end, "Door")

RegisterEvent(195, "Door", function()
    evt.OpenChest(0)
end, "Door")

RegisterEvent(501, "Legacy event 501", function()
    evt.MoveToMap(5648, 12374, 33, 0, 0, 0, 0, 0, "7d25.blv")
end)

RegisterEvent(502, "Legacy event 502", function()
    evt.MoveToMap(-7745, -6673, 65, 1024, 0, 0, 0, 0, "7d26.blv")
end)

