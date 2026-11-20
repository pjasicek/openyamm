-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [5] = {0},
    },
    contextActions = {
    [1] = { kind = "generic_event", source = "opcode" },
    [2] = { kind = "teleport", source = "heuristic" },
    [3] = { kind = "generic_event", source = "opcode" },
    [4] = { kind = "use_switch", source = "title" },
    [5] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [6] = { kind = "generic_event", source = "opcode" },
    },
    textureNames = {"d8s2on"},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.StatusText("The air smells stale and makes you cough.")
    AddValue(MapVar(2), 1)
end)

RegisterEvent(2, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.StatusText("Poisonous spores force you back.")
    evt.DamagePlayer(Players.All, const.Damage.Water, 8)
    evt.MoveToMap(-128, -1152, 0, 0, 0, 0, 0, 0)
    SetValue(MapVar(4), 1)
end)

RegisterEvent(3, "Crumbling boulder.", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.StatusText("The vent brings in fresh air.")
        evt.SetSprite(1, 0, "0")
        evt.SetSprite(2, 0, "0")
        SetValue(MapVar(3), 1)
    end
end, "Crumbling boulder.")

RegisterEvent(4, "Small switch.", function()
    evt.SetTexture(-99, "d8s2on")
    evt.SetDoorState(1, DoorAction.Close)
end, "Small switch.")

RegisterEvent(5, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(6, nil, function(continueStep)
    if continueStep == 5 then
        evt.ForPlayer(Players.All)
        AddValue(Experience, 500)
        AddValue(MapVar(5), 1)
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(5), 1) then
        return
    elseif IsAtLeast(MapVar(3), 1) then
        evt.SetMessage("\"A small nymph comes out of a hole in the floor thanking you for clearing the spores, he shakes your hand vigorously then disappears down the hole (which somehow disappears after him). +500 experience.\"")
        evt._PressAnyKey(6, 5)
    else
        return
    end
end)

