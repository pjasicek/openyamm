-- Authored Starport Terminal behaviour. build_d01.py embeds this file after its generated door table (DOORS) and
-- before the registrations. Event ids follow design/kreegan_world/zone1/dungeons/D1_STARPORT_TERMINAL.md.
-- Map variables: 1 power on, 2 breakers thrown in order (0-3), 3 the freight lift's emergency ride used.
-- Variable 4: Custodian defeated; 5/6: the Claim/Service vent packs have woken.
local handlers = {}

local POWERED = 1                -- the light group of the powered strips
local BREAKER_COGS = {101, 102, 103}
local BOARD_COG = 110
local ORDER = {2, 3, 1}          -- the placard's restart order

-- The powered ceiling lights stand unlit (hes_ceiling_light_off) on cog FIXTURE_COG + 1 of make_dungeon_plans.py.
local CEILING_LIGHTS = 121

local function lightsOn()
    evt.SetLight(POWERED, 1)
    evt.SetSprite(CEILING_LIGHTS, 1, "hes_ceiling_light")
end

local function powerOn()
    SetValue(MapVar(1), 1)
    lightsOn()
    evt.SetTexture(BOARD_COG, "hcboardon")
    evt.SetDoorState(DOORS.seal, DoorAction.Open)
    evt.SetMonGroupBit(11, MonsterBits.Invisible, false)
end

handlers[1] = function()
    evt.SetMonGroupBit(11, MonsterBits.Invisible, not IsAtLeast(MapVar(1), 1))
    evt.SetMonGroupBit(5, MonsterBits.Invisible, not IsAtLeast(MapVar(5), 1))
    evt.SetMonGroupBit(9, MonsterBits.Invisible, not IsAtLeast(MapVar(6), 1))
    if IsAtLeast(MapVar(1), 1) then
        lightsOn()
        evt.SetTexture(BOARD_COG, "hcboardon")
        for _, cog in ipairs(BREAKER_COGS) do evt.SetTexture(cog, "hcmachon") end
    else
        evt.SetLight(POWERED, 0)
    end
end

handlers[2] = function()
    -- TERMINAL_ARRIVAL: build_d01.py fills in Starport Reach's arrival in front of the Terminal (hesper_out1).
    evt.MoveToMap(TERMINAL_ARRIVAL, "hes_out1.odm")
end

handlers[3] = function()
    -- After Tear it out (100034) Aster is silent and her posts are dead (P4's ASTER, block 4; follow-up 35).
    if IsQBitSet(QBit(100002)) and not IsQBitSet(QBit(100034)) then
        -- P4's relay_d01 (CR-P4-16, D1's Texts).
        evt.SimpleMessage("Aster, through the relay: \"The drones are quiet. I felt the grid shift when you broke "
            .. "their hold on this place. I am Aster. I keep the last light of this colony, in the chapel below "
            .. "Landfall, in the old town the Hesperians call the Undervault. Come down to me. And bring what the "
            .. "Custodian took from me. You will know it when you hold it.\"")
        if not IsQBitSet(QBit(100003)) then
            SetQBit(QBit(100203))                -- M3 given (the journal), unless M3 is done (QBITS, CR-P4-09)
        end
    else
        evt.StatusText("A dead relay post; something hums inside.")
    end
end

handlers[4] = function()
    evt.SetDoorState(DOORS.shutter, DoorAction.Open)
    evt.StatusText("The shutter grinds up into the wall.")
end

handlers[5] = function()
    if IsAtLeast(MapVar(1), 1) then
        evt.SimpleMessage("Starport level guide\n\nGround: Concourse, Customs, Baggage, Sorting.\n"
            .. "Basement: Power Plant, Drone Control.\nTower: Flight Control.")
    else
        evt.SimpleMessage("Every line reads CANCELED. The last was set by hand.\n\nALL FLIGHTS HELD: "
            .. "THE SKY IS NOT OURS.")
    end
end

handlers[6] = function()
    evt.SetDoorState(DOORS.security, DoorAction.Open)
    evt.StatusText("The Customs console chirps. Somewhere a lock lets go.")
end

for event, chest in pairs({[7] = 0, [8] = 1, [9] = 2, [10] = 3, [11] = 4, [12] = 5, [15] = 6}) do
    handlers[event] = function() evt.OpenChest(chest) end
end

handlers[13] = function()
    evt.SetDoorState(DOORS.lost, DoorAction.Open)
    evt.StatusText("The loose panel slides aside. A draft of stale air.")
end

handlers[14] = function()
    evt.SimpleMessage("Generator restart, in this order only: breaker 2, breaker 3, breaker 1. Never 1 first. It "
        .. "vents the catwalks.")
