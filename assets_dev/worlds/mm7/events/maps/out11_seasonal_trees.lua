-- Replace the seasonal handler in place to retain its map-load registration.
-- The legacy handler also displays fruit-tree interaction text on arrival.
RegisterEvent(250, nil, function()
    local autumn = evt.CheckSeason(2)
    local winter = not autumn and evt.CheckSeason(3)

    if autumn or winter then
        evt.SetSprite(5, 1, autumn and "7tree14" or "7tree15")
        evt.SetSprite(6, 1, autumn and "7tree17" or "7tree18")
        evt.SetSprite(7, 1, "7tree24")
        evt.SetSprite(10, 0, "0")
    else
        evt.SetSprite(5, 1, "7tree13")
        evt.SetSprite(6, 1, "7tree16")
        evt.SetSprite(7, 1, "7tree22")
        evt.SetSprite(10, 1, "0")
    end

    local fruitSprite = (autumn or winter) and "7tree30" or "0"
    for decorationId = 51, 56 do
        evt.SetSprite(decorationId, 1, fruitSprite)
    end
end)
