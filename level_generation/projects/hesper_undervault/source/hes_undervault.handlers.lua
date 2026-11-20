-- Authored Undervault behaviour. build_undervault.py embeds this file after its generated registrations.
-- Event ids follow design/kreegan_world/zone1/dungeons/UNDERVAULT.md. House ids are the registry's
-- (design/kreegan_world/WORK_PACKAGES/README.md): the Sim Hall 9204 (hesper_stage/skills.yml), the Clinic 9452, the
-- Workshop 9453, the Council Hall 9454, the Archive 9455, the Guardian's Chapel 9456 and the Kept Refuge 9457
-- (hesper_stage/npcs_undervault.yml, with their people). The gallery homes (events 18-25) speak to their residents.
-- The shops, the inn and the bounty board moved up to Landfall (events 3, 4, 5, 7, 8 retired).
-- Filled in by build_undervault.py (its upper-case tokens): the arrivals of Starport Reach's Lift Head and of D2's Water
-- Works passage, the moves to D15's `deep_stair` and to the Scour's `tunnel_arrival` (a status text while that map is
-- not built), whether the Scour is built, and the bulkhead face's cog number.
-- QBits: 100002 M2 done (Odo comes down to the Water Works arch), 100003 M3 done (Aster has spoken for the party: the
-- Council's houses open, CR-P4-14), 100006 M6 done (the Kept Refuge opens; Doctor Ilse in the Clinic), 100115-100118
-- the Scour's camps 1-4 freed (each sends one of its Kept to the Refuge), 100102 S2 done (the Water Works door), 100420
-- the service tunnel used (P1's, with autonote 10102). Map variable 1: the Deep Stair bulkhead opened (it stays open).
-- Monster group 1: Odo (actor 1, invisible until M2).
local handlers = {}

local M3_DONE, M6_DONE, S2_DONE = 100003, 100006, 100102
local TUNNEL_USED, TUNNEL_NOTE = 100420, 10102
local WATER_WORKS = 9040                -- the Water Works door's two ways (hesper_stage/npcs.yml, map-local topics)
local PUMPING_STATION, SERVICE_TUNNEL = 9040, 9041
local NOTICE = "Closed. A notice on the door: 'By the Council's custom, strangers are received after the Guardian "
    .. "has spoken for them.'"

local ODO_GROUP = 1

local function bulkheadOpen()
    return IsAtLeast(MapVar(1), 1)
end

handlers[1] = function()
    if bulkheadOpen() then
        evt.SetTexture(BULKHEAD_COG, "htbulkon")
    end
    if IsQBitSet(QBit(100002)) then           -- Odo by the Water Works arch from M2
        evt.SetMonGroupBit(ODO_GROUP, MonsterBits.Invisible, false)
    end
end

handlers[2] = function()
    -- LIFT_ARRIVAL: build_undervault.py fills in the Lift Head's arrival on Starport Reach (hesper_out1).
    evt.MoveToMap(LIFT_ARRIVAL, "hes_out1.odm")
end

-- An NPC who lives in a house only while a QBit is set (MoveNPC persists in the party; house 0 is nowhere).
local function residentWhile(npc, house, qbit)
    evt.MoveNPC(npc, IsQBitSet(QBit(qbit)) and house or 0)
end

-- The Council's houses: closed to strangers until M3 (UNDERVAULT's CR-P4-14), then entered with their people
-- (hesper_stage/npcs_undervault.yml): the Clinic (Neve; Doctor Ilse from M6), the Sim Hall (Brannoc), the Workshop
-- (Orrin), the Council Hall (Elder Maren), the Archive (Pell). `people`: residents moved in by a QBit.
local HOUSES = {
    [6] = {house = 9452, people = {{9503, M6_DONE}}},              -- the Clinic: Doctor Ilse from M6
    [9] = {house = 9204},                                         -- the Sim Hall
    [10] = {house = 9453},                                        -- the Workshop
    [11] = {house = 9454},                                        -- the Council Hall
    [12] = {house = 9455},                                        -- the Archive
}
for event, door in pairs(HOUSES) do
    handlers[event] = function()
        if not IsQBitSet(QBit(M3_DONE)) then
            evt.StatusText(NOTICE)
            return
        end
        for _, person in ipairs(door.people or {}) do
            residentWhile(person[1], door.house, person[2])
        end
        evt.EnterHouse(door.house)
    end
end

-- The Guardian's Chapel (house 9456, a temple: MM's Donate), open from the first visit: Aster and Iver, her keeper.
handlers[13] = function()
    evt.EnterHouse(9456)
