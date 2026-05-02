-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {"d3ll6"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 2, repeating = true, intervalGameMinutes = 20, remainingGameMinutes = 20 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.StatusText("Looks like an earthquake hit this mine.")
end)

RegisterEvent(2, "Legacy event 2", function()
    evt.StatusText("The mine shakes and shifts around you.")
    evt.FaceExpression(14)
end)

RegisterEvent(3, "Water filled barrel.", function()
    if not IsAtLeast(MapVar(2), 6) then
        evt.StatusText("Even though the water is dirty it still refreshes.")
        AddValue(CurrentHealth, 2)
        AddValue(MapVar(2), 1)
        return
    end
    evt.StatusText("The dirty water leaves a bad taste in your mouth.")
end, "Water filled barrel.")

RegisterEvent(4, "Water filled barrel.", function()
    if not IsAtLeast(MapVar(3), 6) then
        evt.StatusText("Even though the water is dirty it still refreshes.")
        AddValue(CurrentHealth, 2)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("The dirty water leaves a bad taste in your mouth.")
end, "Water filled barrel.")

RegisterEvent(5, "Looks like an earthquake hit this mine.", function()
    evt.StatusText("The doors seem stuck.")
end, "Looks like an earthquake hit this mine.")

RegisterEvent(6, "Switch", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("As you pull the lever rocks fall from above.")
        evt.SetDoorState(2, DoorAction.Close)
        evt.SetDoorState(1, DoorAction.Close)
        if not IsAtLeast(SpeedBonus, 25) then
            evt.DamagePlayer(5, 4, 15)
            SetValue(MapVar(4), 1)
            return
        end
        evt.StatusText("You were fast enough to dodge the bigger rocks.")
        evt.FaceExpression(33)
    end
    evt.StatusText("The switch is locked in place.")
end, "Switch")

RegisterEvent(7, "Mine", function()
    if not IsAtLeast(MapVar(5), 4) then
        local randomStep = PickRandomOption(7, 2, {2, 5})
        if randomStep == 2 then
            evt.StatusText("You mine the gold with no problem.")
            AddValue(Gold, 350)
        elseif randomStep == 5 then
            evt.StatusText("Some loose debris overhead falls on you.")
            evt.DamagePlayer(5, 4, 18)
        end
        AddValue(MapVar(5), 1)
        return
    end
    evt.SetTexture(166, "d3ll6")
    evt.StatusText("The vein dried up.")
end, "Mine")

RegisterEvent(8, "Mine", function()
    if not IsAtLeast(MapVar(6), 4) then
        local randomStep = PickRandomOption(8, 2, {2, 5})
        if randomStep == 2 then
            evt.StatusText("You mine the gold with no problem.")
            AddValue(Gold, 350)
        elseif randomStep == 5 then
            evt.StatusText("Some loose debris overhead falls on you.")
            evt.DamagePlayer(5, 4, 18)
        end
        AddValue(MapVar(6), 1)
        return
    end
    evt.SetTexture(54, "d3ll6")
    evt.StatusText("The vein dried up.")
end, "Mine")

RegisterEvent(9, "Mine", function()
    if not IsAtLeast(MapVar(7), 4) then
        local randomStep = PickRandomOption(9, 2, {2, 5})
        if randomStep == 2 then
            evt.StatusText("You mine the gold with no problem.")
            AddValue(Gold, 350)
        elseif randomStep == 5 then
            evt.StatusText("Some loose debris overhead falls on you.")
            evt.DamagePlayer(5, 4, 18)
        end
        AddValue(MapVar(7), 1)
        return
    end
    evt.SetTexture(164, "d3ll6")
    evt.StatusText("The vein dried up.")
end, "Mine")

RegisterEvent(10, "Boulders.", function()
    evt.StatusText("This cave-in blocks any further access into the mine.")
end, "Boulders.")

RegisterEvent(11, "Legacy event 11", function()
    if IsAtLeast(MapVar(8), 1) then return end
    evt.StatusText("Small rocks and debris fall from above. ")
    evt.FaceExpression(31)
    AddValue(MapVar(8), 1)
    if not IsAtLeast(SpeedBonus, 25) then
        evt.DamagePlayer(5, 4, 8)
        return
    end
    evt.StatusText("You were fast enough to dodge the bigger rocks.")
    evt.FaceExpression(33)
end)

RegisterEvent(12, "Legacy event 12", function()
    if IsAtLeast(MapVar(9), 1) then return end
    evt.StatusText("Small rocks and debris fall from above. ")
    evt.FaceExpression(31)
    AddValue(MapVar(9), 1)
    if not IsAtLeast(SpeedBonus, 25) then
        evt.DamagePlayer(5, 4, 8)
        return
    end
    evt.StatusText("You were fast enough to dodge the bigger rocks.")
    evt.FaceExpression(33)
end)

