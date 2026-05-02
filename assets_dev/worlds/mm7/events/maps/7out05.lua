-- Deyja
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
    SetValue(MapVar(31), 5)
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    elseif IsQBitSet(QBit(782)) then -- Your friends are mad at you
        if IsAtLeast(Counter(10), 720) then
            ClearQBit(QBit(782)) -- Your friends are mad at you
            SetValue(MapVar(6), 0)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 0)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
            return
        end
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    elseif IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    else
        return
    end
end)

RegisterEvent(3, "The Blackened Vial", function()
    evt.EnterHouse(120) -- The Blackened Vial
end, "The Blackened Vial")

RegisterEvent(4, "The Blackened Vial", nil, "The Blackened Vial")

RegisterEvent(5, "Faithful Steeds", function()
    evt.EnterHouse(464) -- Faithful Steeds
end, "Faithful Steeds")

RegisterEvent(6, "Faithful Steeds", nil, "Faithful Steeds")

RegisterEvent(7, "Temple of Dark", function()
    evt.EnterHouse(314) -- Temple of Dark
end, "Temple of Dark")

RegisterEvent(8, "Temple of Dark", nil, "Temple of Dark")

RegisterEvent(9, "The Snobbish Goblin", function()
    evt.EnterHouse(243) -- The Snobbish Goblin
end, "The Snobbish Goblin")

RegisterEvent(10, "The Snobbish Goblin", nil, "The Snobbish Goblin")

RegisterEvent(11, "Master Guild of Spirit", function()
    evt.EnterHouse(154) -- Master Guild of Spirit
end, "Master Guild of Spirit")

RegisterEvent(12, "Master Guild of Spirit", nil, "Master Guild of Spirit")

RegisterEvent(13, "Guild of Twilight", function()
    evt.EnterHouse(176) -- Guild of Twilight
end, "Guild of Twilight")

RegisterEvent(14, "Guild of Twilight", nil, "Guild of Twilight")

RegisterEvent(15, "Death's Door", function()
    evt.EnterHouse(88) -- Death's Door
end, "Death's Door")

RegisterEvent(16, "Death's Door", nil, "Death's Door")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Karrand Residence", function()
    evt.EnterHouse(969) -- Karrand Residence
end, "Karrand Residence")

RegisterEvent(53, "Cleareye's Home", function()
    evt.EnterHouse(970) -- Cleareye's Home
end, "Cleareye's Home")

RegisterEvent(54, "Foestryke Residence", function()
    evt.EnterHouse(971) -- Foestryke Residence
end, "Foestryke Residence")

RegisterEvent(55, "Oxhide Residence", function()
    evt.EnterHouse(972) -- Oxhide Residence
end, "Oxhide Residence")

RegisterEvent(56, "Shadowrunner's Home", function()
    evt.EnterHouse(973) -- Shadowrunner's Home
end, "Shadowrunner's Home")

RegisterEvent(57, "Kedrin Residence", function()
    evt.EnterHouse(974) -- Kedrin Residence
end, "Kedrin Residence")

RegisterEvent(58, "Botham's Home", function()
    evt.EnterHouse(975) -- Botham's Home
end, "Botham's Home")

RegisterEvent(59, "Mogren Residence", function()
    evt.EnterHouse(976) -- Mogren Residence
end, "Mogren Residence")

RegisterEvent(60, "Draken Residence", function()
    evt.EnterHouse(977) -- Draken Residence
end, "Draken Residence")

RegisterEvent(61, "Harli's Place", function()
    evt.EnterHouse(978) -- Harli's Place
end, "Harli's Place")

RegisterEvent(62, "Nevermore Residence", function()
    evt.EnterHouse(979) -- Nevermore Residence
end, "Nevermore Residence")

RegisterEvent(63, "Wiseman Residence", function()
    evt.EnterHouse(980) -- Wiseman Residence
end, "Wiseman Residence")

RegisterEvent(64, "Nightcrawler Residence", function()
    evt.EnterHouse(981) -- Nightcrawler Residence
end, "Nightcrawler Residence")

RegisterEvent(65, "Felburn's House", function()
    evt.EnterHouse(982) -- Felburn's House
end, "Felburn's House")

RegisterEvent(66, "Undershadow's Home", function()
    evt.EnterHouse(983) -- Undershadow's Home
end, "Undershadow's Home")

RegisterEvent(67, "Slicer's House", function()
    evt.EnterHouse(984) -- Slicer's House
end, "Slicer's House")

