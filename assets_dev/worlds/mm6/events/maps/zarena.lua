-- The Arena
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
    evt.MoveToMap(14088, 2800, 96, 1024, 0, 0, 0, 0, "OutD3.Odm")
end, "Exit")

RegisterEvent(5, "Legacy event 5", function()
    evt.SpeakNPC(313) -- Arena Master
end)

