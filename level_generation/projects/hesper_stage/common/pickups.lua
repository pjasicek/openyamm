-- Hesper dungeon pickups (design/kreegan_world/PICKUPS.md): the stat canisters and serum vats (MM's stat barrels)
-- and the supply satchels (MM's random floor loot). stage.py installs this file in worlds/hesper/events/common/
-- hesper_common.lua, which the engine runs before every Hesper map script; a map turns its pickups on with one call
-- from its handlers:
--
--     HesperPickups.setup({treasure = 6, canisters = {701, 702}, vats = {}, satchels = {751}, bundles = {}})
--
-- Each pickup is a decoration placed with its event id as both its event and its cog (blv_kit's
-- `decoration(name, x, y, z, facing, event=id, cog=id)`): a container as hes_stim_canister or hes_serum_vat, a
-- satchel as hes_colony_satchel or hes_scrap_bundle. Ids 700-749 are the containers, 750-789 the satchels; setup
-- registers their click events, the on-load event 790 and the refill hook 791. `treasure` (1-6, required) is the
-- map's treasure level: its Hesper loot class (PROGRESSION.md; ITEMS.md: H1 is level 3, H2 level 5, H3 level 6). The
-- map passes it because `evt.GetCurrentMapName()` returns the display title, not the file. The decoration swaps are
-- the map overlay pickup_sprites.lua (HesperPickupSprites), which stage.py installs for every map that calls setup.
--
-- State is in named map variables, which the game saves with the map and clears when the map respawns:
-- "HesperPickups.Rolled" (1 once the colours are rolled) and "HesperPickups.<id>" (a container: its colour 1-7, or
-- EMPTY; a satchel: 0 full, or what it held once opened: GOLD, ITEM or NOTHING).

HesperPickups = HesperPickups or {}

local CONTAINER_IDS = {700, 749}
local SATCHEL_IDS = {750, 789}
local ON_LOAD_EVENT = 790
local REFILL_HOOK = 791
local EMPTY = 8
local GOLD, ITEM, NOTHING = 1, 2, 3

-- MM's barrel colours, in its event order, with the autonote MM sets for each (engine autonote.txt 17-23).
local COLOURS = {
    {name = "red", stat = BaseMight, label = "Might", autonote = 17},
    {name = "yellow", stat = BaseAccuracy, label = "Accuracy", autonote = 21},
    {name = "blue", stat = BasePersonality, label = "Personality", autonote = 19},
    {name = "orange", stat = BaseIntellect, label = "Intellect", autonote = 18},
    {name = "green", stat = BaseEndurance, label = "Endurance", autonote = 20},
    {name = "purple", stat = BaseSpeed, label = "Speed", autonote = 22},
    {name = "white", stat = BaseLuck, label = "Luck", autonote = 23},
}

local CONTAINER_KINDS = {
    canisters = {model = "hes_stim_canister", title = "Stim canister", empty = "Empty canister"},
    vats = {model = "hes_serum_vat", title = "Serum vat", empty = "Empty vat"},
}
local SATCHEL_KINDS = {
    satchels = {model = "hes_colony_satchel", title = "Colony satchel"},
    bundles = {model = "hes_scrap_bundle", title = "Scrap bundle"},
}

-- MM7's random treasure gold by level (SpawnRandomTreasure, generateGold).
local GOLD_RANGE = {{50, 100}, {100, 200}, {200, 500}, {500, 1000}, {1000, 2000}, {2000, 5000}}

local containers = {}           -- id -> its kind (CONTAINER_KINDS entry)
local satchels = {}             -- id -> its kind (SATCHEL_KINDS entry)
local containerIds, satchelIds = {}, {}    -- in setup's order, so a roll is the same for the same seed
local treasure = nil             -- the map's treasure level, from setup

local function stateVar(id)
    return "HesperPickups." .. id
end

local function showContainer(id)
    local state = evt.GetMapVar(stateVar(id), 0)
    local suffix = state >= 1 and state <= #COLOURS and COLOURS[state].name or "empty"
    HesperPickupSprites[containers[id].model .. "_" .. suffix](id)
end

local function showSatchel(id)
    if evt.GetMapVar(stateVar(id), 0) ~= 0 then
        HesperPickupSprites[satchels[id].model .. "_open"](id)
    end
end

-- Every full container takes a colour of the seven, once a visit to a fresh map (first entry or a respawn).
local function roll()
    for _, id in ipairs(containerIds) do
        evt.SetMapVar(stateVar(id), evt.RandomBetween(1, #COLOURS))
    end
    for _, id in ipairs(satchelIds) do
        evt.SetMapVar(stateVar(id), 0)
    end
    evt.SetMapVar("HesperPickups.Rolled", 1)
end

local function showAll()
    for _, id in ipairs(containerIds) do
        showContainer(id)
    end
    for _, id in ipairs(satchelIds) do
        showSatchel(id)
    end
end

local function drink(id)
    local kind = containers[id]
    local state = evt.GetMapVar(stateVar(id), 0)
    local colour = COLOURS[state]
    if colour == nil then
        evt.StatusText(kind.empty)
        return
    end
    AddValue(colour.stat, 2)
    SetAutonote(colour.autonote)
    evt.SetMapVar(stateVar(id), EMPTY)
    showContainer(id)
    evt.StatusText("+2 " .. colour.label .. " permanent")
end

-- MM7's spawn rule: 40 % gold of the map's level, 40 % an item of its level or one below, 20 % nothing.
local function open(id)
    if evt.GetMapVar(stateVar(id), 0) ~= 0 then
        evt.StatusText("Empty.")
        return
    end
    local level = treasure
    local chance = evt.RandomBetween(1, 100)
    if chance <= 40 then
        local amount = evt.RandomBetween(GOLD_RANGE[level][1], GOLD_RANGE[level][2])
        AddValue(Gold, amount)
        evt.StatusText("You found " .. amount .. " gold.")
        evt.SetMapVar(stateVar(id), GOLD)
    elseif chance <= 80 then
        evt.GiveItem(math.max(1, level - evt.RandomBetween(0, 1)), 0, 0)
        evt.SetMapVar(stateVar(id), ITEM)
    else
        evt.StatusText("Empty.")
        evt.SetMapVar(stateVar(id), NOTHING)
    end
    showSatchel(id)
end

local function register(ids, range, kinds, kindName, into, order, handler)
    for _, id in ipairs(ids or {}) do
        assert(id >= range[1] and id <= range[2], "HesperPickups: " .. kindName .. " id " .. id .. " is outside "
            .. range[1] .. "-" .. range[2])
        assert(containers[id] == nil and satchels[id] == nil, "HesperPickups: id " .. id .. " is used twice")
        into[id] = kinds[kindName]
        table.insert(order, id)
        RegisterEvent(id, kinds[kindName].title, function() handler(id) end, kinds[kindName].title)
    end
end

function HesperPickups.setup(placement)
    treasure = placement.treasure
    assert(treasure ~= nil and treasure >= 1 and treasure <= 6, "HesperPickups: setup needs treasure = 1-6")
    register(placement.canisters, CONTAINER_IDS, CONTAINER_KINDS, "canisters", containers, containerIds, drink)
    register(placement.vats, CONTAINER_IDS, CONTAINER_KINDS, "vats", containers, containerIds, drink)
    register(placement.satchels, SATCHEL_IDS, SATCHEL_KINDS, "satchels", satchels, satchelIds, open)
    register(placement.bundles, SATCHEL_IDS, SATCHEL_KINDS, "bundles", satchels, satchelIds, open)
    RegisterMapOnLoadEvent(ON_LOAD_EVENT, "Pickups on load", function()
        if evt.GetMapVar("HesperPickups.Rolled", 0) == 0 then
            roll()
        end
        showAll()
    end)
    -- A respawn clears the named map variables, so the load event above re-rolls already; the hook makes the refill
    -- explicit should a respawn ever keep them.
    RegisterMapRefillHook(REFILL_HOOK, "Pickups refill", function()
        roll()
        showAll()
    end)
end
