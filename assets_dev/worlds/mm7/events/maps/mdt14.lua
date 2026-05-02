-- The Bandit Caves
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {2},
    openedChestIds = {
    [176] = {1, 0},
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

RegisterEvent(2, "Legacy event 2", function()
    if evt.CheckMonstersKilled(ActorKillCheck.Any, 0, 0, false) then -- any actor; all matching actors defeated
        SetQBit(QBit(655)) -- Killed all monsters in Bandit cave
    end
end)

RegisterEvent(176, "Chest", function()
    if not IsAtLeast(MapVar(2), 1) then
        if not IsQBitSet(QBit(669)) then -- Retrieve Davrik's Signet ring from the Bandit Caves in the northeast of Erathia and return it to Davrik Peladium in Harmondale. - Davrik's Ring Quest
            evt.OpenChest(1)
            return
        end
        if not IsQBitSet(QBit(672)) then -- Got Signet ring out of chest
            SetValue(MapVar(2), 1)
            SetQBit(QBit(672)) -- Got Signet ring out of chest
            evt.OpenChest(0)
        end
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(0)
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

RegisterEvent(501, "Legacy event 501", function()
    evt.MoveToMap(18005, 7107, 2913, 1728, 0, 0, 0, 0, "7out03.odm")
end)

