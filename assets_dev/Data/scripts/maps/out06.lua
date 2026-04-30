-- Shadowspire
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
    onLeave = {6, 7, 8, 9, 10},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    { eventId = 490, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterEvent(4, "Legacy event 4", function()
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Skeletons Archer A, spawn Vampire (monster) A, spawn type 2 index 2
    return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(13, "Taleshire Hall", function()
    evt.EnterHouse(355) -- Taleshire Hall
    return
end, "Taleshire Hall")

RegisterEvent(14, "Taleshire Hall", nil, "Taleshire Hall")

RegisterEvent(15, "Nightcrawler Estate", function()
    evt.EnterHouse(356) -- Nightcrawler Estate
    return
end, "Nightcrawler Estate")

RegisterEvent(16, "Nightcrawler Estate", nil, "Nightcrawler Estate")

RegisterEvent(17, "Mistspring Residence", function()
    evt.EnterHouse(357) -- Mistspring Residence
    return
end, "Mistspring Residence")

RegisterEvent(18, "Mistspring Residence", nil, "Mistspring Residence")

RegisterEvent(19, "House Arachnia", function()
    evt.EnterHouse(358) -- House Arachnia
    return
end, "House Arachnia")

RegisterEvent(20, "House Arachnia", nil, "House Arachnia")

RegisterEvent(21, "Dirthmoore Cottage", function()
    evt.EnterHouse(359) -- Dirthmoore Cottage
    return
end, "Dirthmoore Cottage")

RegisterEvent(22, "Dirthmoore Cottage", nil, "Dirthmoore Cottage")

RegisterEvent(23, "House of Lathaen", function()
    evt.EnterHouse(360) -- House of Lathaen
    return
end, "House of Lathaen")

RegisterEvent(24, "House of Lathaen", nil, "House of Lathaen")

RegisterEvent(25, "Brightsprear Hall", function()
    evt.EnterHouse(361) -- Brightsprear Hall
    return
end, "Brightsprear Hall")

RegisterEvent(26, "Brightsprear Hall", nil, "Brightsprear Hall")

RegisterEvent(27, "Nightwood Estate", function()
    evt.EnterHouse(362) -- Nightwood Estate
    return
end, "Nightwood Estate")

RegisterEvent(28, "Nightwood Estate", nil, "Nightwood Estate")

RegisterEvent(29, "House Shador", function()
    evt.EnterHouse(363) -- House Shador
    return
end, "House Shador")

RegisterEvent(30, "House Shador", nil, "House Shador")

RegisterEvent(31, "House Mercutura", function()
    evt.EnterHouse(364) -- House Mercutura
    return
end, "House Mercutura")

RegisterEvent(32, "House Mercutura", nil, "House Mercutura")

RegisterEvent(33, "Roggen Hall", function()
    evt.EnterHouse(365) -- Roggen Hall
    return
end, "Roggen Hall")

RegisterEvent(34, "Roggen Hall", nil, "Roggen Hall")

RegisterEvent(35, "Hallien's Cottage", function()
    evt.EnterHouse(366) -- Hallien's Cottage
    return
end, "Hallien's Cottage")

RegisterEvent(36, "Hallien's Cottage", nil, "Hallien's Cottage")

RegisterEvent(37, "Roberts Residence", function()
    evt.EnterHouse(367) -- Roberts Residence
    return
end, "Roberts Residence")

RegisterEvent(38, "Roberts Residence", nil, "Roberts Residence")

RegisterEvent(39, "Infaustus' House", function()
    evt.EnterHouse(368) -- Infaustus' House
    return
end, "Infaustus' House")

RegisterEvent(40, "Infaustus' House", nil, "Infaustus' House")

RegisterEvent(41, "House of Journey", function()
    evt.EnterHouse(369) -- House of Journey
    return
end, "House of Journey")

RegisterEvent(42, "House of Journey", nil, "House of Journey")

RegisterEvent(43, "Whisper Hall", function()
    evt.EnterHouse(370) -- Whisper Hall
    return
end, "Whisper Hall")

RegisterEvent(44, "Whisper Hall", nil, "Whisper Hall")

RegisterEvent(45, "Steeleye Estate", function()
    evt.EnterHouse(371) -- Steeleye Estate
    return
end, "Steeleye Estate")

RegisterEvent(46, "Steeleye Estate", nil, "Steeleye Estate")

RegisterEvent(47, "House of Benefice", function()
    evt.EnterHouse(372) -- House of Benefice
    return
end, "House of Benefice")

RegisterEvent(48, "House of Benefice", nil, "House of Benefice")

RegisterEvent(49, "House Umberpool", function()
    evt.EnterHouse(373) -- House Umberpool
    return
end, "House Umberpool")

RegisterEvent(50, "House Umberpool", nil, "House Umberpool")

RegisterEvent(51, "Kelvin's Home", function()
    evt.EnterHouse(374) -- Kelvin's Home
    return
end, "Kelvin's Home")

RegisterEvent(52, "Kelvin's Home", nil, "Kelvin's Home")

RegisterEvent(53, "Caverhill Hall", function()
    evt.EnterHouse(375) -- Caverhill Hall
    return
end, "Caverhill Hall")

RegisterEvent(54, "Caverhill Hall", nil, "Caverhill Hall")

RegisterEvent(55, "Veritas Estate", function()
    evt.EnterHouse(376) -- Veritas Estate
    return
end, "Veritas Estate")

RegisterEvent(56, "Veritas Estate", nil, "Veritas Estate")

RegisterEvent(57, "Stillwater Estate", function()
    evt.EnterHouse(377) -- Stillwater Estate
    return
end, "Stillwater Estate")

RegisterEvent(58, "Stillwater Estate", nil, "Stillwater Estate")

RegisterEvent(59, "Crane Cottage", function()
    evt.EnterHouse(378) -- Crane Cottage
    return
end, "Crane Cottage")

RegisterEvent(60, "Crane Cottage", nil, "Crane Cottage")

RegisterEvent(61, "Bith Estate", function()
    evt.EnterHouse(379) -- Bith Estate
    return
end, "Bith Estate")

RegisterEvent(62, "Bith Estate", nil, "Bith Estate")

RegisterEvent(63, "Fellburn Residence", function()
    evt.EnterHouse(380) -- Fellburn Residence
    return
end, "Fellburn Residence")

RegisterEvent(64, "Fellburn Residence", nil, "Fellburn Residence")

RegisterEvent(65, "Gallowswell Manor", function()
    evt.EnterHouse(381) -- Gallowswell Manor
    return
end, "Gallowswell Manor")

RegisterEvent(66, "Gallowswell Manor", nil, "Gallowswell Manor")

RegisterEvent(67, "House Fiddlebone", function()
    evt.EnterHouse(382) -- House Fiddlebone
    return
end, "House Fiddlebone")

RegisterEvent(68, "House Fiddlebone", nil, "House Fiddlebone")

RegisterEvent(69, "Deverbero Residence", function()
    evt.EnterHouse(383) -- Deverbero Residence
    return
end, "Deverbero Residence")

RegisterEvent(70, "Deverbero Residence", nil, "Deverbero Residence")

RegisterEvent(71, "Tantilion's House", function()
    evt.EnterHouse(384) -- Tantilion's House
    return
end, "Tantilion's House")

RegisterEvent(72, "Tantilion's House", nil, "Tantilion's House")

RegisterEvent(73, "Fist Residence", function()
    evt.EnterHouse(385) -- Fist Residence
    return
end, "Fist Residence")

RegisterEvent(74, "Fist Residence", nil, "Fist Residence")

RegisterEvent(75, "Wargreen's Lab", function()
    evt.EnterHouse(386) -- Wargreen's Lab
    return
end, "Wargreen's Lab")

RegisterEvent(76, "Wargreen's Lab", nil, "Wargreen's Lab")

RegisterEvent(77, "House Wallace", function()
    evt.EnterHouse(387) -- House Wallace
    return
end, "House Wallace")

RegisterEvent(78, "House Wallace", nil, "House Wallace")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
end, "Chest")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(BaseIntellect, 16) then
        AddValue(BaseIntellect, 2)
        evt.StatusText("Intellect +2 (permanent)")
        SetAutonote(259) -- Will in the city of Twilight under the Shadowspire gives a permanent Intellect bonus up to an Intellect of 16.
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(NumBounties, 99) then
            evt.StatusText("Refreshing")
        else
            AddValue(Gold, 200)
            AddValue(MapVar(31), 1)
            SetAutonote(260) -- Well in the city of Twilight under the Shadowspire gives 200 gold if the total gold on party and in the bank is less than 100.
        end
    return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(104, "Drink from the fountain", function()
    if not IsQBitSet(QBit(182)) then -- Twiling Town Portal
        SetQBit(QBit(182)) -- Twiling Town Portal
    end
    if not IsAtLeast(MaxSpellPoints, 0) then
        AddValue(CurrentSpellPoints, 25)
        evt.StatusText("You mind clears, and you recover some Mana")
        SetAutonote(261) -- Fountain in the city of Twilight under the Shadowspire restores Spell Points.
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the fountain")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(191)) then return end -- Obelisk Area 6
    evt.StatusText("inesonmid")
    SetAutonote(24) -- Obelisk message #8: inesonmid
    SetQBit(QBit(191)) -- Obelisk Area 6
    return
end, "Obelisk")

RegisterEvent(171, "Blooded Daggers and Blades", function()
    evt.EnterHouse(5) -- Blooded Daggers and Blades
    return
end, "Blooded Daggers and Blades")

RegisterEvent(172, "Blooded Daggers and Blades", nil, "Blooded Daggers and Blades")

RegisterEvent(173, "Supple Leather", function()
    evt.EnterHouse(19) -- Supple Leather
    return
end, "Supple Leather")

RegisterEvent(174, "Supple Leather", nil, "Supple Leather")

RegisterEvent(175, "Mystical Mayhem", function()
    evt.EnterHouse(33) -- Mystical Mayhem
    return
end, "Mystical Mayhem")

RegisterEvent(176, "Mystical Mayhem", nil, "Mystical Mayhem")

RegisterEvent(177, "Wolves' Bane", function()
    evt.EnterHouse(45) -- Wolves' Bane
    return
end, "Wolves' Bane")

RegisterEvent(178, "Wolves' Bane", nil, "Wolves' Bane")

RegisterEvent(181, "Guild Caravans", function()
    evt.EnterHouse(58) -- Guild Caravans
    return
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(183, "Smoke", function()
    evt.EnterHouse(65) -- Smoke
    return
end, "Smoke")

RegisterEvent(184, "Smoke", nil, "Smoke")

RegisterEvent(185, "Cathedral of Night", function()
    evt.EnterHouse(78) -- Cathedral of Night
    return
end, "Cathedral of Night")

RegisterEvent(186, "Cathedral of Night", nil, "Cathedral of Night")

RegisterEvent(187, "Assassin's School", function()
    evt.EnterHouse(93) -- Assassin's School
    return
end, "Assassin's School")

RegisterEvent(188, "Assassin's School", nil, "Assassin's School")

RegisterEvent(191, "Black Company", function()
    evt.EnterHouse(112) -- Black Company
    return
end, "Black Company")

RegisterEvent(192, "Black Company", nil, "Black Company")

RegisterEvent(193, "The Blood Bank", function()
    evt.EnterHouse(131) -- The Blood Bank
    return
end, "The Blood Bank")

RegisterEvent(194, "The Blood Bank", nil, "The Blood Bank")

RegisterEvent(201, "Guild of Dark", function()
    evt.EnterHouse(143) -- Guild of Dark
    return
end, "Guild of Dark")

RegisterEvent(202, "Guild of Dark", nil, "Guild of Dark")

RegisterEvent(401, "Necromancers' Guild", nil, "Necromancers' Guild")

RegisterEvent(402, "Mad Necromancer's Lab", nil, "Mad Necromancer's Lab")

RegisterEvent(403, "Vampire Crypt", nil, "Vampire Crypt")

RegisterEvent(404, "A Cave", nil, "A Cave")

RegisterEvent(449, "Fountain", nil, "Fountain")

RegisterEvent(450, "Legacy event 450", nil)

RegisterEvent(454, "Wolves' Bane", function()
    if IsQBitSet(QBit(239)) then return end -- for riki
    AddValue(InventoryItem(332), 332) -- Lloyd's Beacon
    SetQBit(QBit(239)) -- for riki
    return
end, "Wolves' Bane")

RegisterEvent(479, "Legacy event 479", function()
    local randomStep = PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(347, -6976, -15104)
    elseif randomStep == 4 then
        evt.PlaySound(347, 2176, -11904)
    elseif randomStep == 6 then
        evt.PlaySound(347, -2496, -16480)
    elseif randomStep == 8 then
        evt.PlaySound(347, -10400, -12800)
    elseif randomStep == 10 then
        evt.PlaySound(347, 7872, -9664)
    end
    return
end)

RegisterEvent(490, "Legacy event 490", function()
    local randomStep = PickRandomOption(490, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, 864, -13024)
    end
    return
end)

RegisterEvent(494, "Rune post", function()
    if IsQBitSet(QBit(281)) then -- Reagant spout area 6
        return
    elseif IsAtLeast(PerceptionSkill, 3) then
        local randomStep = PickRandomOption(494, 4, {5, 7, 9, 11, 13})
        if randomStep == 5 then
            evt.SummonItem(200, 5504, -12224, 96, 1000, 1, true) -- Widowsweep Berries
        elseif randomStep == 7 then
            evt.SummonItem(205, 5504, -12224, 96, 1000, 1, true) -- Phima Root
        elseif randomStep == 9 then
            evt.SummonItem(210, 5504, -12224, 96, 1000, 1, true) -- Poppy Pod
        elseif randomStep == 11 then
            evt.SummonItem(215, 5504, -12224, 96, 1000, 1, true) -- Mushroom
        elseif randomStep == 13 then
            evt.SummonItem(220, 5504, -12224, 96, 1000, 1, true) -- Potion Bottle
        end
        SetQBit(QBit(281)) -- Reagant spout area 6
        return
    else
        return
    end
end, "Rune post")

RegisterEvent(495, "Rune post", function()
    if IsQBitSet(QBit(279)) then return end -- Reagant spout area 6
    if not IsAtLeast(PerceptionSkill, 5) then return end
    local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11})
    if randomStep == 5 then
        evt.SummonItem(2138, -3136, -4032, 348, 1000, 1, true)
    elseif randomStep == 7 then
        evt.SummonItem(2139, -3136, -4032, 348, 1000, 1, true)
    elseif randomStep == 9 then
        evt.SummonItem(2140, -3136, -4032, 348, 1000, 1, true)
    elseif randomStep == 11 then
        evt.SummonItem(2141, -3136, -4032, 348, 1000, 1, true)
    end
    SetQBit(QBit(279)) -- Reagant spout area 6
    return
end, "Rune post")

