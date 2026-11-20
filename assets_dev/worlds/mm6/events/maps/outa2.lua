-- Paradise Valley
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    },
    contextActions = {
    [2] = { kind = "enter_house", source = "opcode", houseId = 32, targetName = "Singing Steel" },
    [4] = { kind = "enter_house", source = "opcode", houseId = 75, targetName = "The Enchanted Hauberk" },
    [6] = { kind = "enter_house", source = "opcode", houseId = 109, targetName = "Mighty Magicks" },
    [8] = { kind = "enter_house", source = "opcode", houseId = 1586, targetName = "The Sparring Ground" },
    [10] = { kind = "enter_house", source = "opcode", houseId = 280, targetName = "The Last Chance" },
    [50] = { kind = "enter_house", source = "opcode", houseId = 1217, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1232, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1247, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1261, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1276, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1291, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1305, targetName = "House" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1317, targetName = "House" },
    [58] = { kind = "enter_house", source = "opcode", houseId = 1329, targetName = "House" },
    [59] = { kind = "enter_house", source = "opcode", houseId = 1341, targetName = "House" },
    [60] = { kind = "enter_house", source = "opcode", houseId = 1353, targetName = "House" },
    [61] = { kind = "enter_house", source = "opcode", houseId = 1364, targetName = "House" },
    [62] = { kind = "enter_house", source = "opcode", houseId = 1375, targetName = "House" },
    [63] = { kind = "enter_house", source = "opcode", houseId = 1386, targetName = "House" },
    [64] = { kind = "enter_house", source = "opcode", houseId = 1396, targetName = "House" },
    [65] = { kind = "enter_house", source = "opcode", houseId = 1406, targetName = "House" },
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [76] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [77] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 334, targetName = "Temple Baa" },
    [100] = { kind = "fountain", source = "title" },
    [200] = { kind = "obelisk", source = "title" },
    },
    learnedEffect = {
    [100] = { autonote = 440, effect = "+100 Power temporary" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 65535, sourceEventId = 100, triggerStep = 9, origin = "legacy", triggerKind = "long", scheduleKind = "weekly" },
    },
})

RegisterEvent(2, "Singing Steel", function()
    evt.EnterHouse(32) -- Singing Steel
end, "Singing Steel")

RegisterEvent(3, "Singing Steel", nil, "Singing Steel")

RegisterEvent(4, "The Enchanted Hauberk", function()
    evt.EnterHouse(75) -- The Enchanted Hauberk
end, "The Enchanted Hauberk")

RegisterEvent(5, "The Enchanted Hauberk", nil, "The Enchanted Hauberk")

RegisterEvent(6, "Mighty Magicks", function()
    evt.EnterHouse(109) -- Mighty Magicks
end, "Mighty Magicks")

RegisterEvent(7, "Mighty Magicks", nil, "Mighty Magicks")

RegisterEvent(8, "The Sparring Ground", function()
    evt.EnterHouse(1586) -- The Sparring Ground
end, "The Sparring Ground")

RegisterEvent(9, "The Sparring Ground", nil, "The Sparring Ground")

RegisterEvent(10, "The Last Chance", function()
    evt.EnterHouse(280) -- The Last Chance
end, "The Last Chance")

RegisterEvent(11, "The Last Chance", nil, "The Last Chance")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1217) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1232) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1247) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1261) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1276) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1291) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1305) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1317) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1329) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1341) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1353) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1364) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1375) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1386) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1396) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1406) -- House
end, "House")

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(77, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(90, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

RegisterEvent(100, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        evt.StatusText("+100 Power temporary.")
        SetAutonote(440) -- 100 Hit points and spell points from fountain in the desert in Paradise Valley.
        return
    end
    SubtractValue(MapVar(2), 1)
    AddValue(CurrentSpellPoints, 100)
    AddValue(CurrentHealth, 100)
    evt.StatusText("+100 Power temporary.")
    SetAutonote(440) -- 100 Hit points and spell points from fountain in the desert in Paradise Valley.
end, "Drink from Fountain")

RegisterEvent(200, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1385)) -- NPC
        SetAutonote(443) -- Obelisk Message # 2: nhrh_aherheatvdi
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            nhrh_aherheatvdi")
    evt._PressAnyKey(200, 2)
end, "Obelisk")

RegisterEvent(65535, "", function()
    SetValue(MapVar(2), 10)
end)

