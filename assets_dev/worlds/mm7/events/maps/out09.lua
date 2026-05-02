-- Evenmorn Island
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [151] = {1},
    [152] = {2},
    [153] = {3},
    [154] = {4},
    [155] = {5},
    [156] = {6},
    [157] = {7},
    [158] = {8},
    [159] = {9},
    [160] = {10},
    [161] = {11},
    [162] = {12},
    [163] = {13},
    [164] = {14},
    [165] = {15},
    [166] = {16},
    [167] = {17},
    [168] = {18},
    [169] = {19},
    [170] = {0},
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

RegisterEvent(3, "The Laughing Monk", function()
    evt.EnterHouse(247) -- The Laughing Monk
end, "The Laughing Monk")

RegisterEvent(4, "The Laughing Monk", nil, "The Laughing Monk")

RegisterEvent(5, "Paramount Guild of Water", function()
    evt.EnterHouse(143) -- Paramount Guild of Water
end, "Paramount Guild of Water")

RegisterEvent(6, "Paramount Guild of Water", nil, "Paramount Guild of Water")

RegisterEvent(7, "Sacred Sails", function()
    evt.EnterHouse(489) -- Sacred Sails
end, "Sacred Sails")

RegisterEvent(8, "Sacred Sails", nil, "Sacred Sails")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Crane Residence", function()
    evt.EnterHouse(987) -- Crane Residence
end, "Crane Residence")

RegisterEvent(53, "Smithson Residence", function()
    evt.EnterHouse(988) -- Smithson Residence
end, "Smithson Residence")

RegisterEvent(54, "Caverhill Residence", function()
    evt.EnterHouse(986) -- Caverhill Residence
end, "Caverhill Residence")

RegisterEvent(151, "Chest ", function()
    evt.OpenChest(1)
end, "Chest ")

RegisterEvent(152, "Chest ", function()
    evt.OpenChest(2)
end, "Chest ")

RegisterEvent(153, "Chest ", function()
    evt.OpenChest(3)
end, "Chest ")

RegisterEvent(154, "Chest ", function()
    evt.OpenChest(4)
end, "Chest ")

RegisterEvent(155, "Chest ", function()
    evt.OpenChest(5)
end, "Chest ")

RegisterEvent(156, "Chest ", function()
    evt.OpenChest(6)
end, "Chest ")

RegisterEvent(157, "Chest ", function()
    evt.OpenChest(7)
end, "Chest ")

RegisterEvent(158, "Chest ", function()
    evt.OpenChest(8)
end, "Chest ")

RegisterEvent(159, "Chest ", function()
    evt.OpenChest(9)
end, "Chest ")

RegisterEvent(160, "Chest ", function()
    evt.OpenChest(10)
end, "Chest ")

RegisterEvent(161, "Chest ", function()
    evt.OpenChest(11)
end, "Chest ")

RegisterEvent(162, "Chest ", function()
    evt.OpenChest(12)
end, "Chest ")

RegisterEvent(163, "Chest ", function()
    evt.OpenChest(13)
end, "Chest ")

RegisterEvent(164, "Chest ", function()
    evt.OpenChest(14)
end, "Chest ")

RegisterEvent(165, "Chest ", function()
    evt.OpenChest(15)
end, "Chest ")

RegisterEvent(166, "Chest ", function()
    evt.OpenChest(16)
end, "Chest ")

RegisterEvent(167, "Chest ", function()
    evt.OpenChest(17)
end, "Chest ")

RegisterEvent(168, "Chest ", function()
    evt.OpenChest(18)
end, "Chest ")

RegisterEvent(169, "Chest ", function()
    evt.OpenChest(19)
end, "Chest ")

RegisterEvent(170, "Legacy event 170", function()
    if IsQBitSet(QBit(690)) then return end -- Open final Obelisk Chest
    evt.OpenChest(0)
    AddValue(Gold, 100000)
    evt.ForPlayer(Players.All)
    SetQBit(QBit(690)) -- Open final Obelisk Chest
end)

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "The Grand Temple of the Moon", nil, "The Grand Temple of the Moon")

RegisterEvent(203, "The Grand Temple of the Sun", nil, "The Grand Temple of the Sun")

RegisterEvent(204, "Legacy event 204", nil)

RegisterEvent(205, "Jump into the Well", function()
    evt.MoveToMap(4234, -8993, 384, 1216, 0, 0, 0, 0)
end, "Jump into the Well")

RegisterEvent(206, "Jump into the Well", function()
    evt.MoveToMap(-13860, -5350, 256, 192, 0, 0, 0, 0)
end, "Jump into the Well")

RegisterEvent(401, "Altar", function()
    if not IsQBitSet(QBit(561)) then return end -- Visit the three stonehenge monoliths in Tatalia, the Evenmorn Islands, and Avlee, then return to Anthony Green in the Tularean Forest.
    if IsQBitSet(QBit(562)) then -- Visited all stonehenges
        return
    elseif IsQBitSet(QBit(563)) then -- Visited stonehenge 1 (area 9)
        return
    else
        evt.ForPlayer(Players.All)
        SetQBit(QBit(563)) -- Visited stonehenge 1 (area 9)
        evt.ForPlayer(Players.All)
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        if IsQBitSet(QBit(564)) and IsQBitSet(QBit(565)) then -- Visited stonehenge 2 (area 13)
            evt.ForPlayer(Players.All)
            SetQBit(QBit(562)) -- Visited all stonehenges
        else
        end
        return
    end
end, "Altar")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(27)) then
        AddValue(BaseAccuracy, 10)
        AddValue(BaseSpeed, 10)
        SetPlayerBit(PlayerBit(27))
        evt.StatusText("+10 Accuracy and Speed(Permanent)")
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(683)) then return end -- Visited Obelisk in Area 9
    evt.StatusText(" _vehlgpe")
    SetAutonote(316) -- Obelisk message #8: _vehlgpe
    evt.ForPlayer(Players.All)
    SetQBit(QBit(683)) -- Visited Obelisk in Area 9
end, "Obelisk")

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter the Grand Temple of the Moon", function()
    evt.MoveToMap(3136, 2053, 1, 512, 0, 0, 148, 1, "7d19.blv")
end, "Enter the Grand Temple of the Moon")

RegisterEvent(502, "Enter the Grand Temple of the Sun", function()
    evt.MoveToMap(0, -3179, 161, 512, 0, 0, 149, 1, "t03.blv")
end, "Enter the Grand Temple of the Sun")