RegisterEvent(68, "Falk Residence", function()
    evt.EnterHouse(985) -- Falk Residence
end, "Falk Residence")

RegisterEvent(69, "Putnam Residence", function()
    evt.EnterHouse(1133) -- Putnam Residence
end, "Putnam Residence")

RegisterEvent(70, "Hawker Residence", function()
    evt.EnterHouse(1134) -- Hawker Residence
end, "Hawker Residence")

RegisterEvent(71, "Avalanche's", function()
    evt.EnterHouse(1135) -- Avalanche's
end, "Avalanche's")

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
    if IsQBitSet(QBit(580)) then -- Placed Golem right leg
        return
    elseif IsQBitSet(QBit(735)) then -- Right leg - I lost it
        return
    else
        SetQBit(QBit(735)) -- Right leg - I lost it
        return
    end
end, "Chest ")

RegisterEvent(170, "Chest ", function()
    evt.OpenChest(0)
    if IsQBitSet(QBit(579)) then -- Placed Golem left leg
        return
    elseif IsQBitSet(QBit(736)) then -- Left leg - I lost it
        return
    else
        SetQBit(QBit(736)) -- Left leg - I lost it
        return
    end
end, "Chest ")

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "Drink from the Well", function()
    if not IsAtLeast(BankGold, 99) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(MapVar(21), 1) then
            evt.StatusText("Refreshing!")
            return
        else
            AddValue(Gold, 200)
            SetValue(MapVar(21), 1)
            evt.StatusText("Refreshing!")
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(203, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(9)) then
        if not IsAutonoteSet(270) then -- 2 points of permanent Intellect from the southern village well in Deyja.
            SetAutonote(270) -- 2 points of permanent Intellect from the southern village well in Deyja.
        end
        AddValue(BaseIntellect, 2)
        SetPlayerBit(PlayerBit(9))
        evt.StatusText("+2 Intellect (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(204, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(11)) then
        if not IsAutonoteSet(272) then -- 10 points of temporary Personality from the well near the Temple of the Dark in Moulder in Deyja.
            SetAutonote(272) -- 10 points of temporary Personality from the well near the Temple of the Dark in Moulder in Deyja.
        end
        AddValue(PersonalityBonus, 10)
        SetPlayerBit(PlayerBit(11))
        evt.StatusText("+10 Personality (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(205, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(12)) then
        if not IsAutonoteSet(273) then -- 10 points of temporary Fire resistance from the well in the south side of Moulder in Deyja.
            SetAutonote(273) -- 10 points of temporary Fire resistance from the well in the south side of Moulder in Deyja.
        end
        AddValue(FireResistanceBonus, 10)
        SetPlayerBit(PlayerBit(12))
        evt.StatusText("+10 Fire Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(206, "Drink from the Well", function()
    if not IsAtLeast(PoisonedGreen, 0) then
        SetValue(PoisonedGreen, 0)
        evt.StatusText("You Feel Great!!")
        return
    end
    local randomStep = PickRandomOption(206, 5, {5, 7})
    if randomStep == 5 then
        evt.StatusText("Haven't you had enough ?")
    elseif randomStep == 7 then
        evt.StatusText("Do you think that's such a good idea ?")
    end
end, "Drink from the Well")

RegisterEvent(207, "Drink from the Well", function()
    if not IsAtLeast(FireResistance, 5) then
        if IsPlayerBitSet(PlayerBit(10)) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAutonoteSet(271) then -- 5 points of permanent Fire resistance from the well in the western village in Deyja.
            AddValue(FireResistance, 5)
            SetPlayerBit(PlayerBit(10))
            evt.StatusText("+5 Fire Resistance (Permanent)")
            return
        else
            SetAutonote(271) -- 5 points of permanent Fire resistance from the well in the western village in Deyja.
            AddValue(FireResistance, 5)
            SetPlayerBit(PlayerBit(10))
            evt.StatusText("+5 Fire Resistance (Permanent)")
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(26)) then
        AddValue(MindResistance, 10)
        AddValue(EarthResistance, 10)
        AddValue(BodyResistance, 10)
        SetPlayerBit(PlayerBit(26))
        evt.StatusText("+10 Mind, Earth, and Body Resistance(Permanent)")
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(679)) then return end -- Visited Obelisk in Area 5
    evt.StatusText(" a_eetcoa")
    SetAutonote(312) -- Obelisk message #4: a_eetcoa
    evt.ForPlayer(Players.All)
    SetQBit(QBit(679)) -- Visited Obelisk in Area 5
end, "Obelisk")

