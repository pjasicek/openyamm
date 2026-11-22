-- The Arena
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    contextActions = {
    [1] = { kind = "leave_dungeon", source = "opcode", targetMap = "OutD3.Odm", targetName = "Castle Ironfist" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Exit", function()
    evt.MoveToMap(14088, 2800, 96, 1024, 0, 0, 0, 1, "OutD3.Odm") -- Castle Ironfist
end, "Exit")

RegisterEvent(5, nil, function()
    evt.SpeakNPC(313) -- Arena Master
end)

