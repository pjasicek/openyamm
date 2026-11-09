-- Authored Hangar Nine behaviour. build_d00.py embeds this file after its generated door table (DOORS) and before
-- the registrations. Event ids follow design/kreegan_world/zone1/dungeons/D0_HANGAR_NINE.md (redesign 2026-10-22).
-- Map variables: 1 the power on, 2 breaker A closed, 3 breaker B closed, 4 the range lever pulled, 5 and 6 the game
-- day the cell charger last gave its cells (day + 1, low and high byte).
-- QBits: 100004 M4 (the Pilot's core in the cockpit: the derelict is the party's ship); 100204 M4 given (the journal,
-- cleared when the core is fitted); 100040-100043 the Ion Coil, the Nav Matrix, the Energy Core and the Re-entry
-- Emitter fitted; 100233 the black box handed in (the cell charger).
local handlers = {}

local PILOTS_CORE, ENGRAM, SHIELD_CELL = 11489, 11331, 11300
local PILOT = 9001                      -- the Pilot's NPC (hesper_stage/npcs.yml): aboard from 100004
local CORE_FITTED, CORE_GIVEN, BLACK_BOX_DONE = 100004, 100204, 100233
-- The derelict's sockets, MM6's Oracle alcoves in the Hesper style: decoration event -> its swap cog (31-35), its
-- light group (11-15), the part it takes and the QBit that records it.
local SOCKETS = {
    [20] = {name = "cockpit", cog = 31, group = 11, item = PILOTS_CORE, qbit = CORE_FITTED},
    [21] = {name = "coil", cog = 32, group = 12, item = 11474, qbit = 100040},
    [22] = {name = "nav", cog = 33, group = 13, item = 11475, qbit = 100041},
    [23] = {name = "engine", cog = 34, group = 14, item = 11476, qbit = 100042},
    [24] = {name = "ring", cog = 35, group = 15, item = 11477, qbit = 100043},
}
local SOCKET_TEXT = {
    cockpit = {
        dead = "The cockpit socket: a gold cradle in the flight console, empty and dark. Nothing aboard has power.",
        ready = "The cockpit socket glows amber, waiting for a flight core. The Pilot's would fit it.",
        lit = "The Pilot's core sits in the cockpit socket, lit. The flight deck hums.",
        fitted = "You set the Pilot's core into the cradle. The prongs close on it, the console wakes line by line, "
            .. "and the flight deck's lights come up.\n\nThe Pilot: \"There. Oh, that is better. A whole ship "
            .. "round me again, and nothing on fire. She is the same class as mine, Hangar Nine's last lander, "
            .. "sealed in here for a thousand years. She is ours now. Four small parts are missing. We need an ion "
            .. "coil for the drive pod, a navigation matrix for the nose, an energy core for the engine bay and a "
            .. "re-entry emitter for the shield ring. Find them and I will fly us home.\"",
    },
    coil = {
        dead = "The drive pod's coil housing: an empty bay with loose cable ends. No power.",
        ready = "The coil housing's lamp is amber. It wants an ion coil.",
        lit = "The Ion Coil hums in the drive pod's housing.",
        fitted = "The Ion Coil slides into the drive pod's housing and locks. Blue light runs along the pod.\n\nThe "
            .. "Pilot: \"Drive coil seated. The pod reads clean. Here, the colony's training memory for the next "
            .. "one who flies her.\"",
    },
    nav = {
        dead = "The nose's navigation bay: empty slots for a matrix. No power.",
        ready = "The navigation bay's lamp is amber. It wants a navigation matrix.",
        lit = "The Nav Matrix glows in the nose bay, its plates full of stars.",
        fitted = "The Nav Matrix's plates slot into the nose bay one by one and fill with light: star charts, and "
            .. "one line home.\n\nThe Pilot: \"I can see the way back. All the way back. Take this. You have earned "
            .. "it.\"",
    },
    engine = {
        dead = "The engine bay between the nozzles: a cage for a power core, empty. No power.",
        ready = "The engine bay's lamp is amber. It wants an energy core.",
        lit = "The Energy Core burns steady in the engine bay.",
        fitted = "The Energy Core drops into the engine bay's cage. The nozzles tick, warm, and settle into a low "
            .. "roar of idle.\n\nThe Pilot: \"That is a lander's core, and it remembers flying. The Harvester never "
            .. "deserved it. An engram for your trouble.\"",
    },
    ring = {
        dead = "The ventral shield ring's emitter mount, empty. No power.",
        ready = "The shield ring's lamp is amber. It wants a re-entry emitter.",
        lit = "The Re-entry Emitter shines in the ventral shield ring.",
        fitted = "The Re-entry Emitter clicks into the ring. A sheet of pale light runs round the hull's foot and "
            .. "fades.\n\nThe Pilot: \"Re-entry shield green. We will not burn up on the way down, wherever down "
            .. "is. Here.\"",
    },
}

