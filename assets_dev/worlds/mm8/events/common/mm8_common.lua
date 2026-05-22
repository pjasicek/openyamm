MM8 = MM8 or {}

MM8.MinutesPerDay = 1440

function MM8.GetMapVar(name, defaultValue)
    return evt.GetMapVar(name, defaultValue or 0)
end

function MM8.SetMapVar(name, value)
    evt.SetMapVar(name, value or 0)
end

function MM8.GetMapFlag(name)
    return MM8.GetMapVar(name, 0) ~= 0
end

function MM8.SetMapFlag(name, enabled)
    MM8.SetMapVar(name, enabled and 1 or 0)
end

function MM8.OpenDimensionDoor()
    if CrossContinents ~= nil
        and CrossContinents.TryDimensionDoorContact ~= nil
        and CrossContinents.TryDimensionDoorContact() then
        return
    end

    evt.OpenDimensionDoor()
end

function MM8.PartyTile()
    local x, y = evt.GetPartyPosition()
    return math.floor(x / 512 + 64), math.floor(64 - y / 512)
end

function MM8.OpenDimensionDoorOnTile(tileX, tileY, latchName)
    evt.ClearDimensionDoorOverlay()

    local partyTileX, partyTileY = MM8.PartyTile()
    local onTile = partyTileX == tileX and partyTileY == tileY

    if onTile and not MM8.GetMapFlag(latchName) then
        MM8.SetMapFlag(latchName, true)
        MM8.OpenDimensionDoor()
    elseif not onTile and MM8.GetMapFlag(latchName) then
        MM8.SetMapFlag(latchName, false)
    end
end

function MM8.HasCurrentPlayerSpell(spellId)
    return PlayerKnowsSpell(nil, spellId)
end

function MM8.UnstoneStatue(spriteId, npcId, addCauriBits)
    evt.ForPlayer(Players.All)
    local hasScroll = HasItem(339)
    local castStoneToFlesh = CurrentEventSpellId() == 40

    if not hasScroll and not castStoneToFlesh then
        evt.ForPlayer(Players.Current)
        return
    end

    if not castStoneToFlesh then
        RemoveItem(339)
    end

    evt.ForPlayer(Players.Current)
    evt.SetSprite(spriteId, 0, "0")

    if addCauriBits then
        SetQBit(QBit(40))
        SetQBit(QBit(430))
    end

    evt.SpeakNPC(npcId)
end

function MM8.TryExchangeGem(exchangeEntries)
    evt.ForPlayer(Players.All)

    for _, entry in ipairs(exchangeEntries or {}) do
        local sourceItemId = entry[1]
        local reward = entry[2]

        if HasItem(sourceItemId) then
            RemoveItem(sourceItemId)

            if reward > 0 then
                AddValue(InventoryItem(reward), reward)
            elseif reward < 0 then
                AddValue(Gold, -reward)
            else
                local itemTypes = {ItemType.Weapon_, ItemType.Armor_, ItemType.Misc, ItemType.Ring_, ItemType.Scroll_}
                local index = PickRandomOption(455, sourceItemId % 250, {1, 2, 3, 4, 5})
                evt.GiveItem(3, itemTypes[index])
            end

            evt.ForPlayer(Players.Current)
            return true
        end
    end

    evt.ForPlayer(Players.Current)
    return false
end

MM8.SeerRecoverableItems = {
    {Item = 539, QBit = 199}, -- Ebonest
    {Item = 540, QBit = 200}, -- Sword of Whistlebone
    {Item = 541, QBit = 201}, -- Axe of Balthazar
    {Item = 603, QBit = 202}, -- Urn of Ashes
    {Item = 604, QBit = 203}, -- Nightshade Brazier
    {Item = 605, QBit = 204}, -- Dragon Leader's Egg
    {Item = 606, QBit = 205}, -- Heart of Fire
    {Item = 607, QBit = 206}, -- Heart of Water
    {Item = 608, QBit = 207}, -- Heart of Air
    {Item = 609, QBit = 208}, -- Heart of Earth
    {Item = 610, QBit = 209}, -- Conflux Key
    {Item = 611, QBit = 210}, -- Lost Book of Kehl
    {Item = 612, QBit = 211}, -- Sarcophagus of Korbu
    {Item = 617, QBit = 212}, -- Power Stone
    {Item = 618, QBit = 213}, -- Power Stone
    {Item = 619, QBit = 214}, -- Pirate Leader's Key
    {Item = 620, QBit = 215}, -- Prison Key
    {Item = 621, QBit = 216}, -- Prison Key
    {Item = 623, QBit = 217}, -- Gem of Restoration
    {Item = 626, QBit = 218}, -- Prophecies of the Sun
    {Item = 627, QBit = 219}, -- Remains of Korbu
    {Item = 629, QBit = 220}, -- Ring of Keys
    {Item = 741, QBit = 221}, -- Dadeross' Letter to Fellmoon
    {Item = 742, QBit = 222}, -- Blackmail Letter
    {Item = 662, QBit = 224}, -- Cannonball of Dominion
    {Item = 616, QBit = 245}, -- Anointed Herb Potion
    {Item = 615, QBit = 246}, -- Drum of Victory
    {Item = 637, QBit = 247}, -- Bone of Doom
    {Item = 614, QBit = 248}, -- Vial of Grave Dirt
    {Item = 613, QBit = 249}, -- Puzzle Box
    {Item = 602, QBit = 282}, -- False Report
    {Item = 516, QBit = 283}, -- Eclipse
}

function MM8.RecoverLostItem()
    support.tryRecoverLostItem(MM8.SeerRecoverableItems)
end

RegisterGlobalEvent(705, "I lost it", function()
    MM8.RecoverLostItem()
end)
