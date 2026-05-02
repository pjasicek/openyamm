-- Caves of the Dragon Riders
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [1] = {1},
    [2] = {2},
    [3] = {3},
    [4] = {4},
    [5] = {5},
    [6] = {6},
    [7] = {7},
    [9] = {8},
    [10] = {9},
    [11] = {10},
    [12] = {11},
    [13] = {12},
    [14] = {13},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(2, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(3, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(4, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(5, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(6, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(7, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(9, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(10, "Legacy event 10", function()
    evt.OpenChest(9)
end)

RegisterEvent(11, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(12, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(13, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(15, "Barrel", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.GiveItem(6, 23, 1607) -- Lionheart Sword
end, "Barrel")

RegisterEvent(16, "Barrel", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    evt.GiveItem(6, ItemType.Armor_, 1680) -- Golden Plate Mail
end, "Barrel")

RegisterEvent(17, "Barrel", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    evt.GiveItem(6, 23, 1610) -- Vanquisher Sword
end, "Barrel")

RegisterEvent(18, "Barrel", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    evt.GiveItem(6, ItemType.Armor_, 1680) -- Golden Plate Mail
end, "Barrel")

RegisterEvent(19, "Barrel", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    evt.GiveItem(6, 25, 1632) -- Grand Poleaxe
end, "Barrel")

RegisterEvent(20, "Barrel", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    evt.GiveItem(6, 26, 1643) -- Titanic Trident
end, "Barrel")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-13551, 4864, 161, 512, 0, 0, 0, 0, "outb1.odm")
end, "Exit")