local POWER_COGS = {[121] = "hes_light_pylon", [122] = "hes_wall_light", [124] = "hes_ceiling_light"}
local RANGE_LIGHTS = 123                -- the range's ceiling panels (make_dungeon_plans.py: FIXTURE_COG + 3)
local CORE_FULL, CORE_IDLE = 5, 6       -- the reactor core's two glows (BLV light groups)
local BREAKER_COGS = {101, 102}
local HOSTILE = {10050, 10054, 10090}   -- the drones, the old turrets, the crawlers: hostile to the party here

local function powered()
    return IsAtLeast(MapVar(1), 1)
end

local function showSockets()
    for _, socket in pairs(SOCKETS) do
        local state = "dead"
        if IsQBitSet(QBit(socket.qbit)) then
            state = "lit"
        elseif powered() then
            state = "ready"
        end
        evt.SetSprite(socket.cog, 1, "hes_sock_" .. socket.name .. "_" .. state)
        evt.SetLight(socket.group, state == "lit" and 1 or 0)
    end
end

local function showPower()
    if powered() then
        for cog, model in pairs(POWER_COGS) do evt.SetSprite(cog, 1, model) end
        evt.SetLight(CORE_FULL, 1)
        evt.SetLight(CORE_IDLE, 0)
        for _, cog in ipairs(BREAKER_COGS) do evt.SetTexture(cog, "hcmachon") end
    else
        evt.SetLight(CORE_FULL, 0)
        evt.SetLight(CORE_IDLE, 1)
        for index, cog in ipairs(BREAKER_COGS) do
            if IsAtLeast(MapVar(1 + index), 1) then evt.SetTexture(cog, "hcmachon") end
        end
    end
    showSockets()
end

handlers[1] = function()
    for _, monster in ipairs(HOSTILE) do evt.SetMonsterRelation(monster, 0, 4) end
    if IsAtLeast(MapVar(4), 1) then
        evt.SetSprite(RANGE_LIGHTS, 1, "hes_ceiling_light")
    end
    showPower()
end

-- --- The info panels -------------------------------------------------------------------------------------------
local PANELS = {
    [10] = "Colony Safety Notice: personal shields.\n\nEvery crew garment and emitter carries a personal shield. "
        .. "It takes energy and impact before your body does, and it grows back once you have been out of harm "
        .. "for a few breaths. A Shield Cell refills it. Used on someone with no shield at all, a cell throws up "
        .. "a short emergency field.",
    [11] = "Colony Safety Notice: energy tools.\n\nEnergy tools burn through shields quickly and through bodies "
        .. "faster. A body with its shield down takes half again as much harm from any energy discharge. If your "
        .. "shield fails, get out of the line of fire.",
    [12] = "Technicians' Notice.\n\nTerminals, consoles, locks and alarm posts answer to a trained hand. The parts "
        .. "store's terminal is set for practice: any trained technician can open it. This terminal cannot command machines. No "
        .. "technician can talk a drone out of shooting.",
    [13] = "Militia Notice.\n\nThe colony's four disciplines are energy guns, energy blades, shield technique and "
        .. "systems work. Training memories, engrams, deepen any of them: shards, full engrams and cores. "
        .. "Mastery is taught by the masters of each discipline in the town.",
    [14] = "Posted during the invasion.\n\nThe invaders wear shields of three strengths. Our blades and bolts "
        .. "barely mark the stronger kinds, and no spell touches a raised shield at all. Break the shield with "
        .. "energy weapons, then strike.",
    [15] = "Posted during the invasion.\n\nThe invaders' carrier wave (the crews call it the Hum) dulls every "
        .. "spell cast under it, by half. Knock out its relays and it weakens.",
    [16] = "Hangar Nine, berth 1: colony lander LN-9, the last of her class.\n\nSealed for the evacuation that never "
        .. "came. Laid up with her flight core, drive coil, navigation matrix, engine core and re-entry emitter "
        .. "drawn and sent to the Starport stores. Refit before flight: all five.",
    [17] = "Reactor restart.\n\nClose both breakers, A and B, in either order. The terminal between them can close "
        .. "both at once for a technician. Power returns to the bay, the lander's berth and Hangar Control.",
    [18] = "Hazard: coolant leak.\n\nThe tank farm's coolant line is cracked. The spill eats through boots. Keep out "
        .. "of the pool by the west wall.",
}
for event, text in pairs(PANELS) do
    handlers[event] = function() evt.SimpleMessage(text) end
