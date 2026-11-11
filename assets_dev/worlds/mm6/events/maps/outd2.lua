-- Bootleg Bay
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {122},
    onLeave = {},
    openedChestIds = {
    [60] = {1},
    [61] = {2},
    [62] = {3},
    [63] = {4},
    [64] = {5},
    },
    contextActions = {
    [2] = { kind = "enter_house", source = "opcode", houseId = 23, targetName = "Hammer and Tongs" },
    [4] = { kind = "enter_house", source = "opcode", houseId = 65, targetName = "Abraham's Metalworks" },
    [6] = { kind = "enter_house", source = "opcode", houseId = 99, targetName = "The Little Magic Shop" },
    [8] = { kind = "enter_house", source = "opcode", houseId = 1587, targetName = "Training-by-the-Sea" },
    [10] = { kind = "enter_house", source = "opcode", houseId = 266, targetName = "The Goblin's Tooth" },
    [12] = { kind = "enter_house", source = "opcode", houseId = 267, targetName = "The Broken Cutlass" },
    [14] = { kind = "enter_house", source = "opcode", houseId = 1595, targetName = "Circus" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 333, targetName = "House of Healing" },
    [16] = { kind = "enter_house", source = "opcode", houseId = 506, targetName = "Valkyrie" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 505, targetName = "Tsunami" },
    [18] = { kind = "enter_house", source = "opcode", houseId = 1596, targetName = "Tent" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 1598, targetName = "Tent" },
    [20] = { kind = "enter_house", source = "opcode", houseId = 1601, targetName = "Tent" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 1597, targetName = "Wagon" },
    [22] = { kind = "enter_house", source = "opcode", houseId = 1599, targetName = "Wagon" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 1600, targetName = "Wagon" },
    [24] = { kind = "generic_event", source = "opcode" },
    [25] = { kind = "generic_event", source = "opcode" },
    [26] = { kind = "generic_event", source = "opcode" },
    [50] = { kind = "enter_house", source = "opcode", houseId = 1224, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1239, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1254, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1269, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1284, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1299, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1312, targetName = "House" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1324, targetName = "House" },
    [58] = { kind = "enter_house", source = "opcode", houseId = 1335, targetName = "House" },
    [59] = { kind = "enter_house", source = "opcode", houseId = 1347, targetName = "House" },
    [60] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [61] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [62] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [63] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [64] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 428, targetName = "Hall of the Fire Lord" },
    [91] = { kind = "enter_house", source = "opcode", houseId = 423, targetName = "Temple of the Fist" },
    [92] = { kind = "enter_house", source = "opcode", houseId = 429, targetName = "Temple of the Sun" },
    [93] = { kind = "enter_house", source = "opcode", houseId = 426, targetName = "Temple of Tsantsa" },
    [94] = { kind = "enter_house", source = "opcode", houseId = 334, targetName = "Temple Baa" },
    [100] = { kind = "well", source = "title" },
    [101] = { kind = "well", source = "title" },
    [102] = { kind = "fountain", source = "title" },
    [103] = { kind = "fountain", source = "title" },
    [220] = { kind = "fountain", source = "title" },
    [221] = { kind = "use_pedestal", source = "title" },
    [223] = { kind = "obelisk", source = "title" },
    [261] = { kind = "shrine", source = "title" },
    },
    learnedEffect = {
    [100] = { autonote = 410, effect = "+20 Might temporary" },
    [102] = { autonote = 411, effect = "+2 Intellect permanent" },
    [103] = { autonote = 412, effect = "+2 Personality permanent" },
    [220] = { autonote = 400, effect = "+20 Spell points restored" },
    },
    textureNames = {},
    spriteNames = {"ped05"},
    castSpellIds = {},
    timers = {
    { eventId = 104, sourceEventId = 104, triggerStep = 0, origin = "legacy", triggerKind = "long", scheduleKind = "monthly" },
    { eventId = 219, sourceEventId = 219, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "weekly" },
    },
})

RegisterEvent(2, "Hammer and Tongs", function()
    evt.EnterHouse(23) -- Hammer and Tongs
end, "Hammer and Tongs")

RegisterEvent(3, "Hammer and Tongs", nil, "Hammer and Tongs")

RegisterEvent(4, "Abraham's Metalworks", function()
    evt.EnterHouse(65) -- Abraham's Metalworks
end, "Abraham's Metalworks")

RegisterEvent(5, "Abraham's Metalworks", nil, "Abraham's Metalworks")

RegisterEvent(6, "The Little Magic Shop", function()
    evt.EnterHouse(99) -- The Little Magic Shop
end, "The Little Magic Shop")

RegisterEvent(7, "The Little Magic Shop", nil, "The Little Magic Shop")

RegisterEvent(8, "Training-by-the-Sea", function()
    evt.EnterHouse(1587) -- Training-by-the-Sea
end, "Training-by-the-Sea")

RegisterEvent(9, "Training-by-the-Sea", nil, "Training-by-the-Sea")

RegisterEvent(10, "The Goblin's Tooth", function()
    evt.EnterHouse(266) -- The Goblin's Tooth
end, "The Goblin's Tooth")

RegisterEvent(11, "The Goblin's Tooth", nil, "The Goblin's Tooth")

