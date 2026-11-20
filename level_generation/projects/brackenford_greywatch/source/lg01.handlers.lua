-- Authored map behavior. Reused MM8 house instances are supplied by the generated town inventory.
local handlers = {}
handlers[1] = function()
    evt.MoveToMap(0, -512, 768, 512, 0, 0, 0, 0, "lg02.blv")
end
for chestIndex = 0, 3 do
    local targetChest = chestIndex
    handlers[201 + chestIndex] = function()
        evt.OpenChest(targetChest)
    end
end
handlers[301] = function()
    SetValue(MapVar(11), 1)
    evt.StatusText("ethesunsh")
end
handlers[302] = function()
    if not IsAtLeast(MightBonus, 25) then
        AddValue(MightBonus, 25)
        evt.StatusText("Might +25 (Temporary)")
    else
        evt.StatusText("Refreshing")
    end
end
handlers[2] = function()
    evt.MoveToMap(5632, -3200, 0, 512, 0, 0, 0, 0, "lg02.blv")
end
for eventId, houseId in pairs(LG.houses) do
    local targetHouse = houseId
    handlers[eventId] = function()
        evt.EnterHouse(targetHouse)
    end
end

handlers[303] = function()
    evt.StatusText("Refreshing")
end

-- Shared supply resets at the next game-day boundary, including after leaving/reloading the map.
-- Named map state avoids consuming legacy byte variables or touching original campaign fountains.
handlers[304] = function()
    local day = math.floor(CurrentGameMinutes() / 1440)
    if evt.GetMapVar("Brackenford.Fountain.Day", -1) ~= day then
        evt.SetMapVar("Brackenford.Fountain.Day", day)
        evt.SetMapVar("Brackenford.Fountain.Uses", 0)
    end
    local uses = evt.GetMapVar("Brackenford.Fountain.Uses", 0)
    if uses >= 40 then
        evt.StatusText("The fountain will recover tomorrow.")
        return
    end
    AddValue(CurrentHealth, 15)
    AddValue(CurrentSpellPoints, 15)
    evt.SetMapVar("Brackenford.Fountain.Uses", uses + 1)
    evt.StatusText("Restored 15 health and mana. " .. tostring(39 - uses) .. " uses remain today.")
end
