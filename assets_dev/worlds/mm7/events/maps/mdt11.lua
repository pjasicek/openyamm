-- The Hidden Tomb
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
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterEvent(176, "Sarcophagus", function()
    evt.OpenChest(1)
end, "Sarcophagus")

RegisterEvent(177, "Sarcophagus", function()
    evt.OpenChest(2)
end, "Sarcophagus")

RegisterEvent(178, "Sarcophagus", function()
    evt.OpenChest(3)
end, "Sarcophagus")

RegisterEvent(179, "Sarcophagus", function()
    evt.OpenChest(4)
end, "Sarcophagus")

RegisterEvent(180, "Sarcophagus", function()
    evt.OpenChest(5)
end, "Sarcophagus")

RegisterEvent(181, "Sarcophagus", function()
    evt.OpenChest(6)
    SetQBit(QBit(754)) -- Opened chest with shadow mask
end, "Sarcophagus")

RegisterEvent(182, "Sarcophagus", function()
    evt.OpenChest(7)
end, "Sarcophagus")

RegisterEvent(183, "Sarcophagus", function()
    evt.OpenChest(8)
end, "Sarcophagus")

RegisterEvent(184, "Sarcophagus", function()
    evt.OpenChest(9)
end, "Sarcophagus")

RegisterEvent(185, "Sarcophagus", function()
    evt.OpenChest(10)
end, "Sarcophagus")

RegisterEvent(186, "Sarcophagus", function()
    evt.OpenChest(11)
end, "Sarcophagus")

RegisterEvent(187, "Sarcophagus", function()
    evt.OpenChest(12)
end, "Sarcophagus")

RegisterEvent(188, "Sarcophagus", function()
    evt.OpenChest(13)
end, "Sarcophagus")

RegisterEvent(189, "Sarcophagus", function()
    evt.OpenChest(14)
end, "Sarcophagus")

RegisterEvent(190, "Sarcophagus", function()
    evt.OpenChest(15)
end, "Sarcophagus")

RegisterEvent(191, "Sarcophagus", function()
    evt.OpenChest(16)
end, "Sarcophagus")

RegisterEvent(192, "Sarcophagus", function()
    evt.OpenChest(17)
end, "Sarcophagus")

RegisterEvent(193, "Sarcophagus", function()
    evt.OpenChest(18)
end, "Sarcophagus")

RegisterEvent(194, "Sarcophagus", function()
    evt.OpenChest(19)
end, "Sarcophagus")

RegisterEvent(195, "Sarcophagus", function()
    evt.OpenChest(0)
end, "Sarcophagus")

RegisterEvent(501, "Leave the Hidden tomb", function()
    evt.MoveToMap(14207, -21526, 0, 1536, 0, 0, 0, 0, "7out03.odm")
end, "Leave the Hidden tomb")

