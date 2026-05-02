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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
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
    evt.EnterHouse(1416) -- House
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

RegisterEvent(200, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            nhrh_aherheatvdi")
    SetQBit(QBit(1385)) -- NPC
    SetAutonote(443) -- Obelisk Message # 2: nhrh_aherheatvdi
end, "Obelisk")

