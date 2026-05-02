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

RegisterEvent(2, "Wards and Pendants", function()
    evt.EnterHouse(32) -- Wards and Pendants
end, "Wards and Pendants")

RegisterEvent(3, "Wards and Pendants", nil, "Wards and Pendants")

RegisterEvent(4, "Sanctum", function()
    evt.EnterHouse(75) -- Sanctum
end, "Sanctum")

RegisterEvent(5, "Sanctum", nil, "Sanctum")

RegisterEvent(6, "Profit House", function()
    evt.EnterHouse(109) -- Profit House
end, "Profit House")

RegisterEvent(7, "Profit House", nil, "Profit House")

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1586)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "House of Hawthorne ", function()
    evt.EnterHouse(280) -- House of Hawthorne
end, "House of Hawthorne ")

RegisterEvent(11, "House of Hawthorne ", nil, "House of Hawthorne ")

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1217)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1232)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1247)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1261)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1276)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1291)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1305)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1317)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1329)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1341)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1353)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1364)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1375)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1386)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1396)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1406)
    evt.EnterHouse(1416)
end)

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(77, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(90, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
end, "Hovel of Mist")

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

