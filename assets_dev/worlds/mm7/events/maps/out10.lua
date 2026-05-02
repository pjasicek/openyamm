-- Mount Nighon
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
    if not IsQBitSet(QBit(183)) then -- Hareckburg Town Portal
        SetQBit(QBit(183)) -- Hareckburg Town Portal
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "The Tannery", function()
    evt.EnterHouse(54) -- The Tannery
end, "The Tannery")

RegisterEvent(4, "The Tannery", nil, "The Tannery")

RegisterEvent(5, "Arcane Items", function()
    evt.EnterHouse(92) -- Arcane Items
end, "Arcane Items")

RegisterEvent(6, "Arcane Items", nil, "Arcane Items")

RegisterEvent(7, "Offerings and Blessings", function()
    evt.EnterHouse(318) -- Offerings and Blessings
end, "Offerings and Blessings")

RegisterEvent(8, "Offerings and Blessings", nil, "Offerings and Blessings")

RegisterEvent(9, "Applied Instruction", function()
    evt.EnterHouse(1576) -- Applied Instruction
end, "Applied Instruction")

RegisterEvent(10, "Applied Instruction", nil, "Applied Instruction")

RegisterEvent(11, "Fortune's Folly", function()
    evt.EnterHouse(248) -- Fortune's Folly
end, "Fortune's Folly")

RegisterEvent(12, "Fortune's Folly", nil, "Fortune's Folly")

RegisterEvent(13, "Paramount Guild of Fire", function()
    evt.EnterHouse(131) -- Paramount Guild of Fire
end, "Paramount Guild of Fire")

RegisterEvent(14, "Paramount Guild of Fire", nil, "Paramount Guild of Fire")

RegisterEvent(15, "The Blooded Dagger", function()
    evt.EnterHouse(14) -- The Blooded Dagger
end, "The Blooded Dagger")

RegisterEvent(16, "The Blooded Dagger", nil, "The Blooded Dagger")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Whitesky Residence", function()
    evt.EnterHouse(990) -- Whitesky Residence
end, "Whitesky Residence")

RegisterEvent(53, "Evander's Home", function()
    evt.EnterHouse(995) -- Evander's Home
end, "Evander's Home")

RegisterEvent(54, "Anwyn Residence", function()
    evt.EnterHouse(996) -- Anwyn Residence
end, "Anwyn Residence")

RegisterEvent(55, "Silk's Home", function()
    evt.EnterHouse(997) -- Silk's Home
end, "Silk's Home")

RegisterEvent(56, "Dusk's Home", function()
    evt.EnterHouse(1002) -- Dusk's Home
end, "Dusk's Home")

RegisterEvent(57, "Elmo's House", function()
    evt.EnterHouse(991) -- Elmo's House
end, "Elmo's House")

RegisterEvent(58, "Roggen Residence", function()
    evt.EnterHouse(1143) -- Roggen Residence
end, "Roggen Residence")

RegisterEvent(59, "Elzbet's House", function()
    evt.EnterHouse(1144) -- Elzbet's House
end, "Elzbet's House")

RegisterEvent(60, "Aznog's Place", function()
    evt.EnterHouse(1145) -- Aznog's Place
end, "Aznog's Place")

RegisterEvent(61, "Hollis' Home", function()
    evt.EnterHouse(1146) -- Hollis' Home
end, "Hollis' Home")

RegisterEvent(62, "Lanshee's House", function()
    evt.EnterHouse(1147) -- Lanshee's House
end, "Lanshee's House")

RegisterEvent(63, "Neldon Residence", function()
    evt.EnterHouse(1148) -- Neldon Residence
end, "Neldon Residence")

RegisterEvent(64, "Hawthorne Residence", function()
    evt.EnterHouse(1149) -- Hawthorne Residence
end, "Hawthorne Residence")

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

