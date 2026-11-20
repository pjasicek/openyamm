-- MMerge smith topics: Make Weapon, Make Armor and Make Item turn one lump of ore into a random item whose treasure
-- level is the ore's tier. MMerge takes whichever ore it finds first on the current character; this takes the best
-- ore anywhere in the party.

local oreTiers = {
    {item = 691, level = 6}, -- MM8 Stalt-laced ore
    {item = 1493, level = 6}, -- MM7 Stalt-laced ore
    {item = 690, level = 5}, -- Erudine-laced ore
    {item = 1492, level = 5},
    {item = 689, level = 4}, -- Kergar-laced ore
    {item = 1491, level = 4},
    {item = 688, level = 3}, -- Phylt-laced ore
    {item = 1490, level = 3},
    {item = 687, level = 2}, -- Siertal-laced ore
    {item = 1489, level = 2},
    {item = 686, level = 1}, -- Iron-laced ore
    {item = 1488, level = 1},
}

local function takeBestOre()
    local memberCount = evt.GetPartyMemberCount()

    for _, ore in ipairs(oreTiers) do
        for playerIndex = 0, memberCount - 1 do
            if PlayerHasItem(playerIndex, ore.item) then
                RemovePlayerItem(playerIndex, ore.item)
                return ore.level
            end
        end
    end

    return nil
end

local function makeOreItem(itemType, doneTextId, refuseTextId)
    local level = takeBestOre()

    if level == nil then
        evt.SetMessage(NPCText(refuseTextId))
        return
    end

    evt.GiveItem(level, itemType)
    evt.SetMessage(NPCText(doneTextId))
end

local smithTopics = {
    {event = 501, title = "Make Weapon", itemType = ItemType.Weapon_, done = 1621, refuse = 1622},
    {event = 502, title = "Make Armor", itemType = ItemType.Armor_, done = 1623, refuse = 1624},
    {event = 503, title = "Make Item", itemType = ItemType.Misc, done = 1625, refuse = 1626},
    {event = 594, title = "Make Weapon", itemType = ItemType.Weapon_, done = 534, refuse = 535},
    {event = 595, title = "Make Armor", itemType = ItemType.Armor_, done = 536, refuse = 537},
    {event = 596, title = "Make Item", itemType = ItemType.Misc, done = 538, refuse = 539},
}

for _, topic in ipairs(smithTopics) do
    RegisterGlobalEvent(topic.event, topic.title, function()
        makeOreItem(topic.itemType, topic.done, topic.refuse)
    end)
end
