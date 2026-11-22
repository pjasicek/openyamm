-- Devil Outpost
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    contextActions = {
    [1] = { kind = "leave_dungeon", source = "opcode", targetMap = "outb1.odm", targetName = "Kriegspire" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Exit", function()
    evt.MoveToMap(-17420, -959, 161, 1920, 0, 0, 0, 6, "outb1.odm") -- Kriegspire
end, "Exit")

