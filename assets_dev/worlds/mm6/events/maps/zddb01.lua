-- Dragon's Lair
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    contextActions = {
    [1] = { kind = "leave_dungeon", source = "opcode", targetMap = "outc3.odm", targetName = "Mire of the Damned" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Exit", function()
    evt.MoveToMap(-17962, 20974, 1, 1152, 0, 0, 0, 6, "outc3.odm") -- Mire of the Damned
end, "Exit")