RegisterEvent(170, "Chest ", function()
    evt.OpenChest(0)
end, "Chest ")

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(15)) then
        if not IsAutonoteSet(277) then -- 2 Skill Points from the well near Offerings and Blessings in Damocles in Mount Nighon.
            SetAutonote(277) -- 2 Skill Points from the well near Offerings and Blessings in Damocles in Mount Nighon.
        end
        AddValue(SkillPoints, 2)
        SetPlayerBit(PlayerBit(15))
        evt.StatusText("+2 Skill Points")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(203, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(16)) then
        if not IsAutonoteSet(278) then -- 2 points of permanent Personality from the well near Fortune's Folly in Damocles in Mount Nighon.
            SetAutonote(278) -- 2 points of permanent Personality from the well near Fortune's Folly in Damocles in Mount Nighon.
        end
        AddValue(BasePersonality, 2)
        SetPlayerBit(PlayerBit(16))
        evt.StatusText("+2 Personality (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(204, "Drink from the Well", function()
    if IsPlayerBitSet(PlayerBit(17)) then
        evt.StatusText("Refreshing!")
        return
    elseif IsAutonoteSet(279) then -- 20 points of temporary Air, Earth, Fire, Water, Body, and Mind resistances from the well near the Fire Guild in Damocles in Mount Nighon.
        AddValue(FireResistanceBonus, 20)
        AddValue(WaterResistanceBonus, 20)
        AddValue(BodyResistanceBonus, 20)
        AddValue(AirResistanceBonus, 20)
        AddValue(EarthResistanceBonus, 20)
        AddValue(MindResistanceBonus, 20)
        SetPlayerBit(PlayerBit(17))
        evt.StatusText("+20 All Resistances (Temporary)")
        return
    else
        SetAutonote(279) -- 20 points of temporary Air, Earth, Fire, Water, Body, and Mind resistances from the well near the Fire Guild in Damocles in Mount Nighon.
        AddValue(FireResistanceBonus, 20)
        AddValue(WaterResistanceBonus, 20)
        AddValue(BodyResistanceBonus, 20)
        AddValue(AirResistanceBonus, 20)
        AddValue(EarthResistanceBonus, 20)
        AddValue(MindResistanceBonus, 20)
        SetPlayerBit(PlayerBit(17))
        evt.StatusText("+20 All Resistances (Temporary)")
        return
    end
end, "Drink from the Well")

RegisterEvent(205, "Fountain", nil, "Fountain")

RegisterEvent(206, "Drink from the Fountain", function()
    if not IsPlayerBitSet(PlayerBit(14)) then
        if not IsAutonoteSet(276) then -- 50 points of temporary Intellect and Personality from the central fountain in Damocles in Mount Nighon.
            SetAutonote(276) -- 50 points of temporary Intellect and Personality from the central fountain in Damocles in Mount Nighon.
        end
        AddValue(PersonalityBonus, 50)
        AddValue(IntellectBonus, 50)
        SetPlayerBit(PlayerBit(14))
        evt.StatusText("+50 Intellect and Personality (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Fountain")

RegisterEvent(207, "Drink from the Well", function()
    if not IsAtLeast(MaxSpellPoints, 0) then
        AddValue(CurrentSpellPoints, 25)
        evt.StatusText("+50 Spell Points")
        SetAutonote(280) -- 50 Spell Points recovered from the well in the eastern village in Mount Nighon.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(208, "Drink from the Well", function()
    if not IsAtLeast(MaxHealth, 0) then
        AddValue(CurrentHealth, 25)
        evt.StatusText("+50 Hit Points")
        SetAutonote(281) -- 50 Hit Points recovered from the well in the western village in Mount Nighon.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(209, "Thunderfist Mountain", nil, "Thunderfist Mountain")

RegisterEvent(210, "The Maze", nil, "The Maze")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(28)) then
        AddValue(BasePersonality, 10)
        AddValue(BaseIntellect, 10)
        SetPlayerBit(PlayerBit(28))
        evt.StatusText("+10 Personality and Intellect(Permanent)")
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(684)) then return end -- Visited Obelisk in Area 10
    evt.StatusText("fi_eo_od")
    SetAutonote(317) -- Obelisk message #9: fi_eo_od
    evt.ForPlayer(Players.All)
    SetQBit(QBit(684)) -- Visited Obelisk in Area 10
end, "Obelisk")

RegisterEvent(454, "Legacy event 454", function()
    evt.ForPlayer(Players.All)
    SetValue(Eradicated, 0)
end)

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter Thunderfist Mountain", function()
    evt.MoveToMap(-1024, 768, 4097, 1792, 0, 0, 150, 1, "\t7d07.blv")
end, "Enter Thunderfist Mountain")

RegisterEvent(502, "Enter The Maze", function()
    evt.MoveToMap(1536, -8614, 1, 512, 0, 0, 151, 1, "d02.blv")
end, "Enter The Maze")

RegisterEvent(503, "Enter Thunderfist Mountain", function()
    evt.MoveToMap(9960, 1443, 390, 1936, 0, 0, 150, 1, "\t7d07.blv")
end, "Enter Thunderfist Mountain")

RegisterEvent(504, "Enter Thunderfist Mountain", function()
    evt.MoveToMap(-11058, 4858, 3969, 148, 0, 0, 150, 1, "\t7d07.blv")
end, "Enter Thunderfist Mountain")

RegisterEvent(505, "Enter Thunderfist Mountain", function()
    evt.MoveToMap(11471, -3498, 2814, 414, 0, 0, 150, 1, "\t7d07.blv")
end, "Enter Thunderfist Mountain")

