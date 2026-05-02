-- New Sorpigal
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {100, 65535, 65534, 65533, 65532, 65531, 65530, 65529, 65528, 65527, 65526, 232},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    [80] = {6},
    [81] = {7},
    [82] = {8},
    [83] = {9},
    [84] = {10},
    [85] = {11},
    [86] = {12},
    [87] = {13},
    [88] = {14},
    [89] = {15},
    [90] = {16},
    [91] = {17},
    [92] = {18},
    },
    textureNames = {},
    spriteNames = {"6tree06", "swrdstx"},
    castSpellIds = {6},
    timers = {
    { eventId = 230, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterNoOpEvent(2, "Welcome to New Sorpigal", "Welcome to New Sorpigal")

RegisterEvent(3, "New Sorpigal Temple", function()
    evt.EnterHouse(325) -- New Sorpigal Temple
end, "New Sorpigal Temple")

RegisterEvent(4, "New Sorpigal Temple", nil, "New Sorpigal Temple")

RegisterEvent(5, "+5 Spell points restored.", function()
    evt.EnterHouse(62) -- The Common Defense
end, "+5 Spell points restored.")

RegisterEvent(6, "+5 Spell points restored.", nil, "+5 Spell points restored.")

RegisterEvent(7, "Savings House", function()
    evt.EnterHouse(297) -- Savings House
end, "Savings House")

RegisterEvent(8, "Savings House", nil, "Savings House")

RegisterEvent(9, "Traveler's Supply", function()
    evt.EnterHouse(1213) -- Traveler's Supply
end, "Traveler's Supply")

RegisterEvent(10, "Traveler's Supply", nil, "Traveler's Supply")

RegisterEvent(11, "A Lonely Knight", function()
    evt.EnterHouse(260) -- A Lonely Knight
end, "A Lonely Knight")

RegisterEvent(12, "A Lonely Knight", nil, "A Lonely Knight")

RegisterEvent(13, "The Seeing Eye", function()
    evt.EnterHouse(97) -- The Seeing Eye
end, "The Seeing Eye")

RegisterEvent(14, "The Seeing Eye", nil, "The Seeing Eye")

RegisterEvent(15, "New Sorpigal Coach Company", function()
    evt.EnterHouse(470) -- New Sorpigal Coach Company
end, "New Sorpigal Coach Company")

RegisterEvent(16, "New Sorpigal Coach Company", nil, "New Sorpigal Coach Company")

RegisterEvent(17, "New Sorpigal", function()
    evt.EnterHouse(22) -- The Knife Shoppe
end, "New Sorpigal")

RegisterEvent(18, "New Sorpigal", nil, "New Sorpigal")

RegisterEvent(19, "Blades' End", function()
    evt.EnterHouse(197) -- Blades' End
end, "Blades' End")

RegisterEvent(20, "Blades' End", nil, "Blades' End")

RegisterEvent(21, "Initiate Guild of the Elements", function()
    evt.EnterHouse(1214) -- Initiate Guild of the Elements
end, "Initiate Guild of the Elements")

RegisterEvent(22, "Initiate Guild of the Elements", nil, "Initiate Guild of the Elements")

RegisterEvent(23, "New Sorpigal Training Grounds", function()
    evt.EnterHouse(1583) -- New Sorpigal Training Grounds
end, "New Sorpigal Training Grounds")

RegisterEvent(24, "New Sorpigal Training Grounds", nil, "New Sorpigal Training Grounds")

RegisterEvent(25, "Initiate Guild of the Self", function()
    evt.EnterHouse(189) -- Initiate Guild of the Self
end, "Initiate Guild of the Self")

RegisterEvent(26, "Initiate Guild of the Self", nil, "Initiate Guild of the Self")

RegisterEvent(27, "Buccaneers' Lair", function()
    evt.EnterHouse(191) -- Buccaneers' Lair
end, "Buccaneers' Lair")

RegisterEvent(28, "Town Hall", function()
    evt.EnterHouse(208) -- Town Hall
end, "Town Hall")

RegisterEvent(29, "Odyssey", function()
    evt.EnterHouse(496) -- Odyssey
end, "Odyssey")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1228) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1243) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1258) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1273) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1288) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1383) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1394) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1413) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1422) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1430) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1439) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1448) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1456) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1463) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1469) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1303) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1316) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1328) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1339) -- House
end, "House")