RegisterEvent(454, "Legacy event 454", function()
    if IsQBitSet(QBit(761)) then return end -- Don't get ambushed
    local randomStep = PickRandomOption(454, 2, {2, 4})
    if randomStep == 2 then
        SetValue(MapVar(31), 5)
    elseif randomStep == 4 then
        evt.SpeakNPC(461) -- Lunius Shador
        SetValue(MapVar(31), 0)
    end
end)

RegisterEvent(455, "Legacy event 455", function()
    if not IsAtLeast(MapVar(31), 5) then
        if not IsQBitSet(QBit(761)) then -- Don't get ambushed
            SetQBit(QBit(761)) -- Don't get ambushed
            evt.SummonMonsters(3, 1, 10, -2760, -15344, 2464, 66, 0) -- encounter slot 3 "Zombie" tier A, count 10, pos=(-2760, -15344, 2464), actor group 66, no unique actor name
            evt.SummonMonsters(3, 1, 10, -4560, -16632, 2464, 66, 0) -- encounter slot 3 "Zombie" tier A, count 10, pos=(-4560, -16632, 2464), actor group 66, no unique actor name
            evt.SetMonGroupBit(66, MonsterBits.Hostile, 1)
            SetValue(MapVar(31), 5)
            evt.SetNPCTopic(461, 0, 513) -- Lunius Shador topic 0: Pay 1000 Gold
            evt.SetNPCTopic(461, 1, 514) -- Lunius Shador topic 1: Don't Pay
            return
        end
        SetValue(MapVar(31), 5)
    end
    evt.SetNPCTopic(461, 0, 513) -- Lunius Shador topic 0: Pay 1000 Gold
    evt.SetNPCTopic(461, 1, 514) -- Lunius Shador topic 1: Don't Pay
end)

RegisterEvent(456, "Legacy event 456", function()
    if not IsAtLeast(MapVar(31), 5) then
        if not IsQBitSet(QBit(761)) then -- Don't get ambushed
            SetQBit(QBit(761)) -- Don't get ambushed
            evt.SummonMonsters(3, 1, 10, 19336, -13040, 2464, 66, 0) -- encounter slot 3 "Zombie" tier A, count 10, pos=(19336, -13040, 2464), actor group 66, no unique actor name
            evt.SummonMonsters(3, 1, 10, 17150, -13555, 2464, 66, 0) -- encounter slot 3 "Zombie" tier A, count 10, pos=(17150, -13555, 2464), actor group 66, no unique actor name
            evt.SetMonGroupBit(66, MonsterBits.Hostile, 1)
            SetValue(MapVar(31), 5)
            evt.SetNPCTopic(461, 0, 513) -- Lunius Shador topic 0: Pay 1000 Gold
            evt.SetNPCTopic(461, 1, 514) -- Lunius Shador topic 1: Don't Pay
            return
        end
        SetValue(MapVar(31), 5)
    end
    evt.SetNPCTopic(461, 0, 513) -- Lunius Shador topic 0: Pay 1000 Gold
    evt.SetNPCTopic(461, 1, 514) -- Lunius Shador topic 1: Don't Pay
end)

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter the Hall of the Pit", function()
    evt.MoveToMap(512, -3156, 1, 545, 0, 0, 140, 1, "t04.blv")
end, "Enter the Hall of the Pit")

RegisterEvent(502, "Enter Watchtower 6", function()
    evt.MoveToMap(-416, -1033, 1, 512, 0, 0, 141, 1, "\t7d15.blv")
end, "Enter Watchtower 6")

RegisterEvent(503, "Legacy event 503", function()
    if not IsQBitSet(QBit(611)) then -- Chose the path of Light
        evt.SpeakNPC(357) -- William Setag
        return
    end
    evt.MoveToMap(442, -1112, 1, 512, 0, 0, 0, 0, "\tmdt10.blv")
end)

RegisterEvent(504, "Enter Watchtower 6", function()
    if not IsQBitSet(QBit(708)) then -- Find second entrance to Watchtower6
        SetQBit(QBit(708)) -- Find second entrance to Watchtower6
        evt.MoveToMap(190, 4946, -511, 1024, 0, 0, 141, 1, "\t7d15.blv")
        return
    end
    evt.MoveToMap(190, 4946, -511, 1024, 0, 0, 141, 1, "\t7d15.blv")
end, "Enter Watchtower 6")