end

-- The Kept Refuge (house 9457), open from M6: Tamsin, Hob and Dree, and one freed Kept from each of the Scour's camps
-- 1-4 once that camp is free (P4's NPCS: Cale, Senna, Rook, Tibb).
local REFUGE, CAMP_KEPT = 9457, {{9576, 100115}, {9577, 100116}, {9578, 100117}, {9579, 100118}}
handlers[14] = function()
    if not IsQBitSet(QBit(M6_DONE)) then
        evt.StatusText("A shack in the Kept Refuge. Tamsin is not here yet.")
        return
    end
    for _, person in ipairs(CAMP_KEPT) do
        residentWhile(person[1], REFUGE, person[2])
    end
    evt.EnterHouse(REFUGE)
end

handlers[15] = function()
    evt.StatusText("Cold, clean water from the Ancient coolant loop.")
end

-- The Water Works door: barred until S2; after it, two ways (CR-P1-5): the door's dialogue offers the Pumping Station
-- and the old service tunnel to the Scour; leaving it is staying.
handlers[16] = function()
    if IsQBitSet(QBit(S2_DONE)) then          -- S2 Pressure done (D2's filter console)
        evt.SpeakNPC(WATER_WORKS)
    else
        evt.StatusText("The Water Works door to the Pumping Station, barred. Odo the plumber says the filters there "
            .. "are choked.")
    end
end

handlers[PUMPING_STATION] = function()
    -- D2_WORKS: build_undervault.py fills in the Pumping Station's arrival in its Water Works passage (hesper_d02).
    evt.MoveToMap(D2_WORKS, "hes_d02.blv")
end

handlers[SERVICE_TUNNEL] = function()
    if SCOUR_BUILT and not IsQBitSet(QBit(TUNNEL_USED)) then      -- the first use from either side
        SetQBit(QBit(TUNNEL_USED))
        SetAutonote(TUNNEL_NOTE)
    end
    SCOUR_TUNNEL()
end

-- The Deep Stair bulkhead (CR-P3-03): a root lock that only Grandmaster Hacking turns (the party's best hacker);
-- opened, its face lights (htbulkon) and stays open, and it leads on to D15 (M14b; 100217 is not needed).
handlers[17] = function()
    if not bulkheadOpen() then
        evt.ForPlayer(Players.All)
        if not evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Grandmaster, 1) then
            evt.StatusText("An Ancient root lock. Nothing you know opens it.")
            return
        end
        SetValue(MapVar(1), 1)                -- the root lock turns: the glyph studs and the seams light cyan
        evt.SetTexture(BULKHEAD_COG, "htbulkon")
    end
    ENTER_D15()
end

-- The gallery homes (events 18-25; the registry's houses 9472-9479 are not house rows): each door speaks to its
-- resident, MM's way with a home (P4's NPCS: Pim and Sabra, then the six gallery residents with their news). The two
-- Kept shacks (events 30, 31) and the other numbers stay quiet.
for event = 18, 31 do
    handlers[event] = function() evt.StatusText("Nobody answers.") end
end

-- Pim's home (the turret keeper) and the go-between Sabra's, their status lines kept as the homes' look.
handlers[18] = function()
    evt.StatusText("The turret keeper's home: tools, Ion Cells on a charging rack, a half-stripped Ward Turret head.")
    evt.SpeakNPC(9551)
end

handlers[19] = function()
    evt.StatusText("The go-between's home: Ashrunner trade goods and a crawler tread hung on the wall.")
    evt.SpeakNPC(9552)
end

-- Kobb, Lissa, Mott, Nara, Oswin and Rhosa (9568-9573).
for event = 20, 25 do
    handlers[event] = function() evt.SpeakNPC(9548 + event) end
end