end

local function breaker(index)
    return function()
        if IsAtLeast(MapVar(1), 1) then
            evt.StatusText("The breaker is closed. The generator hums.")
            return
        end
        local thrown = 0
        for step = 1, 3 do
            if IsAtLeast(MapVar(2), step) then thrown = step end
        end
        if ORDER[thrown + 1] == index then
            SetValue(MapVar(2), thrown + 1)
            evt.SetTexture(BREAKER_COGS[index], "hcmachon")
            if thrown + 1 == 3 then
                powerOn()
                evt.SimpleMessage("The third breaker slams home. The generator roars, strips flicker on all over the "
                    .. "Starport, and somewhere below a heavy seal unlocks.")
            else
                evt.StatusText("The breaker closes with a heavy clunk. Its lamp turns green.")
            end
        else
            SetValue(MapVar(2), 0)
            for _, cog in ipairs(BREAKER_COGS) do evt.SetTexture(cog, "hcmachine") end
            evt.DamagePlayer(Players.All, const.Damage.Fire, 25)
            evt.StatusText("Wrong order! Steam blasts the catwalks and every breaker trips open.")
        end
    end
end
handlers[16], handlers[17], handlers[18] = breaker(1), breaker(2), breaker(3)

handlers[20] = function()
    if IsAtLeast(MapVar(1), 1) then return end
    evt.DamagePlayer(Players.All, const.Damage.Air, 18)
    evt.StatusText("The conveyor plate sparks, then discharges!")
end

handlers[21] = function()
    if IsAtLeast(MapVar(1), 1) then
        evt.SetDoorState(DOORS.lift, DoorAction.Trigger)
        evt.StatusText("The freight lift hums into motion.")
    elseif not IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(3), 1)
        evt.SetDoorState(DOORS.lift, DoorAction.Open)
        evt.StatusText("Emergency power: one ride. The platform lurches and sinks into the dark.")
    else
        evt.StatusText("The controls are dead. The emergency cell is spent.")
    end
end

handlers[22] = function()
    if IsAtLeast(MapVar(4), 1) or not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, false) then return end
    SetValue(MapVar(4), 1)
    evt.SummonItem(11478, 1700, 3000, -768, 0, 1, false)
    evt.SummonItem(11332, 1700, 3000, -768, 0, 1, false)
end

handlers[23] = function()
    handlers[22]()
    if not IsAtLeast(MapVar(1), 1) then
        evt.StatusText("The Drone Control console is dark: no power.")
    elseif IsQBitSet(QBit(100002)) then
        evt.StatusText("The drone hunts are shut down.")
    elseif not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("The Custodian still holds Drone Control.")
    else
        SetQBit(QBit(100002))
        ClearQBit(QBit(100202))                  -- M2 given (the journal): the done event clears it (QBITS)
        evt.SimpleMessage("You find the hunt schedules and cancel them, one by one. Far above, the drones that "
            .. "patrol Landfall's walls turn for home and settle in their racks. The Hesperians will see it.")
    end
end

handlers[25] = function()
    evt.SimpleMessage("Flight control. Through the windows: the ash apron, the dead pylons, the Lift Head and the "
        .. "crater where you came down. The console holds a map of Starport Reach.")
end

for event = 26, 28 do
    handlers[event] = function()
        evt.StatusText("The remote breaker controls are dead. Use the switches in the Power Plant.")
    end
end

handlers[29] = function() evt.SetDoorState(DOORS.maintenance, DoorAction.Trigger) end
handlers[30] = function() evt.SetDoorState(DOORS.sorting, DoorAction.Trigger) end
handlers[31] = function() evt.StatusText("Locked. The Customs console controls it.") end

RegisterEvent(22, "Custodian defeated", handlers[22])
RegisterMapTimerEvent(32, 30, function()
    handlers[22]()
    local x, y, z = evt.GetPartyPosition()
    for _, pack in ipairs({{5, 5, 3200, 2100, 0}, {6, 9, 6800, 1950, -768}}) do
        if not IsAtLeast(MapVar(pack[1]), 1) and (x-pack[3])^2 + (y-pack[4])^2 + (z-pack[5])^2 <= 600^2 then
            SetValue(MapVar(pack[1]), 1)
            evt.SetMonGroupBit(pack[2], MonsterBits.Invisible, false)
        end
    end
end, "Terminal monsters")

-- GetCurrentMapName returns the display title; pass this dungeon's H1/H2 treasure level explicitly.
HesperPickups.setup({
    treasure = 3,
    canisters = {701, 702, 703, 704, 705, 706, 707, 708, 709, 710},
    satchels = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765}
})