RegisterEvent(12, "The Broken Cutlass", function()
    evt.EnterHouse(267) -- The Broken Cutlass
end, "The Broken Cutlass")

RegisterEvent(13, "The Broken Cutlass", nil, "The Broken Cutlass")

RegisterEvent(14, "Circus", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1595) -- Circus
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus")

RegisterEvent(15, "House of Healing", function()
    evt.EnterHouse(333) -- House of Healing
end, "House of Healing")

RegisterEvent(16, "Valkyrie", function()
    evt.EnterHouse(506) -- Valkyrie
end, "Valkyrie")

RegisterEvent(17, "Tsunami", function()
    evt.EnterHouse(505) -- Tsunami
end, "Tsunami")

RegisterEvent(18, "Tent", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1596) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(19, "Tent", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1598) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(20, "Tent", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1601) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(21, "Wagon", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1597) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(22, "Wagon", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1599) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(23, "Wagon", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1600) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(24, "Ironfist Castle", function()
    evt.StatusText("Ironfist Castle")
end, "Ironfist Castle")

RegisterEvent(25, "Freehaven", function()
    evt.StatusText("Freehaven")
end, "Freehaven")

RegisterEvent(26, "Circus (Winter)", function()
    evt.StatusText("Circus (Winter)")
end, "Circus (Winter)")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1224) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1239) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1254) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1269) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1284) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1299) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1312) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1324) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1335) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1347) -- House
end, "House")

RegisterEvent(60, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(61, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(62, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(63, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(64, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, nil, function()
    evt.MoveToMap(-1792, -19, 1, 0, 0, 0, 428, 1, "6d04.blv") -- Hall of the Fire Lord
end)

RegisterEvent(91, "Temple of the Fist", function()
    evt.MoveToMap(0, -2231, 513, 512, 0, 0, 423, 1, "6t2.blv") -- Temple of the Fist
end, "Temple of the Fist")

RegisterEvent(92, "Temple of the Sun", function()
    evt.MoveToMap(-3258, 483, 49, 0, 0, 0, 429, 1, "6t4.blv") -- Temple of the Sun
end, "Temple of the Sun")

RegisterEvent(93, "Temple of Tsantsa", function()
    evt.MoveToMap(2817, -4748, -639, 512, 0, 0, 426, 1, "6t3.blv") -- Temple of Tsantsa
end, "Temple of Tsantsa")

RegisterEvent(94, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

RegisterEvent(100, "Drink from Well.", function()
    if IsAtLeast(MightBonus, 20) then return end
    SetValue(MightBonus, 20)
    evt.StatusText("+20 Might temporary.")
    SetAutonote(410) -- 20 Points of temporary might from the well near the Goblin's Tooth in Bootleg Bay.
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    evt.DamagePlayer(Players.Current, const.Damage.Water, 40)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Well.")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(BaseIntellect, 15) then
        if not IsAtLeast(MapVar(3), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(3), 1)
        AddValue(BaseIntellect, 2)
        evt.StatusText("+2 Intellect permanent.")
        SetAutonote(411) -- 2 Points of permanent intellect from the north fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsAtLeast(BasePersonality, 15) then
        if not IsAtLeast(MapVar(4), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(4), 1)
        AddValue(BasePersonality, 2)
        evt.StatusText("+2 Personality permanent.")
        SetAutonote(412) -- 2 Points of permanent personality from the south fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(104, nil, function()
    SetValue(MapVar(3), 8)
    SetValue(MapVar(4), 8)
end)

RegisterEvent(122, nil, function()
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.SetSprite(347, 1, "ped05")
    end
end)

RegisterEvent(219, nil, function()
    SetValue(MapVar(11), 0)
end)

RegisterEvent(220, "Drink from Fountain of Magic", function()
    if IsQBitSet(QBit(1135)) then -- Drink from the Fountain of Magic and return to Lord Albert Newton in Mist. - NPC
        evt.SetNPCTopic(790, 1, 1371) -- Albert Newton topic 1: Wizards
        SetQBit(QBit(1260)) -- NPC
    end
    if not IsAtLeast(MaxSpellPoints, 0) then
        AddValue(CurrentSpellPoints, 20)
        evt.StatusText("+20 Spell points restored.")
        SetAutonote(400)
        return
    end
    evt.StatusText("Refreshing!")
    SetAutonote(400)
end, "Drink from Fountain of Magic")

RegisterEvent(221, "Pedestal", function()
    if not HasItem(2074) then return end -- Dragon Statuette
    RemoveItem(2074) -- Dragon Statuette
    evt.SetSprite(347, 1, "ped05")
    SetQBit(QBit(1250)) -- NPC
    if not IsQBitSet(QBit(1247)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1246)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> House
    end
end, "Pedestal")

RegisterEvent(223, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1394)) -- NPC
        SetAutonote(452) -- Obelisk Message # 11: d_re_e_Hpfotyhz_
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            d_re_e_Hpfotyhz_")
    evt._PressAnyKey(223, 2)
end, "Obelisk")

RegisterEvent(261, "Shrine of Might", function()
    if not IsAtLeast(MonthIs, 0) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1231)) then -- NPC
            SetQBit(QBit(1231)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseMight, 10)
            evt.StatusText("+10 Might permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseMight, 3)
        evt.StatusText("+3 Might permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Might")

