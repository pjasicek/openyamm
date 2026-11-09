-- Authored Pumping Station behaviour. build_d02.py embeds this file before the registrations. Event ids follow
-- design/kreegan_world/zone1/dungeons/D2_PUMPING_STATION.md. Map variables 1-3: valves 1-3 turned; each valve is a
-- decoration on its event (3-5), which also keys its turned model.
-- Variable 4: Queen defeated. Groups 7/8 are the crawler/Gloamling sump packs, released by the second distinct valve.
local handlers = {}

local BRINE_COGS = {201, 202, 203}              -- the water planes at -256, -512 and -640, top first
local GROWTHS = -2                              -- individual BLV light L8 (negative id bypasses MM8 group semantics)
local S2 = 100102                               -- QBit: Pressure (S2) done (QBITS: S*n* done = 100100 + n)

local function drained()
    local count = 0
    for valve = 1, 3 do
        if IsAtLeast(MapVar(valve), 1) then count = count + 1 end
    end
    return count
end

-- A valve's wheel is decoration cog 2 + valve (its event too), its body cog 30 + valve (author_d02_blender.py).
local function showTurned()
    for valve = 1, 3 do
        if IsAtLeast(MapVar(valve), 1) then
            evt.SetSprite(2 + valve, 1, "hes_valve_wheel_turned")
            evt.SetSprite(30 + valve, 1, "hes_valve_body_open")
        end
    end
end

local function lowerTo(count)
    for stage = 1, count do
        evt.SetFacetBit(BRINE_COGS[stage], FacetBits.Invisible + FacetBits.Untouchable, 1)
    end
end

handlers[1] = function()
    lowerTo(drained())
    showTurned()
    evt.SetMonGroupBit(7, MonsterBits.Invisible, drained() < 2)
    evt.SetMonGroupBit(8, MonsterBits.Invisible, drained() < 2)
    if IsAtLeast(MapVar(4), 1) then evt.SetLight(GROWTHS, 0) end
end

handlers[2] = function()
    -- CANYON_ARRIVAL: build_d02.py fills in Starport Reach's arrival at the Pumping Station hatch (hesper_out1).
    evt.MoveToMap(CANYON_ARRIVAL, "hes_out1.odm")
end

local function valve(index)
    return function()
        if IsAtLeast(MapVar(index), 1) then
            evt.StatusText("Cistern drain, valve " .. index .. " of 3: open.")
            return
        end
        SetValue(MapVar(index), 1)
        showTurned()
        local count = drained()
        lowerTo(count)
        if count == 2 then
            evt.SetMonGroupBit(7, MonsterBits.Invisible, false)
            evt.SetMonGroupBit(8, MonsterBits.Invisible, false)
        end
        if count == 3 then
            evt.StatusText("The last valve screeches open. The brine drains away to the cistern floor.")
        else
            evt.StatusText("Cistern drain, valve " .. index .. " of 3. With a long rush the brine drops.")
        end
    end
end
handlers[3], handlers[4], handlers[5] = valve(1), valve(2), valve(3)

handlers[12] = function()
    if IsAtLeast(MapVar(4), 1) or not evt.CheckMonstersKilled(ActorKillCheck.Group, 6, 0, false) then return end
    SetValue(MapVar(4), 1)
    evt.SetLight(GROWTHS, 0)
end

handlers[7] = function()
    handlers[12]()
    if IsQBitSet(QBit(S2)) then
        evt.StatusText("Filters clear. Flow to Undervault: restored.")
        return
    end
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("The beds are choked with glass.")
        return
    end
    SetQBit(QBit(S2))
    ClearQBit(QBit(100222))                  -- S2 given (Odo's Pressure), done here (follow-up 25)
    SetAutonote(10414)                       -- the Water Works door and the tunnel to the Scour
    evt.SetLight(GROWTHS, 0)
    evt.SimpleMessage("You clear the glass from the intakes and reset the filters. The console reads \"Filters "
        .. "clear. Flow to Undervault: restored.\" Somewhere ahead, the Water Works door unlocks.")
end

handlers[8] = function()
    if IsQBitSet(QBit(S2)) then
        -- UNDERVAULT_WORKS: build_d02.py fills in the Undervault's arrival in its Water Works (hesper_undervault).
        evt.MoveToMap(UNDERVAULT_WORKS, "hes_undervault.blv")
    else
        evt.StatusText("The Water Works door. It opens from the other side.")
    end
end

for event, chest in pairs({[9] = 0, [10] = 1, [11] = 2, [13] = 3, [14] = 4}) do
    handlers[event] = function() evt.OpenChest(chest) end
end

RegisterEvent(12, "Glassback Queen defeated", handlers[12])
RegisterMapTimerEvent(15, 30, handlers[12], "Filter Beds")

-- GetCurrentMapName returns the display title; pass this dungeon's H1/H2 treasure level explicitly.
HesperPickups.setup({
    treasure = 3,
    satchels = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760}
})
