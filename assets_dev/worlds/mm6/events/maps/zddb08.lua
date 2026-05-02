-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {46},
    timers = {
    },
})

RegisterEvent(1, "Shard filled caskets.", function()
    evt.StatusText("Barrel is filled with crystal shards (worthless).")
end, "Shard filled caskets.")

RegisterEvent(2, "Sacks.", function()
    evt.StatusText("The sacks are filled with flawed crystal shards (worthless).")
end, "Sacks.")

RegisterEvent(3, "Crystal.", function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(2), 1)
    evt.SetSprite(18, 0, "0")
end, "Crystal.")

RegisterEvent(4, "Crystal.", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(3), 1)
    evt.SetSprite(19, 0, "0")
end, "Crystal.")

RegisterEvent(5, "Crystal.", function()
    if IsAtLeast(MapVar(4), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(4), 1)
    evt.SetSprite(45, 0, "0")
end, "Crystal.")

RegisterEvent(6, "Crystal.", function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(5), 1)
    evt.SetSprite(30, 0, "0")
end, "Crystal.")

RegisterEvent(7, "Crystal.", function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(6), 1)
    evt.SetSprite(32, 0, "0")
end, "Crystal.")

RegisterEvent(8, "Crystal.", function()
    if IsAtLeast(MapVar(7), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(7), 1)
    evt.SetSprite(31, 0, "0")
end, "Crystal.")

RegisterEvent(9, "Crystal.", function()
    if IsAtLeast(MapVar(8), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(8), 1)
    evt.SetSprite(26, 0, "0")
end, "Crystal.")

RegisterEvent(10, "Crystal.", function()
    if IsAtLeast(MapVar(9), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(9), 1)
    evt.SetSprite(27, 0, "0")
end, "Crystal.")

RegisterEvent(11, "Crystal.", function()
    if IsAtLeast(MapVar(10), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(10), 1)
    evt.SetSprite(25, 0, "0")
end, "Crystal.")

RegisterEvent(12, "Crystal.", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(11), 1)
    evt.SetSprite(43, 0, "0")
end, "Crystal.")

RegisterEvent(13, "Crystal.", function()
    if IsAtLeast(MapVar(12), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(12), 1)
    evt.SetSprite(22, 0, "0")
end, "Crystal.")

RegisterEvent(14, "Table with implements atop.", function()
    SetValue(MapVar(26), 0)
    if IsAtLeast(MapVar(2), 1) then
        if not IsAtLeast(MapVar(14), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(14), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(3), 1) then
        if not IsAtLeast(MapVar(15), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(15), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(4), 1) then
        if not IsAtLeast(MapVar(16), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(16), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(5), 1) then
        if not IsAtLeast(MapVar(17), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(17), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(6), 1) then
        if not IsAtLeast(MapVar(18), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(18), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(7), 1) then
        if not IsAtLeast(MapVar(19), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(19), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(8), 1) then
        if not IsAtLeast(MapVar(20), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(20), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(9), 1) then
        if not IsAtLeast(MapVar(21), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(21), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(10), 1) then
        if not IsAtLeast(MapVar(22), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(22), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(11), 1) then
        if not IsAtLeast(MapVar(23), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(23), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(12), 1) then
        if not IsAtLeast(MapVar(24), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 100)
            AddValue(MapVar(24), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(13), 1) then
        if not IsAtLeast(MapVar(25), 1) then
            evt.SimpleMessage("You refine the crystal you harvested (+200 to its value).")
            AddValue(Gold, 200)
            AddValue(MapVar(25), 1)
            SetValue(MapVar(26), 1)
        end
    end
    if IsAtLeast(MapVar(26), 1) then
        return
    end
    evt.StatusText("You see a scattered of refining tools and small crystal shavings.")
end, "Table with implements atop.")

RegisterEvent(15, "Crystal.", function()
    evt.StatusText(" This razor sharp crystal is too immature to harvest.")
    evt.DamagePlayer(7, 4, 2)
end, "Crystal.")

RegisterEvent(16, "Legacy event 16", function()
    if IsAtLeast(MapVar(27), 1) then return end
    evt.StatusText("Someone has gone to a lot of trouble carving all these murals")
    AddValue(MapVar(27), 1)
end)

RegisterEvent(17, "Carved mural.", function()
    evt.StatusText("You study the mural and get a good feeling inside.")
    evt.CastSpell(46, 1, 2, 0, 0, 0, 0, 0, 0) -- Bless
end, "Carved mural.")

RegisterEvent(18, "Cabinet", function()
    evt.StatusText("The cabinet is filled with old and broken harvesting tools.")
end, "Cabinet")

RegisterEvent(19, "Crystal.", function()
    if IsAtLeast(MapVar(13), 1) then return end
    evt.StatusText("You mine the crystal in its raw form (+300 gold).")
    AddValue(Gold, 300)
    SetValue(MapVar(13), 1)
    evt.SetSprite(44, 0, "0")
end, "Crystal.")

