-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    contextActions = {
    [1] = { kind = "generic_event", source = "opcode" },
    [2] = { kind = "generic_event", source = "opcode" },
    [3] = { kind = "use_switch", source = "title" },
    [5] = { kind = "teleport", source = "heuristic" },
    [6] = { kind = "teleport", source = "heuristic" },
    [7] = { kind = "teleport", source = "heuristic" },
    [8] = { kind = "secret_event", source = "heuristic", hidden = true },
    [9] = { kind = "generic_event", source = "opcode" },
    [10] = { kind = "generic_event", source = "opcode" },
    },
    textureNames = {"d8s2on"},
    spriteNames = {"torch01"},
    castSpellIds = {6},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.StatusText("There is a strong smell of gas pervading the air.")
    AddValue(MapVar(2), 1)
end)

RegisterEvent(2, "Small glittering pool.", function()
    if not IsAtLeast(MapVar(3), 4) then
        evt.StatusText("The water cools you down.")
        AddValue(FireResistance, 40)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("\"You drink the water, with no effect.\"")
end, "Small glittering pool.")

RegisterEvent(3, "Switch.", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("The torches Ignite and so does the swamp gas.")
        evt.SetTexture(-225, "d8s2on")
        evt.CastSpell(6, 0, 1, -3004, -2315, 120, -3244, -2315, 120) -- Fireball
        evt.DamagePlayer(Players.All, const.Damage.Magic, 20)
        evt.SetSprite(1, 1, "torch01")
        evt.SetSprite(2, 1, "torch01")
        evt.SetSprite(3, 1, "torch01")
        evt.SetSprite(4, 1, "torch01")
        evt.SetSprite(5, 1, "torch01")
        evt.SetSprite(6, 1, "torch01")
        evt.SetSprite(7, 1, "torch01")
        evt.SetSprite(8, 1, "torch01")
        evt.SetSprite(9, 1, "torch01")
        evt.SetSprite(10, 1, "torch01")
        evt.SetSprite(11, 1, "torch01")
        evt.SetSprite(12, 1, "torch01")
        evt.SetSprite(13, 1, "torch01")
        evt.SetSprite(14, 1, "torch01")
        evt.SetSprite(15, 1, "torch01")
        evt.SetSprite(16, 1, "torch01")
        evt.SetSprite(17, 1, "torch01")
        evt.SetSprite(18, 1, "torch01")
        evt.SetSprite(19, 1, "torch01")
        evt.SetSprite(20, 1, "torch01")
        evt.SetSprite(21, 1, "torch01")
        evt.SetSprite(22, 1, "torch01")
        evt.SetSprite(23, 1, "torch01")
        evt.SetSprite(24, 1, "torch01")
        SetValue(MapVar(4), 1)
        SetValue(MapVar(5), 1)
        return
    end
    evt.StatusText("The switch does not work.")
end, "Switch.")

RegisterEvent(5, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.StatusText("Swamp gas forces you back couching and gagging.")
    evt.DamagePlayer(Players.All, const.Damage.Water, 8)
    evt.MoveToMap(-1328, -704, 0, 0, 0, 0, 0, 0)
end)

RegisterEvent(6, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.StatusText("Swamp gas forces you back couching and gagging.")
    evt.DamagePlayer(Players.All, const.Damage.Water, 8)
    evt.MoveToMap(-2128, -1152, 0, 0, 0, 0, 0, 0)
end)

RegisterEvent(7, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.StatusText("Swamp gas forces you back couching and gagging.")
    evt.DamagePlayer(Players.All, const.Damage.Water, 8)
    evt.MoveToMap(-1888, -1600, 0, 0, 0, 0, 0, 0)
end)

RegisterEvent(8, nil, function()
    evt.StatusText("Hundreds of snakes crawl out of the floor and bite you.")
    evt.DamagePlayer(Players.All, const.Damage.Water, 15)
end)

RegisterEvent(9, nil, function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.StatusText("A voice hisses -Walk the path of the snake-.")
    AddValue(MapVar(6), 1)
end)

RegisterEvent(10, nil, function(continueStep)
    if continueStep == 3 then
        evt.ForPlayer(Players.All)
        AddValue(Experience, 750)
        AddValue(MapVar(7), 1)
        return
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(7), 1) then return end
    evt.SetMessage("\"A voice whispers -I am the spirit of the swamp, congratulations, take what you may and leave in peace-\"")
    evt._PressAnyKey(10, 3)
end)

