-- Hermit's Isle
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterNoOpEvent(1, "Obelisk", "Obelisk")

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-2048, 3453, 2049, 1536, 0, 0, 177, 1, "6t6.blv")
end)

RegisterEvent(100, "Drink from Fountain", function()
    SetValue(Age, 0)
    evt.StatusText("Rejuvination!")
    SetAutonote(439) -- Unnatural aging cured at fountain to the east of Hermit's Isle.
end, "Drink from Fountain")

RegisterEvent(210, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _etecpe__ersoede")
    SetQBit(QBit(1386)) -- NPC
    SetAutonote(444) -- Obelisk Message # 3: _etecpe__ersoede
end, "Obelisk")

