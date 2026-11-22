-- Hermit's Isle
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    },
    contextActions = {
    [1] = { kind = "obelisk", source = "title" },
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [76] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 433, targetName = "Supreme Temple of Baa" },
    [100] = { kind = "fountain", source = "title" },
    [210] = { kind = "obelisk", source = "title" },
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

RegisterEvent(90, nil, function()
    evt.MoveToMap(-2048, 3453, 2049, 1536, 0, 0, 433, 5, "6t6.blv") -- Supreme Temple of Baa
end)

RegisterEvent(100, "Drink from Fountain", function()
    SetValue(Age, 0)
    evt.StatusText("Rejuvination!")
    SetAutonote(439) -- Unnatural aging cured at fountain to the east of Hermit's Isle.
end, "Drink from Fountain")

RegisterEvent(210, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1386)) -- NPC
        SetAutonote(444) -- Obelisk Message # 3: _etecpe__ersoede
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _etecpe__ersoede")
    evt._PressAnyKey(210, 2)
end, "Obelisk")