RegisterEvent(69, "House", function()
    evt.EnterHouse(1351) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1361) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1372) -- House
end, "House")

RegisterEvent(75, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(76, "Crate", function()
    evt.OpenChest(2)
end, "Crate")

RegisterEvent(77, "Crate", function()
    evt.OpenChest(3)
end, "Crate")

RegisterEvent(78, "Crate", function()
    evt.OpenChest(4)
end, "Crate")

RegisterEvent(79, "Crate", function()
    evt.OpenChest(5)
end, "Crate")

RegisterEvent(80, "Crate", function()
    evt.OpenChest(6)
end, "Crate")

RegisterEvent(81, "Crate", function()
    evt.OpenChest(7)
end, "Crate")

RegisterEvent(82, "Crate", function()
    evt.OpenChest(8)
end, "Crate")

RegisterEvent(83, "Crate", function()
    evt.OpenChest(9)
end, "Crate")

RegisterEvent(84, "Crate", function()
    evt.OpenChest(10)
end, "Crate")

RegisterEvent(85, "Crate", function()
    evt.OpenChest(11)
end, "Crate")

RegisterEvent(86, "Crate", function()
    evt.OpenChest(12)
end, "Crate")

RegisterEvent(87, "Crate", function()
    evt.OpenChest(13)
end, "Crate")

RegisterEvent(88, "Crate", function()
    evt.OpenChest(14)
end, "Crate")

RegisterEvent(89, "Crate", function()
    evt.OpenChest(15)
end, "Crate")

RegisterEvent(90, "Crate", function()
    evt.OpenChest(16)
end, "Crate")

RegisterEvent(91, "Rock", function()
    evt.OpenChest(17)
end, "Rock")

RegisterEvent(92, "Crate", function()
    evt.OpenChest(18)
end, "Crate")

RegisterEvent(100, "Legacy event 100", function()
    if IsQBitSet(QBit(1104)) then return end -- Lisa
    SetQBit(QBit(1104)) -- Lisa
    SetQBit(QBit(1105)) -- Show Sulman's letter to Andover Potbello in New Sorpigal. - Set when the party starts
    AddValue(InventoryItem(2125), 2125) -- The Letter
end)

RegisterEvent(101, "Legacy event 101", function()
    if not IsQBitSet(QBit(1324)) then -- Peter
        evt.ForPlayer(Players.All)
        if not HasItem(2109) then -- Key to Goblinwatch
            evt.StatusText("The door is locked.")
            return
        end
        RemoveItem(2109) -- Key to Goblinwatch
        SetQBit(QBit(1324)) -- Peter
    end
    evt.MoveToMap(601, 6871, 177, 1400, 0, 0, 161, 1, "6d01.blv")
end)

RegisterEvent(102, "Legacy event 102", function()
    evt.MoveToMap(16406, -19669, 865, 500, 0, 0, 166, 1, "6d02.blv")
end)

RegisterEvent(103, "Legacy event 103", function()
    evt.MoveToMap(-2688, 1216, 1153, 1536, 0, 0, 191, 1, "6d18.blv")
end)

RegisterEvent(104, "Legacy event 104", function()
    evt.MoveToMap(12808, 6832, 64, 512, 0, 0, 0, 0)
end)

RegisterEvent(109, "Well", function()
    if not IsAtLeast(MapVar(71), 1) then
        if not IsAtLeast(Gold, 1) then
            AddValue(MapVar(71), 1)
            AddValue(Gold, 100)
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Well")

RegisterEvent(110, "Well", function()
    if not IsAtLeast(BaseLuck, 15) then
        if not IsAtLeast(MapVar(72), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(72), 1)
        AddValue(BaseLuck, 2)
        evt.StatusText("+2 Luck permanent")
        return
    end
    evt.StatusText("Refreshing!")
end, "Well")

RegisterEvent(111, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(11), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(11), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(298, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 7
    end
    local function Step_7()
        return nil
    end
    local function Step_9()
        if IsAtLeast(MapVar(11), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 9 then
            step = Step_9()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(112, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(12), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(12), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(299, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(12), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(113, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(13), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(13), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(300, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(13), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(114, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(14), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(14), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(301, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(14), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(115, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(15), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(15), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(467, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(15), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(116, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(16), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(16), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(303, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(16), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(117, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(17), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(17), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(302, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(17), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(118, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(18), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(18), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(305, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(18), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(119, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(19), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(19), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("You pick an apple.")
        return 4
    end
    local function Step_4()
        evt.SetSprite(304, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("Tree")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(19), 1) then return 4 end
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(130, "Legacy event 130", function()
    SetValue(MapVar(51), 30)
    SetValue(MapVar(52), 30)
end)

RegisterEvent(131, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(51), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(391) -- 5 Hit points cured by the central fountain in New Sorpigal.
        return
    end
    SubtractValue(MapVar(51), 1)
    AddValue(CurrentHealth, 5)
    evt.StatusText("+5 Hit points restored.")
    SetAutonote(391) -- 5 Hit points cured by the central fountain in New Sorpigal.
end, "Drink from Fountain")

RegisterEvent(140, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(52), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(392) -- 5 Spell points restored by the northwest fountain in New Sorpigal.
        return
    end
    SubtractValue(MapVar(52), 1)
    AddValue(CurrentSpellPoints, 5)
    evt.StatusText("+5 Spell points restored.")
    SetAutonote(392) -- 5 Spell points restored by the northwest fountain in New Sorpigal.
end, "Drink from Fountain")

RegisterEvent(150, "Drink from Fountain", function()
    if not IsAtLeast(MightBonus, 10) then
        SetValue(MightBonus, 10)
        evt.StatusText("+10 Might temporary.")
        SetAutonote(393) -- 10 Points of temporary might from the northeast fountain in New Sorpigal.
        return
    end
    evt.StatusText("Refreshing!")
    SetAutonote(393) -- 10 Points of temporary might from the northeast fountain in New Sorpigal.
end, "Drink from Fountain")

RegisterEvent(210, "Well", function()
    if IsAtLeast(Gold, 10000) then
        SubtractValue(Gold, 1000)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 5000) then
        SubtractValue(Gold, 500)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 1000) then
        SubtractValue(Gold, 100)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 500) then
        SubtractValue(Gold, 50)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 100) then
        SubtractValue(Gold, 10)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 50) then
        SubtractValue(Gold, 5)
        evt.SimpleMessage("Your purse feels much lighter as you foolishly throw your money into the well.")
        return
    elseif IsAtLeast(Gold, 40) then
        return
    else
        return
    end
end, "Well")

RegisterEvent(220, "Legacy event 220", function()
    evt.PlaySound(42607, -14600, 13500)
    evt.SummonObject(1050, -14320, 16272, 100, 1000, 15, true) -- Fireball
    evt.SummonObject(1050, -14096, 15648, 100, 600, 15, true) -- Fireball
    evt.SummonObject(1050, -13856, 16448, 100, 2000, 15, true) -- Fireball
    evt.SummonObject(4070, -14336, 16228, 100, 2000, 15, true) -- Rock Blast
    evt.SummonObject(4070, -14272, 16112, 96, 800, 15, true) -- Rock Blast
    evt.SummonObject(4070, -14496, 15536, 100, 1500, 15, true) -- Rock Blast
end)

RegisterEvent(221, "Legacy event 221", function()
    if IsAtLeast(MapVar(53), 1) then return end
    SetValue(MapVar(53), 1)
    evt.SummonMonsters(1, 1, 4, -16130, -4711, 258, 0, 0) -- encounter slot 1 "BGoblin" tier A, count 4, pos=(-16130, -4711, 258), actor group 0, no unique actor name
end)

RegisterEvent(222, "Legacy event 222", function()
    if IsAtLeast(MapVar(54), 1) then return end
    SetValue(MapVar(54), 1)
    evt.SummonMonsters(2, 3, 5, 6864, 17056, 452, 0, 0) -- encounter slot 2 "PeasantM2" tier C, count 5, pos=(6864, 17056, 452), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 5, 7808, 17984, 333, 0, 0) -- encounter slot 2 "PeasantM2" tier C, count 5, pos=(7808, 17984, 333), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 5, 11760, 18784, 97, 0, 0) -- encounter slot 2 "PeasantM2" tier C, count 5, pos=(11760, 18784, 97), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 5, 8488, 16768, 97, 0, 0) -- encounter slot 2 "PeasantM2" tier C, count 5, pos=(8488, 16768, 97), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 5, 13024, 15360, 257, 0, 0) -- encounter slot 1 "BGoblin" tier C, count 5, pos=(13024, 15360, 257), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 5, 11376, 17472, 97, 0, 0) -- encounter slot 1 "BGoblin" tier C, count 5, pos=(11376, 17472, 97), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 5, 14128, 12464, 97, 0, 0) -- encounter slot 1 "BGoblin" tier C, count 5, pos=(14128, 12464, 97), actor group 0, no unique actor name
    evt.SummonMonsters(1, 3, 5, 4976, 16528, 97, 0, 0) -- encounter slot 1 "BGoblin" tier C, count 5, pos=(4976, 16528, 97), actor group 0, no unique actor name
end)

RegisterEvent(225, "Legacy event 225", function()
    if IsAtLeast(MapVar(61), 1) then return end
    AddValue(InventoryItem(1822), 1822) -- Fly
    SetValue(MapVar(61), 1)
end)

RegisterEvent(226, "Legacy event 226", function(continueStep)
    local function Step_0()
        if IsQBitSet(QBit(1326)) then return 8 end -- NPC
        return 1
    end
    local function Step_1()
        if IsAtLeast(ActualMight, 25) then return 5 end
        return 2
    end
    local function Step_2()
        evt.FaceExpression(51)
        return 3
    end
    local function Step_3()
        evt.StatusText("The Sword won't budge!")
        return 4
    end
    local function Step_4()
        return 8
    end
    local function Step_5()
        SetQBit(QBit(1326)) -- NPC
        return 6
    end
    local function Step_6()
        AddValue(InventoryItem(1608), 1608) -- Claymore
        return 7
    end
    local function Step_7()
        evt.SetSprite(339, 1, "swrdstx")
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_10()
        if IsQBitSet(QBit(1326)) then return 7 end -- NPC
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        elseif step == 10 then
            step = Step_10()
        else
            step = nil
        end
    end
end)

RegisterEvent(230, "Legacy event 230", function()
    if IsQBitSet(QBit(1180)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, -6152, -9208, 2700, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(231, "Legacy event 231", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1180)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1180)) -- NPC
        evt.ShowMovie("Name", true)
    else
        return
    end
end)

RegisterEvent(232, "Legacy event 232", function()
    if IsQBitSet(QBit(1180)) then -- NPC
    end
end)

RegisterEvent(240, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _nrh__tf__cehr__")
    SetAutonote(456) -- Obelisk Message # 15: _nrh__tf__cehr__
    SetQBit(QBit(1398)) -- NPC
end, "Obelisk")

RegisterEvent(261, "Shrine of Luck", function()
    if not IsAtLeast(MonthIs, 6) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1237)) then -- NPC
            SetQBit(QBit(1237)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseLuck, 10)
            evt.StatusText("+10 Luck permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseLuck, 3)
        evt.StatusText("+3 Luck permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Luck")

RegisterEvent(65535, "", function()
    return evt.map[111](9)
end)

RegisterEvent(65534, "", function()
    return evt.map[112](8)
end)

RegisterEvent(65533, "", function()
    return evt.map[113](8)
end)

RegisterEvent(65532, "", function()
    return evt.map[114](8)
end)

RegisterEvent(65531, "", function()
    return evt.map[115](8)
end)

RegisterEvent(65530, "", function()
    return evt.map[116](8)
end)

RegisterEvent(65529, "", function()
    return evt.map[117](8)
end)

RegisterEvent(65528, "", function()
    return evt.map[118](8)
end)

RegisterEvent(65527, "", function()
    return evt.map[119](8)
end)

RegisterEvent(65526, "", function()
    return evt.map[226](10)
end)