end

-- --- The lander: its sockets and the flight deck's console ------------------------------------------------------
local function socketHandler(event)
    local socket = SOCKETS[event]
    local text = SOCKET_TEXT[socket.name]
    return function()
        if IsQBitSet(QBit(socket.qbit)) then
            evt.StatusText(text.lit)
            return
        end
        if not powered() then
            evt.StatusText(text.dead)
            return
        end
        if socket.item ~= PILOTS_CORE and not IsQBitSet(QBit(CORE_FITTED)) then
            evt.StatusText("The socket's lock answers to the flight computer, and the cockpit socket is empty.")
            return
        end
        if not HasItem(socket.item) then
            evt.StatusText(text.ready)
            return
        end
        RemoveItem(socket.item)
        SetQBit(QBit(socket.qbit))
        showSockets()
        if socket.item == PILOTS_CORE then
            ClearQBit(QBit(CORE_GIVEN))         -- M4 done: its journal line goes (QBITS: 100204)
        else
            AddValue(InventoryItem(ENGRAM), ENGRAM)
        end
        evt.SimpleMessage(text.fitted)
    end
end
for event in pairs(SOCKETS) do
    handlers[event] = socketHandler(event)
end

-- The flight deck's side console: from M4 done the Pilot speaks here (his topic The repair list counts the parts).
handlers[19] = function()
    if IsQBitSet(QBit(CORE_FITTED)) then
        evt.SpeakNPC(PILOT)
    else
        evt.StatusText("The flight console: a standby lamp, and an empty cradle where the flight core belongs.")
    end
end

-- The cell charger beside the flight deck's hatch (P4's CR-P4-15, the integrator's fix 4; P4's lines, follow-up 38):
-- from the black box (100233) and M4 (100004), one Shield Cell per character once a game day. The day it last gave is
-- kept in map variables 5 and 6 (a map variable holds 0-255), so a new day finds it ready again.
local function chargerDay()
    local day = math.floor(CurrentGameMinutes() / 1440) + 1
    return day % 256, math.floor(day / 256) % 256
end

local function mapVarIs(index, value)
    return IsAtLeast(MapVar(index), value) and not IsAtLeast(MapVar(index), value + 1)
end

handlers[70] = function()
    if not IsQBitSet(QBit(BLACK_BOX_DONE)) or not IsQBitSet(QBit(CORE_FITTED)) then
        evt.StatusText("A cell charger, dark. The Pilot has not keyed it to you.")
        return
    end
    local low, high = chargerDay()
    if mapVarIs(5, low) and mapVarIs(6, high) then
        evt.StatusText("The charger's lamp is amber. Charging; come back tomorrow.")
        return
    end
    SetValue(MapVar(5), low)
    SetValue(MapVar(6), high)
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        AddValue(InventoryItem(SHIELD_CELL), SHIELD_CELL)
    end
    evt.PlaySoundName("cell_charger")         -- the stage's charger sound (the Hesper audio job)
    evt.StatusText("The lander's charger clicks open: a fresh Shield Cell for each of you.")
end

-- --- The Parts Store, the range ------------------------------------------------------------------------------------
-- Any party member with Hacking (Novice, bought at the Warden's Post in Landfall).
local function partyHacks()
    evt.ForPlayer(Players.All)
    return evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Novice, 1)
end

