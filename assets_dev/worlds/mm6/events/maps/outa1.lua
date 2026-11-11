-- Sweet Water
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {104},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    },
    contextActions = {
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 421, targetName = "The Hive" },
    [100] = { kind = "well", source = "title" },
    [101] = { kind = "fountain", source = "title" },
    [102] = { kind = "fountain", source = "title" },
    [103] = { kind = "use_pedestal", source = "title" },
    [204] = { kind = "enter_house", source = "opcode", houseId = 1216, targetName = "House" },
    [205] = { kind = "enter_house", source = "opcode", houseId = 1231, targetName = "House" },
    [210] = { kind = "obelisk", source = "title" },
    },
    learnedEffect = {
    [102] = { autonote = 441, effect = "+50 Seven Statistic temporary" },
    },
    textureNames = {},
    spriteNames = {"ped02"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(90, "The Hive", function()
    if IsQBitSet(QBit(1261)) then return end -- NPC
    evt.MoveToMap(435, 3707, 1, 512, 0, 0, 421, 1, "hive.blv") -- The Hive
end, "The Hive")

RegisterEvent(100, "Drink from Well.", function()
    evt.DamagePlayer(Players.Current, const.Damage.Water, 200)
    SetValue(Paralyzed, 0)
    evt.StatusText("Poison!")
end, "Drink from Well.")

RegisterEvent(101, "Drink from Fountain", function()
    evt.DamagePlayer(Players.Current, const.Damage.Water, 200)
    SetValue(Paralyzed, 0)
    evt.StatusText("Poison!")
end, "Drink from Fountain")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(MightBonus, 50) then
        SetValue(MightBonus, 50)
        SetValue(IntellectBonus, 50)
        SetValue(PersonalityBonus, 50)
        SetValue(EnduranceBonus, 50)
        SetValue(SpeedBonus, 50)
        SetValue(AccuracyBonus, 50)
        SetValue(LuckBonus, 50)
        evt.StatusText("+50 Seven Statistic temporary.")
        SetAutonote(441) -- 50 Points of temporary might, accuracy, endurance, speed, personality, intellect, and luck from the fountain southwest of the village of Sweet Water.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Pedestal", function()
    if not HasItem(2070) then return end -- Tiger Statuette
    RemoveItem(2070) -- Tiger Statuette
    evt.SetSprite(606, 1, "ped02")
    SetQBit(QBit(1246)) -- NPC
    if not IsQBitSet(QBit(1247)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> House
    end
end, "Pedestal")

RegisterEvent(104, nil, function()
    if IsQBitSet(QBit(1246)) then -- NPC
        evt.SetSprite(606, 1, "ped02")
    end
end)

RegisterEvent(204, "House", function()
    evt.EnterHouse(1216) -- House
end, "House")

RegisterEvent(205, "House", function()
    evt.EnterHouse(1231) -- House
end, "House")

RegisterEvent(210, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1384)) -- NPC
        SetAutonote(442) -- Obelisk Message # 1: Itotecthothesaip
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            Itotecthothesaip")
    evt._PressAnyKey(210, 2)
end, "Obelisk")

