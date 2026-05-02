-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [5] = {0},
    },
    textureNames = {"d8s2on"},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.StatusText("The air smells stale and makes you cough.")
    AddValue(MapVar(2), 1)
end)

RegisterEvent(2, "Legacy event 2", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.StatusText("Poisonous spores force you back.")
    evt.DamagePlayer(5, 2, 8)
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
    evt.SetTexture(99, "d8s2on")
    evt.SetDoorState(1, DoorAction.Close)
end, "Small switch.")

RegisterEvent(5, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(6, "Legacy event 6", function()
    if IsAtLeast(MapVar(5), 1) then
        return
    elseif IsAtLeast(MapVar(3), 1) then
        evt.SimpleMessage("\"A small nymph comes out of a hole in the floor thanking you for clearing the spores, he shakes your hand vigorously then disappears down the hole (which somehow disappears after him). +500 experience.\"")
        evt.ForPlayer(Players.All)
        AddValue(Experience, 500)
        AddValue(MapVar(5), 1)
    else
        return
    end
end)