-- The practice terminal: set for a Novice technician.
handlers[25] = function()
    if partyHacks() then
        evt.SetDoorState(DOORS.parts, DoorAction.Open)
        evt.StatusText("Practice terminal: technician access granted. The Parts Store door slides up.")
    else
        evt.StatusText("Practice terminal: ACCESS REFUSED. TECHNICIANS ONLY. (It wants a hand trained in Hacking.)")
    end
end
handlers[44] = function()
    evt.StatusText("Locked. The practice terminal beside the door opens it.")
end

handlers[26] = function()
    evt.SetDoorState(DOORS.range, DoorAction.Open)
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        evt.SetSprite(RANGE_LIGHTS, 1, "hes_ceiling_light")
        evt.StatusText("The shutter grinds up and the range lights buzz on. Something at the far end powers up.")
    end
end

-- --- The reactor: two breakers, or the terminal for both ------------------------------------------------------------
local function powerOn()
    SetValue(MapVar(1), 1)
    showPower()
    evt.SetDoorState(DOORS.control, DoorAction.Open)
    evt.SimpleMessage("The reactor's core flares from a dull red to a hard blue-white. Light pylons blaze up round "
        .. "the bay, the lander's empty sockets glow amber, and far above a seal thumps open: Hangar Control.")
end

local function breaker(index)
    return function()
        if powered() then
            evt.StatusText("The breaker is closed. The reactor hums.")
            return
        end
        if IsAtLeast(MapVar(1 + index), 1) then
            evt.StatusText("This breaker is closed. The other one is still open.")
            return
        end
        SetValue(MapVar(1 + index), 1)
        evt.SetTexture(BREAKER_COGS[index], "hcmachon")
        if IsAtLeast(MapVar(2), 1) and IsAtLeast(MapVar(3), 1) then
            powerOn()
        else
            evt.StatusText("The breaker slams home and its lamps turn green. The core stirs, but holds.")
        end
    end
end
handlers[27], handlers[28] = breaker(1), breaker(2)

-- The terminal closes both breakers for a technician (Hacking).
handlers[29] = function()
    if powered() then
        evt.StatusText("Reactor terminal: output nominal.")
        return
    end
    if not partyHacks() then
        evt.StatusText("Reactor terminal: restart sequence locked. A trained hand could run it; the breakers will do.")
        return
    end
    SetValue(MapVar(2), 1)
    SetValue(MapVar(3), 1)
    powerOn()
end

-- --- Chests and doors ---------------------------------------------------------------------------------------------
for event, chest in pairs({[30] = 0, [31] = 1, [32] = 2, [33] = 3}) do
    handlers[event] = function() evt.OpenChest(chest) end
end
handlers[40] = function() evt.SetDoorState(DOORS.tech, DoorAction.Trigger) end
handlers[41] = function() evt.SetDoorState(DOORS.militia, DoorAction.Trigger) end
handlers[42] = function() evt.SetDoorState(DOORS.reactor, DoorAction.Trigger) end
handlers[43] = function() evt.SetDoorState(DOORS.fuel, DoorAction.Trigger) end
handlers[60] = function()
    if powered() then
        evt.SetDoorState(DOORS.control, DoorAction.Open)
    else
        evt.StatusText("Hangar Control's seal. Dead: no power. The reactor is below.")
    end
end

-- --- Hangar Control ------------------------------------------------------------------------------------------------
handlers[34] = function()
    if IsQBitSet(QBit(CORE_FITTED)) then
        evt.SpeakNPC(PILOT)                 -- the Pilot over the link (CR-P4-15)
    else
        evt.SimpleMessage("The link to berth 1 answers with a single line: FLIGHT CORE ABSENT. Down in the bay, the "
            .. "derelict's cockpit socket waits. The Pilot's core would fit it.")
    end
end
handlers[35] = function()
    evt.SimpleMessage("Roof controls. The bay doors above the lander are locked shut: LAUNCH CLEARANCE REQUIRED. "
        .. "Not yet.")
end

-- --- The way out --------------------------------------------------------------------------------------------------
handlers[50] = function()
    -- SURFACE_ARRIVAL: build_d00.py fills in Starport Reach's arrival at the Crew Ramp door (hesper_out1).
    evt.MoveToMap(SURFACE_ARRIVAL, "hes_out1.odm")
end

-- GetCurrentMapName returns the display title; pass this dungeon's H1/H2 treasure level explicitly.
HesperPickups.setup({
    treasure = 3,
    satchels = {751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768}
})
