-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Sack", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("You find jerked beef in the sack (+10 food).")
        AddValue(Food, 10)
        AddValue(MapVar(2), 1)
        return
    end
    evt.StatusText("The sack is empty.")
end, "Sack")

RegisterEvent(2, "Stew filled bowl.", function()
    if not IsAtLeast(MapVar(3), 2) then
        evt.StatusText("The stew tasts good - you feel better (+5 hits).")
        AddValue(CurrentHealth, 5)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("The bowl is empty.")
end, "Stew filled bowl.")

RegisterEvent(3, "Crates filled with wood chips.", function()
    evt.StatusText("There is of nothing of value in the crates.")
end, "Crates filled with wood chips.")

RegisterEvent(4, "Mead filled barrel.", function()
    if not IsAtLeast(MapVar(4), 4) then
        evt.StatusText("You drink the mead and are feeling good.")
        AddValue(PoisonedGreen, 5)
        AddValue(MapVar(4), 1)
        return
    end
    evt.StatusText("The mead barrel is empty.")
end, "Mead filled barrel.")

