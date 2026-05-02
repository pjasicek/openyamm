-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [2] = {1},
    [3] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Bench", function()
    if IsAtLeast(MapVar(2), 1) then return end
    AddValue(MapVar(2), 1)
    evt.StatusText("You find a small wooden dowl.")
end, "Bench")

RegisterEvent(2, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(3, "Crate", function()
    evt.OpenChest(0)
end, "Crate")

