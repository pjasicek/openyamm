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

RegisterEvent(1, "Exit", function()
    evt.MoveToMap(14088, 2800, 96, 1024, 0, 0, 0, 0)
end, "Exit")

RegisterEvent(5, "Legacy event 5", function()
    evt.SpeakNPC(1092) -- Runaway Chaos
end)