RegisterEvent(496, "Rune post", function()
    if IsQBitSet(QBit(280)) then -- Reagant spout area 6
        return
    elseif IsAtLeast(PerceptionSkill, 7) then
        local randomStep = PickRandomOption(496, 4, {5, 7, 9, 11, 13, 15})
        if randomStep == 5 then
            evt.SummonItem(240, -12288, 7744, 988, 1000, 1, true) -- Might Boost
        elseif randomStep == 7 then
            evt.SummonItem(241, -12288, 7744, 988, 1000, 1, true) -- Intellect Boost
        elseif randomStep == 9 then
            evt.SummonItem(242, -12288, 7744, 988, 1000, 1, true) -- Personality Boost
        elseif randomStep == 11 then
            evt.SummonItem(243, -12288, 7744, 988, 1000, 1, true) -- Endurance Boost
        elseif randomStep == 13 then
            evt.SummonItem(244, -12288, 7744, 988, 1000, 1, true) -- Speed Boost
        elseif randomStep == 15 then
            evt.SummonItem(245, -12288, 7744, 988, 1000, 1, true) -- Accuracy Boost
        end
        SetQBit(QBit(280)) -- Reagant spout area 6
        return
    else
        return
    end
end, "Rune post")

RegisterEvent(501, "Enter the Necromancers' Guild", function()
    evt.MoveToMap(0, 64, 0, 512, 0, 0, 212, 0, "d19.blv")
    return
end, "Enter the Necromancers' Guild")

RegisterEvent(502, "Enter the Mad Necromancer's Lab", function()
    evt.MoveToMap(-900, -127, 1, 520, 0, 0, 213, 0, "d20.blv")
    return
end, "Enter the Mad Necromancer's Lab")

RegisterEvent(503, "Enter the Vampire Crypt", function()
    evt.MoveToMap(-457, -1749, 1, 512, 0, 0, 0, 0, "D21.blv")
    return
end, "Enter the Vampire Crypt")

RegisterEvent(504, "Enter the Cave", function()
    evt.MoveToMap(9690, 1334, 1176, 1024, 0, 0, 0, 0, "D49.blv")
    return
end, "Enter the Cave")

