-- The Xeen world's hand-written helpers (owner: A3, devdocs/xeen/lanes/A3.md). Prepended to the global program and
-- to every Xeen map's program (game/data/MapScriptSources.cpp, buildLuaWorldCommonPathCandidates). The quest topics
-- and map hooks are generated into xeen_quests.lua (tools/xeen/gen_quests.py), which calls these helpers by name.
-- Format and rules: devdocs/xeen/formats/QUESTS_FORMAT.md. Qbits are looked up by name (Xeen.qbit("m7.sigil")) from
-- the generated XeenQuests.qbits, so no number is written twice.

Xeen = Xeen or {}
XeenQuests = XeenQuests or {}
XeenQuests.hooks = XeenQuests.hooks or {}
XeenQuests.qbits = XeenQuests.qbits or {}

-- A quest bit by its quest-file name ("m4.done"); an unknown name is a status-line error and nil.
function Xeen.qbit(name)
    local value = XeenQuests.qbits[name]
    if value == nil then
        evt.StatusText("Unknown Xeen quest bit: " .. tostring(name))
    end
    return value
end

function Xeen.isSet(name)
    local value = Xeen.qbit(name)
    return value ~= nil and IsQBitSet(QBit(value))
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Map hooks (QUESTS_FORMAT.md section 7). A map event calls XeenQuests.hook("m2.invoice_crate"); a door asks
-- XeenQuests.can(name) first. A hook runs once when it has a `once` qbit, and returns whether it ran.

function XeenQuests.can(name)
    local hook = XeenQuests.hooks[name]
    if hook == nil then
        return false
    end
    return hook.requires == nil or hook.requires()
end

-- A status line held by its length, as gen_quests' status lines and the studio's statusLine: over 30 characters 2
-- seconds and one more for each 15 characters, at most 6.
function XeenQuests.statusLine(text)
    if #text <= 30 then
        evt.StatusText(text)
    else
        evt.StatusText(text, math.max(2, math.min(6, 2 + #text // 15)))
    end
end

function XeenQuests.hook(name)
    local hook = XeenQuests.hooks[name]
    if hook == nil then
        evt.StatusText("Unknown Xeen quest hook: " .. tostring(name))
        return false
    end
    if hook.once ~= nil and IsQBitSet(QBit(hook.once)) then
        if hook.elseText ~= nil then
            if hook.elseStatus then
                XeenQuests.statusLine(hook.elseText())
            else
                evt.SimpleMessage(hook.elseText())
            end
        end
        return false
    end
    if hook.requires ~= nil and not hook.requires() then
        if hook.failText ~= nil then
            if hook.failStatus then
                XeenQuests.statusLine(hook.failText())
            else
                evt.SimpleMessage(hook.failText())
            end
        end
        return false
    end
    hook.run()
    return true
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Promotions (QUESTS section 3). MM9's composite model (worlds/mm9/events/common/mm9_common.lua MM9.Promotions): each
-- promotion quest promotes every member of the class lines it serves. Keys: canonical class names, compared case- and
-- space-blind. Tier 1 on Cloudside; tier 2 on Darkside with the Light or Dark choice per character (engine O2: until
-- it lands, a Light quest and a Dark quest of one line are both offered and the first one taken wins, because the
-- member is no longer of the tier-1 class).

Xeen.Promotions = {
    -- tier 1
    crusade = {Knight = "Cavalier", Paladin = "Crusader", Ranger = "Hunter"},          -- T1-A: M4, Valia
    pendant = {Sorcerer = "Wizard", Archer = "WarriorMage"},                           -- T1-B: Q-C2, Barok
    seasons = {Druid = "GreatDruid", Cleric = "Priest"},                               -- T1-C: Q-C10, the druids
    pagoda = {Monk = "Initiate"},                                                      -- T1-D: Q-C4, Kai Wu
    tiara = {Thief = "Rogue"},                                                         -- T1-E: Q-C3, Roxanne
    -- tier 2, Light
    dimitri = {Cavalier = "Champion"},                                                 -- Kalindra dungeon
    heretics = {Crusader = "Hero", Priest = "PriestLight"},                            -- Q-D6
    sprites = {Hunter = "RangerLord"},                                                 -- Q-D10 polite
    statuettes = {WarriorMage = "MasterArcher"},                                       -- Q-D20
    leafpoint = {GreatDruid = "ArchDruid"},                                            -- Leafpoint, D4
    drawkcab = {Initiate = "Master"},                                                  -- Q-D3
    quarter = {Rogue = "Spy"},                                                         -- Q-D14
    jewel = {Wizard = "ArchMage"},                                                     -- Q-D18
    -- tier 2, Dark
    knights = {Cavalier = "BlackKnight", Crusader = "Villain"},                        -- Q-D17 with the knights
    bounty = {Hunter = "BountyHunter"},                                                -- Q-D11 burn the forts
    southern = {WarriorMage = "Sniper", Rogue = "Assassin"},                           -- Q-D19
    sandro = {Priest = "PriestDark", Wizard = "Lich", Necromancer = "Lich"},           -- Q-D23 (QUESTS 3.2: the MMerge
                                                                                       -- Necromancer line, Human)
    coven = {GreatDruid = "Warlock"},                                                  -- Q-D22 join
    clan = {Initiate = "Ninja"},                                                       -- Q-C4 side with the clan
    -- racial
    minotaur = {Minotaur = "MinotaurLord"},                                            -- Q-D25
    troll = {Troll = "WarTroll"},                                                      -- Q-D13
    vampire = {Vampire = "Nosferatu"},                                                 -- Q-C7
    dragon = {Dragon = "GreatWyrm"},                                                   -- Q-C25
    elf = {DarkElf = "Patriarch"},                                                     -- Q-C17
}

local function classKey(name)
    return (string.gsub(string.lower(tostring(name or "")), "[%s_%-]", ""))
end

function Xeen.promotionTarget(key, playerIndex)
    local lines = Xeen.Promotions[key]
    if lines == nil then
        return nil
    end
    local current = classKey(GetPlayerClassName(playerIndex))
    for from, to in pairs(lines) do
        if classKey(from) == current then
            return to
        end
    end
    return nil
end

function Xeen.canPromote(key)
    for _, playerIndex in ipairs(PartyMembers()) do
        if Xeen.promotionTarget(key, playerIndex) ~= nil then
            return true
        end
    end
    return false
end

-- Promotes every eligible member; returns how many.
function Xeen.promote(key)
    local promoted = 0
    for _, playerIndex in ipairs(PartyMembers()) do
        local target = Xeen.promotionTarget(key, playerIndex)
        if target ~= nil and SetPlayerClass(playerIndex, target) then
            promoted = promoted + 1
        end
    end
    return promoted
end

-- The Seasons Relay's renewal (Q-C1): every member's magical age goes back to none (the engine's Age variable is the
-- age a character has gained or lost by magic, as MM6-MM8's fountains and curses set it).
function Xeen.renewAges()
    evt.ForPlayer(Players.All)
    SetValue(Age, 0)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Staged places by qbit (QUESTS 4.1, 4.2; the cursed towns; Darkside's failing sun). A stage is the highest entry
-- whose qbit is set (0 when none is). Map lanes show and hide BModel groups, faces and actor groups from
-- Xeen.stageOf(name) in their on-load events; houses that open by stage ask the same.

Xeen.Stages = {
    newcastle = {"m9.walls", "m11.keep", "m22.dungeon"},                 -- 1 walls, 2 keep, 3 dungeon dug
    kalindra = {"m19.stage1", "m19.stage2", "m26.stage3", "m26.stage4"}, -- 5, 10, 15, 20 Energy Disks
    darkside_sun = {"m17.done", "m27.done", "m33.done"},                 -- 1 fading, 2 failing, 3 restored
    asp = {"q-c5.done"},
    winterkill = {"q-c6.done"},
    nightshadow = {"q-c7.done"},
    lakeside = {"q-d22.done"},
}

function Xeen.stageOf(name)
    local stages = Xeen.Stages[name]
    if stages == nil then
        evt.StatusText("Unknown Xeen stage: " .. tostring(name))
        return 0
    end
    local stage = 0
    for index, qbitName in ipairs(stages) do
        local value = XeenQuests.qbits[qbitName]
        if value ~= nil and IsQBitSet(QBit(value)) then
            stage = index
        end
    end
    return stage
end

-- Darkside's sky by the sun's stage (WORLD_DESIGN 1.2 and 4; sky presets are A6's aliases, 2026-11-20): xeendark1
-- from the start, xeendark2 at M17, xeendark3 at M27, xeendark1 again at M33. Only Darkside ODMs call this (their
-- on-load events); Cloudside keeps its own sky.
Xeen.DarksideSkies = {[0] = "xeendark1", [1] = "xeendark2", [2] = "xeendark3", [3] = "xeendark1"}

function Xeen.applyDarksideSky()
    evt.SetOutdoorSky(Xeen.DarksideSkies[Xeen.stageOf("darkside_sun")])
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Falls from the sky maps (D-6.2): X8's edges drop the party onto X1 or X3, X9's onto the land below, and X2's lake
-- landing is soft. The party arrives above the ground and falls the rest of the way, so the engine's own fall damage
-- applies (Party.cpp: height x (max HP / 10) / 256 per member, so 850 takes about a third of each member's hit
-- points at any level) and Feather Fall spares whoever has it. A landing on water (onWater true) arrives at the
-- surface: no fall, no damage. x, y, groundZ: the landing point and its ground (or water) height in game units; yaw as
-- evt.MoveToMap takes it; map: the target map's file name ("xeen_x1.odm").

Xeen.SkyFallHeight = 850

function Xeen.skyFall(x, y, groundZ, yaw, map, onWater)
    local z = groundZ
    if not onWater then
        z = groundZ + Xeen.SkyFallHeight
    end
    -- direct: no leave-the-dungeon dialogue when the fall starts in a BLV; keepHeight: arrive at z in the air and fall.
    evt.MoveToMap(x, y, z, yaw, 0, 0, 0, 0, map, {direct = true, keepHeight = not onWater})
end

-- Named falls: a sky map's edges and gaps drop the party at one point below (D-6.4, D-37). The map's fall event
-- calls Xeen.skyFallTo("x9"). X9's land on X2's Darzog island, entrance:x9_fall, facing east (D-50 change 4, kept by
-- D-54: the lake dragons' leash circles stay at least 5,888 from every fall landing and Darzog's door). P5's ring,
-- causeway and shrine land on X5's Darkstone rock top, entrance:p5_fall, facing the tower door 480 ahead (south;
-- D-56 Q3; A6 put the point on the whole cell (55, 59), 256 north of D-56's (-4608, 2304)).
-- D7's six fall zones (D-58 Q10): the sky over the Darkside is cut in a 3 x 2 grid of the source's squares (A-B, C-D, E-F
-- from west to east; rows 1-2 north of y 0, rows 3-4 south), one landing per map beneath, entrance:d7_fall (D7's L1
-- NOTES "Falls"; each map's owner confirms its point at install). P2's islands fall back onto its own Gale Landing
-- (D-58 P2 Q1: the same map, from Xeen.SkyFallHeight above it, with falling damage).
Xeen.SkyFalls = {
    x9 = {-15360, 3072, 768, 0, "xeen_x2.odm"},
    p5 = {-4608, 2560, 1504, 1536, "xeen_x5.odm"},
    d7_ab12 = {13824, -7680, 1672, 1536, "xeen_d6.odm"},   -- A1-B2: before the Necropolis' gate
    d7_cd12 = {1024, -4608, 1600, 1536, "xeen_d5.odm"},    -- C1-D2: by the Great Pyramid (A6's installed point)
    d7_ef12 = {5632, -13312, 1120, 1024, "xeen_d4.odm"},   -- E1-F2: Lakeside's square
    d7_ab34 = {-6656, 6144, 1152, 1536, "xeen_d1.odm"},    -- A3-B4: north of Lucio's Jetty
    d7_cd34 = {15872, -6656, 1056, 1536, "xeen_d2.odm"},   -- C3-D4: before the Southern Tower's door
    d7_ef34 = {-15360, 11776, 1312, 0, "xeen_d3.odm"},     -- E3-F4: outside Sandcaster's south gate (D3's installed entrance:d7_fall)
    p2 = {-4096, -4096, 0, 256, "xeen_p2.blv"},            -- P2: the Gale Landing
}

-- D7's fall event (below z -1,000, and the room's floor) calls Xeen.skyFallD7(): the zone under the party picks the map.
-- The room is 128 x 88 cells (x -32768..32768, y -22528..22528); the columns split x in thirds.
function Xeen.skyFallD7()
    local x, y = evt.GetPartyPosition()
    local column = "ab"
    if x >= 10923 then
        column = "ef"
    elseif x >= -10923 then
        column = "cd"
    end
    local row = y >= 0 and "12" or "34"
    Xeen.skyFallTo("d7_" .. column .. row)
end

function Xeen.skyFallTo(key)
    local fall = Xeen.SkyFalls[key]
    if fall == nil then
        evt.StatusText("Unknown fall: " .. tostring(key))
        return
    end
    Xeen.skyFall(fall[1], fall[2], fall[3], fall[4], fall[5], false)
end

-- The world rim (P2 feedback F29, 2026-11-23; U-12): under a rim map's cliff lies the void (the sea that stood for the
-- stars until the void was built), and nobody is stranded in it. Each rim map's timer event
-- (level_generation/projects/xeen/common/wild.py, every second, not while flying) calls Xeen.rimFall(seas, points):
-- seas are the rim's polygons (the void, or the old sea) in game units, points the map's return points on the rim top
-- {x, y, groundZ, yaw}. A party over a sea (at any height), or within Xeen.RimFallMargin of one
-- and below Xeen.RimFallDepth (the rim's foot, a hole beside a waterfall), is put back over the nearest point and
-- falls Xeen.SkyFallHeight (the engine's fall damage; Feather Fall spares).
Xeen.RimFallDepth = 320
Xeen.RimFallMargin = 1024

local function insidePolygon(polygon, x, y)
    local inside = false
    local count = #polygon
    for index = 1, count do
        local a = polygon[index]
        local b = polygon[index == 1 and count or index - 1]
        if (a[2] > y) ~= (b[2] > y) and x < (b[1] - a[1]) * (y - a[2]) / (b[2] - a[2]) + a[1] then
            inside = not inside
        end
    end
    return inside
end

local function distanceToPolygon(polygon, x, y)
    local best = math.huge
    local count = #polygon
    for index = 1, count do
        local a = polygon[index]
        local b = polygon[index == count and 1 or index + 1]
        local dx, dy = b[1] - a[1], b[2] - a[2]
        local share = 0
        local lengthSquared = dx * dx + dy * dy
        if lengthSquared > 0 then
            share = math.max(0, math.min(1, ((x - a[1]) * dx + (y - a[2]) * dy) / lengthSquared))
        end
        local ex, ey = x - a[1] - dx * share, y - a[2] - dy * share
        best = math.min(best, math.sqrt(ex * ex + ey * ey))
    end
    return best
end

function Xeen.rimFall(seas, points)
    -- a flying party is not falling (the map's timer runs always; IsAtLeast(IsFlying, 0) holds while it flies)
    if IsAtLeast(IsFlying, 0) then
        return
    end
    local x, y, z = evt.GetPartyPosition()
    -- In the void itself at any height (D-109: the land runs level to its edge, and the first void cell's floor,
    -- never drawn, slopes from the land's height down to the void's: a party could stand on it in mid-air); within
    -- Xeen.RimFallMargin of it only below Xeen.RimFallDepth (a hole beside a waterfall).
    local below = false
    for _, sea in ipairs(seas) do
        if insidePolygon(sea, x, y)
            or (z < Xeen.RimFallDepth and distanceToPolygon(sea, x, y) <= Xeen.RimFallMargin) then
            below = true
            break
        end
    end
    if not below or #points == 0 then
        return
    end
    local nearest = points[1]
    local nearestDistance = math.huge
    for _, point in ipairs(points) do
        local dx, dy = point[1] - x, point[2] - y
        local distance = dx * dx + dy * dy
        if distance < nearestDistance then
            nearest = point
            nearestDistance = distance
        end
    end
    evt.StatusText("You fall into the void between the stars... and wake on the rim.")
    -- a move within the map ("0"): the map is not loaded again, so its timers (this one) keep running
    evt.MoveToMap(nearest[1], nearest[2], nearest[3] + Xeen.SkyFallHeight, nearest[4], 0, 0, 0, 0, "0",
        {direct = true, keepHeight = true})
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The elemental planes (M38, D-58 C2-C3). A Skyroads corner's right answer (m38.corner_<element>) moves the party directly
-- onto its plane's arrival shelf, entrance:d7_fall, standing (no keepHeight, no falling damage). Points from each plane's
-- L1 NOTES (the shelf's floor 0); the plane's lane confirms them at install.
Xeen.PlaneArrivals = {
    fire = {3776, -3904, 0, 768, "xeen_p1.blv"},      -- the Cinder Shelf, facing north-west
    air = {-4096, -4096, 0, 256, "xeen_p2.blv"},      -- the Gale Landing, facing north-east
    earth = {-3840, 3968, 0, 1792, "xeen_p3.blv"},    -- the Dust Ledge, facing south-east
    water = {3968, 3968, 0, 1280, "xeen_p4.blv"},     -- the Spray Terrace, facing south-west
}

function Xeen.toPlane(element)
    local arrival = Xeen.PlaneArrivals[element]
    if arrival == nil then
        evt.StatusText("Unknown plane: " .. tostring(element))
        return
    end
    evt.MoveToMap(arrival[1], arrival[2], arrival[3], arrival[4], 0, 0, 0, 0, arrival[5], {direct = true})
end

-- The test (D-58 C3, P-1): "Accept the test of X?" raises the Sleeper's Guardian and two greater elementals (the map's
-- hidden group). Each guardian's death event calls Xeen.planeTestCheck("<element>", <the group>); once all three are dead
-- it runs m38.test_<element>_passed (its qbit, once), which the chamber gate, the guardians and the pit read on load.
Xeen.PlaneTests = {
    fire = {qbit = "m38.fire_test", hook = "m38.test_fire_passed"},
    air = {qbit = "m38.air_test", hook = "m38.test_air_passed"},
    earth = {qbit = "m38.earth_test", hook = "m38.test_earth_passed"},
    water = {qbit = "m38.water_test", hook = "m38.test_water_passed"},
}

function Xeen.planeTestCheck(element, group)
    local test = Xeen.PlaneTests[element]
    if test == nil then
        evt.StatusText("Unknown plane test: " .. tostring(element))
        return false
    end
    if Xeen.isSet(test.qbit) then
        return true
    end
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, group, 0, false) then
        return false
    end
    return XeenQuests.hook(test.hook)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The travel pyramids (WORLD_DESIGN 3.3). Before the party holds the right to pass, the source's answer: "the moons
-- are not aligned". Each pyramid's map event calls Xeen.travelPyramid("<from>"); destinations are filled in by the map
-- lanes when both ends exist (x, y, z, yaw in game units and the target map).

Xeen.Pyramids = {
    vertigo = {opens = "m7.sigil", to = "castleview"},          -- X1 knoll east of Vertigo -> D1
    castleview = {opens = "m7.sigil", to = "vertigo"},          -- D1 outside Castleview -> X1
    shangrila = {opens = "m30.done", to = "alamar_gate"},       -- XD-17 -> D6 (late)
    alamar_gate = {opens = "m30.done", to = "shangrila"},
}

Xeen.PyramidArrivals = {
    vertigo = {8832, 9472, 800, 1024, "xeen_x1.odm"},       -- X1: the orchard road's end, west of the knoll (A5)
    castleview = {-1024, 13312, 1248, 1792, "xeen_d1.odm"},  -- D1's travel pyramid (A4, D1 installed)
    shangrila = {0, 3200, 256, 1536, "xeen_xd17.blv"},       -- XD-17's entrance:d6_pyramid (D-50 Q9, A5)
    alamar_gate = {-5120, 1024, 1856, 512, "xeen_d6.odm"},   -- D6's entrance:xd17_pyramid by Castle Alamar's gate (A6)
}

function Xeen.travelPyramid(from)
    local pyramid = Xeen.Pyramids[from]
    if pyramid == nil then
        evt.StatusText("Unknown pyramid: " .. tostring(from))
        return false
    end
    if not Xeen.isSet(pyramid.opens) then
        evt.SimpleMessage("The moons are not aligned.")
        return false
    end
    local arrival = Xeen.PyramidArrivals[pyramid.to]
    if arrival == nil then
        evt.SimpleMessage("The moons are not aligned.")
        return false
    end
    evt.PlaySoundName("xeen_pyramid_travel")
    -- direct: the click is the choice; no leave-the-dungeon question from XD-17's pyramid (a BLV)
    evt.MoveToMap(arrival[1], arrival[2], arrival[3], arrival[4], 0, 0, 0, 0, arrival[5], {direct = true})
    return true
end

-- How many of an item the whole party carries (Megacredits: Emerson takes five at a time).
-- The party's count, each item once: a member's count includes the shared quest pouch, so a sum over members would
-- count a pouch item once per member.
function Xeen.itemCount(itemId)
    return evt.CountItems(itemId, itemId)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Gems as a second currency (QUESTS 4.3, MONSTERS_AND_ITEMS 4: talking skulls, the dragon tax, gemsmiths, Slick).
-- A "gem" is any gem item the party carries, whatever its kind; paying takes the cheapest first.

Xeen.GemItems = {177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 988, 989, 990, 991, 992, 993, 994, 995, 996, 997,
    998, 2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065}

function Xeen.gemCount()
    local count = 0
    for _, itemId in ipairs(Xeen.GemItems) do
        count = count + Xeen.itemCount(itemId)
    end
    return count
end

-- Takes `count` gems and returns true, or takes nothing and returns false when the party has fewer.
function Xeen.payGems(count)
    if Xeen.gemCount() < count then
        return false
    end
    -- RemoveItem takes from wherever the count saw the gem: a pack, a pouch or the mouse cursor.
    local left = count
    for _, itemId in ipairs(Xeen.GemItems) do
        while left > 0 and Xeen.itemCount(itemId) > 0 do
            RemoveItem(itemId)
            left = left - 1
        end
        if left == 0 then
            break
        end
    end
    return true
end

-- The party is on this map, by its map_stats name ("Castle Blackfang", DD-14): evt.GetCurrentMapName() gives the
-- map's English name, not its file. For a person met on two maps (Ambrose's D6 and DD-14 topics, D-52).
function Xeen.onMap(name)
    return (evt.GetCurrentMapName() or "") == name
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Time of day (PRODUCTION E12: the Count's coffin at night, the Queen carried out after nightfall, the sundials).

function Xeen.hour()
    return math.floor(CurrentGameMinutes() / 60) % 24
end

-- Night is 21:00 to 05:59, as the game's own lighting.
function Xeen.isNight()
    local hour = Xeen.hour()
    return hour >= 21 or hour < 6
end

function Xeen.isHour(hour)
    return Xeen.hour() == hour
end

-- Once a day (D-49: D5's Shrine of Great Power, Fountain of Might, the munchies): a named map variable holds the game
-- day it was last used, plus one (0 is never).
function Xeen.today()
    return math.floor(CurrentGameMinutes() / 1440)
end

function Xeen.usedToday(key)
    return evt.GetMapVar(key, 0) == Xeen.today() + 1
end

function Xeen.markToday(key)
    evt.SetMapVar(key, Xeen.today() + 1)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The mirrors (WORLD_DESIGN 3.3; QUESTS 4.3). A4 lists them (source/towns, houses of kind mirror: face, town, qbit,
-- arrival); gen_quests writes that list into xeen_quests.lua as Xeen.Mirrors, keyed by the mirror's id. A town's mirror
-- event calls Xeen.useMirror(id): touching sets the mirror's qbit (also the town's Town Portal unlock), then the
-- party may pick any touched mirror of the same face; Darkside's mirrors wake only with Kalindra's stage 4.

Xeen.Mirrors = Xeen.Mirrors or {}

-- A mirror with `opens` (a quest bit's name, A4's town file) works only once that bit is set; a bit of a quest not
-- written yet keeps it shut.
function Xeen.mirrorOpen(mirror)
    if mirror.opens == nil then
        return true
    end
    local value = XeenQuests.qbits[mirror.opens]
    return value ~= nil and IsQBitSet(QBit(value))
end

function Xeen.touchMirror(id)
    local mirror = Xeen.Mirrors[id]
    if mirror ~= nil then
        SetQBit(QBit(mirror.qbit))
    end
end

-- The ids of the touched mirrors of a face, in town-name order (none on Darkside before Kalindra's stage 4).
function Xeen.mirrorDestinations(face)
    local destinations = {}
    if face == "darkside" and Xeen.stageOf("kalindra") < 4 then
        return destinations
    end
    for id, mirror in pairs(Xeen.Mirrors) do
        local usable = mirror.arrival ~= nil and Xeen.mirrorOpen(mirror)
        if mirror.face == face and usable and IsQBitSet(QBit(mirror.qbit)) then
            table.insert(destinations, id)
        end
    end
    table.sort(destinations, function(left, right) return Xeen.Mirrors[left].town < Xeen.Mirrors[right].town end)
    return destinations
end

-- A mirror's map event: function(continueStep) Xeen.useMirror(<mirror id>, <this event id>, continueStep) end.
-- The first call touches the mirror and offers the other touched mirrors of its face as buttons
-- (AskChoiceWithAnswerSteps); the button continues the same event with the picked mirror's step, which moves the party.
-- Returns whether the party travelled.
function Xeen.useMirror(id, eventId, continueStep)
    local mirror = Xeen.Mirrors[id]
    if mirror == nil then
        evt.StatusText("Unknown mirror: " .. tostring(id))
        return false
    end
    if not Xeen.mirrorOpen(mirror) then
        evt.SimpleMessage(mirror.closedText or "The mirror shows the square, but not you.")
        return false
    end
    Xeen.touchMirror(id)
    local choices = {}
    for _, otherId in ipairs(Xeen.mirrorDestinations(mirror.face)) do
        if otherId ~= id then
            table.insert(choices, otherId)
        end
    end
    if continueStep ~= nil and continueStep >= 1 and continueStep <= #choices then
        local arrival = Xeen.Mirrors[choices[continueStep]].arrival
        evt.PlaySoundName("xeen_mirror_travel")
        -- direct: the player already chose the destination; no second "leave?" from a mirror inside a dungeon
        evt.MoveToMap(arrival[1], arrival[2], arrival[3], arrival[4], 0, 0, 0, 0, arrival[5], {direct = true})
        return true
    end
    if continueStep ~= nil or #choices == 0 then
        if #choices == 0 then
            evt.SimpleMessage("The mirror shows the square, and you in it.")
        end
        return false
    end
    evt.PlaySoundName("xeen_mirror_touch")
    local answers = {}
    for index, otherId in ipairs(choices) do
        table.insert(answers, {Answer = Xeen.Mirrors[otherId].town, Step = index})
    end
    AskChoiceWithAnswerSteps(eventId, #choices + 1, "Where to?", answers)
    return false
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The Great Pyramid's number niches (M28, DD-15 L1, D-61 Q3; dark/aaze0083:13-38). Each niche's event calls
--   function(continueStep) return Xeen.pyramidNiche(<1-8>, <this event id>, continueStep) end
-- A typed prompt; the number or its word is right ("Correct!" and the niche's bit), anything else "Wrong!" (the niche
-- asks again next time). The eighth right answer runs m28.niches (vault_open). Returns true while the vault is open.

Xeen.PyramidNiches = {
    {question = "I'm the smallest. What's my number?", number = "3", word = "Three"},
    {question = "I'm the smallest even. What's my number?", number = "4", word = "Four"},
    {question = "I'm the smallest prime that's left. What's my number?", number = "5", word = "Five"},
    {question = "I'm what's left. What's my number?", number = "6", word = "Six"},
    {question = "I'm the largest prime. What's my number?", number = "7", word = "Seven"},
    {question = "I'm twice the smallest even. What's my number?", number = "8", word = "Eight"},
    {question = "I'm the smallest squared. What's my number?", number = "9", word = "Nine"},
    {question = "I'm the largest. What's my number?", number = "10", word = "Ten"},
}

function Xeen.pyramidNiche(index, eventId, continueStep)
    local niche = Xeen.PyramidNiches[index]
    if niche == nil then
        evt.StatusText("Unknown niche: " .. tostring(index))
        return false
    end
    local bits = {Xeen.qbit("m28.niche_1"), Xeen.qbit("m28.niche_2"), Xeen.qbit("m28.niche_3"),
        Xeen.qbit("m28.niche_4"), Xeen.qbit("m28.niche_5"), Xeen.qbit("m28.niche_6"), Xeen.qbit("m28.niche_7"),
        Xeen.qbit("m28.niche_8")}
    if IsQBitSet(QBit(bits[index])) then
        if continueStep == nil then
            evt.StatusText(tr("The niche shows its number: {number}.", {number = niche.number}))
        end
        return Xeen.isSet("m28.vault_open")
    end
    if continueStep == nil then
        AskQuestionWithAnswerSteps(eventId, 2, niche.question,
            {{Answer = niche.number, Step = 1}, {Answer = niche.word, Step = 1}})
        return false
    end
    if continueStep ~= 1 then
        evt.StatusText("Wrong!")
        return false
    end
    SetQBit(QBit(bits[index]))
    for _, bit in ipairs(bits) do
        if not IsQBitSet(QBit(bit)) then
            evt.StatusText("Correct!")
            return false
        end
    end
    XeenQuests.hook("m28.niches")
    return true
end

-- The Pharaoh's wall safe (M28, DD-15 L4, D-61 Q7; dark/aaze0086:19-29): three typed prompts in turn, 20 left,
-- 30 right, 1 left (the tapestry's border). The safe's event calls
--   function(continueStep) if Xeen.pharaohSafe(<this event id>, continueStep) then <open the safe's chest> end end
-- A wrong number is "No Luck." and the safe starts again. The third right number runs m28.safe (safe_open); returns
-- true once the safe is open.
Xeen.PharaohSafe = {
    {question = "Enter Combination. Left?", answer = "20"},
    {question = "Enter Combination. Right?", answer = "30"},
    {question = "Enter Combination. Left?", answer = "1"},
}

function Xeen.pharaohSafe(eventId, continueStep)
    if Xeen.isSet("m28.safe_open") then
        return continueStep == nil
    end
    local wrong = #Xeen.PharaohSafe + 1
    if continueStep == wrong then
        evt.StatusText("No Luck.")
        return false
    end
    local given = continueStep or 0
    if given >= #Xeen.PharaohSafe then
        XeenQuests.hook("m28.safe")
        return true
    end
    local prompt = Xeen.PharaohSafe[given + 1]
    AskQuestionWithAnswerSteps(eventId, wrong, prompt.question, {{Answer = prompt.answer, Step = given + 1}})
    return false
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Castle Alamar's sundials (M33, DD-17 L2; dark/aaze0050:1-16). Four element dials, Fire, Air, Earth and Water Time,
-- each turned round twelve readings; the true-name gate (hook m33.true_name_gate) opens only while all four read nine,
-- Alamar's birth number. Each dial's event calls Xeen.alamarSundial("fire", eventId, continueStep); the helper keeps
-- the readings in map variables, sets each dial's bit (m33.dial_<element>_nine, 117611-117614) while that dial reads
-- nine and m33.sundial_nine while all four do, clearing them otherwise (D-61 Q13). Each ring's bridge slab stands level
-- only while its dial's bit is set: the dial's event sets the slab's state after the helper returns true (turned).
-- DD-17's load event calls Xeen.alamarSundialsSync() before it sets the slabs and the fields, so a map state reset by
-- a rebuild (the dials back at their start) never leaves a bridge or the gate open on stale bits.

Xeen.AlamarSundials = {
    {key = "fire", title = "Fire Time", start = 3},
    {key = "air", title = "Air Time", start = 6},
    {key = "earth", title = "Earth Time", start = 12},
    {key = "water", title = "Water Time", start = 7},
}

function Xeen.alamarSundialReading(dial)
    return evt.GetMapVar("dd17_sundial_" .. dial.key, dial.start)
end

-- Rewrites each dial's bit and m33.sundial_nine from the four readings; returns whether all four read nine.
function Xeen.alamarSundialsSync()
    local dialBits = {fire = Xeen.qbit("m33.dial_fire_nine"), air = Xeen.qbit("m33.dial_air_nine"),
        water = Xeen.qbit("m33.dial_water_nine"), earth = Xeen.qbit("m33.dial_earth_nine")}
    local allNine = true
    for _, dial in ipairs(Xeen.AlamarSundials) do
        local atNine = Xeen.alamarSundialReading(dial) == 9
        local dialBit = dialBits[dial.key]
        if dialBit ~= nil then
            if atNine then
                SetQBit(QBit(dialBit))
            else
                ClearQBit(QBit(dialBit))
            end
        end
        if not atNine then
            allNine = false
        end
    end
    local bit = Xeen.qbit("m33.sundial_nine")
    if bit ~= nil then
        if allNine then
            SetQBit(QBit(bit))
        else
            ClearQBit(QBit(bit))
        end
    end
    return allNine
end

function Xeen.alamarSundial(key, eventId, continueStep)
    local dial = nil
    for _, candidate in ipairs(Xeen.AlamarSundials) do
        if candidate.key == key then
            dial = candidate
        end
    end
    if dial == nil then
        evt.StatusText("Unknown sundial: " .. tostring(key))
        return false
    end
    local reading = Xeen.alamarSundialReading(dial)
    if continueStep == 1 then
        local before = reading
        reading = reading % 12 + 1
        evt.SetMapVar("dd17_sundial_" .. dial.key, reading)
        Xeen.alamarSundialsSync()
        -- The slabs cannot be seen from the alcove: the dial says what it did below (D-61).
        if reading == 9 then
            evt.StatusText("The dial clicks home at nine. Somewhere below, stone grinds level.")
        elseif before == 9 then
            evt.StatusText("Somewhere below, stone drops away.")
        else
            evt.StatusText(tr("{title}: the sundial reads {reading}.", {title = tr(dial.title), reading = reading}))
        end
        return true
    end
    if continueStep ~= nil then
        Xeen.alamarSundialsSync()
        return false
    end
    AskChoiceWithAnswerSteps(eventId, 3,
        tr("{title}. The sundial reads {reading}. Turn?", {title = tr(dial.title), reading = reading}),
        {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})
    return false
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Genie lamps (Q-D27, D-49, D-58; dark/aaze0006:6-9, aaze0010:11-14, aaze0014:15-18, aaze0093:11-14, aazex105:11-14,
-- aaze0099:0-7). A lamp's map event:
--   function(continueStep) Xeen.genieLamp("d5_hills", <this event id>, continueStep) end
-- A wish lamp asks for one of three wishes, a greedy lamp offers all its gold (Yes is punished, No shares), the angry
-- lamp (D7) asks whom it may strike, and strikes someone whatever the answer (never lethal). The answer runs the lamp's
-- hook (its qbit, once) and then the answer's; a freed lamp shows the lamp hook's line. A lamp may have its own question.

Xeen.GenieKinds = {
    wish = {
        question = "Genie of the Lamp: \"Lucky day! For freeing me, I will grant you one of three wishes.\"",
        answers = {{"Experience", "q-d27.wish_experience"}, {"Gold", "q-d27.wish_gold"}, {"Gems", "q-d27.wish_gems"}},
    },
    greedy = {
        question = "Genie of the Lamp: \"My powers are low. I can give you 10,000 gold, but it is all that I have. Do you want it?\"",
        answers = {{"Yes", "q-d27.greed"}, {"No", "q-d27.share"}},
    },
    angry = {
        answers = {{"Take me", "q-d27.angry_self"}, {"Take my friends", "q-d27.angry_friends"},
            {"Make me king", "q-d27.angry_king"}},
    },
}

Xeen.GenieLamps = {
    d5_hills = {hook = "q-d27.d5_hills"},
    d5_dune = {hook = "q-d27.d5_dune"},
    d6_pinnacle = {hook = "q-d27.d6_pinnacle"},
    d6_islet = {hook = "q-d27.d6_islet"},
    d6_crag = {hook = "q-d27.d6_crag", kind = "greedy"},
    d7_tired = {hook = "q-d27.d7_tired",
        question = "Genie of the Lamp: \"(yawn) The people before you used up two wishes. There's one left. Take your pick.\""},
    d7_kind = {hook = "q-d27.d7_kind",
        question = "Genie of the Lamp: \"Thank you for releasing me. I like you, and I will grant you one wish. Choose one.\""},
    d7_angry = {hook = "q-d27.d7_angry", kind = "angry",
        question = "Genie of the Lamp: \"What took you so long? I've been stuck in that little lamp for 2000 years. If you had freed me after one thousand years, I would understand. But two? Two thousand years is simply unacceptable. I just can't let this slide. You can give up your life or the lives of your friends. What will it be?\""},
}

function Xeen.genieLamp(key, eventId, continueStep)
    local lamp = Xeen.GenieLamps[key]
    if lamp == nil then
        evt.StatusText("Unknown lamp: " .. tostring(key))
        return
    end
    local kind = Xeen.GenieKinds[lamp.kind or "wish"]
    if not XeenQuests.can(lamp.hook) or Xeen.isSet(lamp.hook) then
        if continueStep == nil then
            XeenQuests.hook(lamp.hook)
        end
        return
    end
    if continueStep == nil then
        local choices = {}
        for index, answer in ipairs(kind.answers) do
            table.insert(choices, {Answer = answer[1], Step = index})
        end
        AskChoiceWithAnswerSteps(eventId, #kind.answers + 1, lamp.question or kind.question, choices)
        return
    end
    local answer = kind.answers[continueStep]
    if answer == nil then
        return
    end
    XeenQuests.hook(lamp.hook)
    XeenQuests.hook(answer[2])
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The Skyroads' tolls (D7, D-58 Q3 and D-6; dark/aaze0097:2-3, aazex109:3-4, aazex100:2-3, aaze0092:3-4). Each toll's
-- trigger on the road calls
--   function(continueStep) Xeen.toll("north", <its two Sky Bandits' group>, <this event id>, continueStep) end
-- The bandits ask for the source's 10,000 gold. Paying (d7.toll_paid) keeps the toll open until the map refills (map
-- variable d7_toll_<key> 1); refusing, or paying without the gold, turns only this toll's two bandits hostile (2) and
-- the toll asks no more until the refill brings them back peaceful. A toll whose bandits are dead asks nothing.
Xeen.Tolls = {
    north = {question = "Sky Bandits: \"Pay us 10,000 gold or else!\"", pay = "OK.", fight = "Or else WHAT?"},
    east = {question = "Sky Bandits: \"You have invaded our territory. Appease us with 10,000 gold or face our wrath!\"",
        pay = "Take our money", fight = "Bow down before us!"},
    south = {question = "Sky Bandits: \"Many apologies, good folks, but this is a robbery. I'm afraid we are going to have to ask you for 10,000 gold.\"",
        pay = "Here you are", fight = "We must decline"},
    west = {question = "Sky Bandits: \"Hold! The toll for passing this part of the road is 10,000 gold!\"",
        pay = "Here you go", fight = "Draw steel, knave!"},
}

function Xeen.toll(key, group, eventId, continueStep)
    local toll = Xeen.Tolls[key]
    if toll == nil then
        evt.StatusText("Unknown toll: " .. tostring(key))
        return
    end
    local variable = "d7_toll_" .. key
    if evt.GetMapVar(variable, 0) ~= 0 or evt.CheckMonstersKilled(ActorKillCheck.Group, group, 0, false) then
        return
    end
    if continueStep == nil then
        evt.PlaySoundName("xeen_bandit_whistle")
        AskChoiceWithAnswerSteps(eventId, 3, toll.question,
            {{Answer = toll.pay, Step = 1}, {Answer = toll.fight, Step = 2}})
        return
    end
    if continueStep == 1 and XeenQuests.hook("d7.toll_paid") then
        evt.SetMapVar(variable, 1)
        return
    end
    if continueStep ~= 1 and continueStep ~= 2 then
        return
    end
    evt.SetMapVar(variable, 2)
    evt.SetMonGroupBit(group, MonsterBits.Hostile, 1)
    if continueStep == 2 then
        XeenQuests.hook("d7.toll_refused")
    end
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The Merchants of the Elements (D7, D-58; dark/aaze0090:4-10, aaze0097:4-10, aazex104:4-10, aazex110:0-6). Each
-- barge's event calls
--   function(continueStep) Xeen.merchantRiddle("smoke", <this event id>, continueStep) end
-- The merchant asks his riddle (a typed answer); the right one runs d7.merchant_<cargo> (its qbit, once: experience),
-- any other d7.merchant_wrong. Once solved, the merchant only says what the hook's else line says.
Xeen.Merchants = {
    smoke = {answer = "smoke", question = "Merchant of the Elements: \"Between Fire and Air I constantly travel, a simple clue to unravel. What's my cargo?\""},
    dust = {answer = "dust", question = "Merchant of the Elements: \"Between Air and Earth I constantly travel, a simple clue to unravel. What's my cargo?\""},
    steam = {answer = "steam", question = "Merchant of the Elements: \"Between Fire and Water I constantly travel, a simple clue to unravel. What's my cargo?\""},
    mud = {answer = "mud", question = "Merchant of the Elements: \"Between Water and Earth I constantly travel, a simple clue to unravel. What's my cargo?\""},
}

function Xeen.merchantRiddle(key, eventId, continueStep)
    local merchant = Xeen.Merchants[key]
    if merchant == nil then
        evt.StatusText("Unknown merchant: " .. tostring(key))
        return
    end
    local hook = "d7.merchant_" .. key
    if Xeen.isSet("d7.riddle_" .. key) then
        if continueStep == nil then
            XeenQuests.hook(hook)
        end
        return
    end
    if continueStep == nil then
        AskQuestionWithAnswerSteps(eventId, 2, merchant.question, {{Answer = merchant.answer, Step = 1}})
    elseif continueStep == 1 then
        XeenQuests.hook(hook)
    else
        XeenQuests.hook("d7.merchant_wrong")
    end
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The tribble door (DD-26, Q-D28, D-65 change 2; dark/aaze0038:5-9). The bronze pair's event calls
--   function(continueStep) if Xeen.tribbleDoor(<this event id>, continueStep) then <open the leaves> end end
-- Shut, the voice's line is the typed prompt's own text (no message before it: D-65 B1). "tribbles" or "tribble", in any
-- case, runs q-d28.tribble_door (map qbit 117805, "Correct! You may pass.") and returns true; any other answer runs
-- q-d28.tribble_wrong and returns false. Open (117805 set; DD-26's load event keeps the leaves open) it returns true and
-- asks nothing.
Xeen.TribbleDoor = {question = "A disembodied voice booms, \"What's the password?\"", answers = {"tribbles", "tribble"}}

function Xeen.tribbleDoor(eventId, continueStep)
    if Xeen.isSet("q-d28.door_open") then
        return true
    end
    if continueStep == nil then
        local answers = {}
        for _, answer in ipairs(Xeen.TribbleDoor.answers) do
            table.insert(answers, {Answer = answer, Step = 1})
        end
        AskQuestionWithAnswerSteps(eventId, 2, Xeen.TribbleDoor.question, answers)
        return false
    end
    if continueStep == 1 then
        return XeenQuests.hook("q-d28.tribble_door")
    end
    XeenQuests.hook("q-d28.tribble_wrong")
    return false
end

-- ---------------------------------------------------------------------------------------------------------------------
-- Gifts to every member present, once per character (a player bit each): the Sky Lake's scarabs (D7, D-58 Q5: +10 to
-- one resistance, no item; the d7.scarab_<element> hooks pay and call these) and the Voweless Knights' books (DD-08,
-- D-61 Q25: +1 to one statistic).

-- True when some member present has not had this gift yet.
function Xeen.anyMemberLacks(bit)
    for _, playerIndex in ipairs(PartyMembers()) do
        evt.ForPlayer(playerIndex)
        if not IsPlayerBitSet(PlayerBit(bit)) then
            evt.ForPlayer(Players.Current)
            return true
        end
    end
    evt.ForPlayer(Players.Current)
    return false
end

-- Every member present without the bit gains `amount` of `value` (a resistance, a base statistic) and the bit.
function Xeen.giveEachOnce(bit, value, amount)
    for _, playerIndex in ipairs(PartyMembers()) do
        evt.ForPlayer(playerIndex)
        if not IsPlayerBitSet(PlayerBit(bit)) then
            AddValue(value, amount)
            SetPlayerBit(PlayerBit(bit))
        end
    end
    evt.ForPlayer(Players.Current)
end

-- ---------------------------------------------------------------------------------------------------------------------
-- The Voweless Knights' books (Q-D17, DD-08, D-61 Q25; dark/aaze0069:8, :10-12, :18-20, aaze0070:2-6, :11-12,
-- aaze0071:2-8, :14-16). Each lectern's event calls
--   function(continueStep) Xeen.vowelessBook("sleeping_dogs", <this event id>, continueStep) end
-- The book asks for its proverb; the whole proverb (case and punctuation ignored) or its vowels in order are right and
-- run q-d17.book_<key> (+1 to one statistic for every member present who lacks the book's player bit); anything else
-- runs q-d17.book_wrong (the slam), and the book may be tried again. Once nobody present lacks it, it only shows its
-- hook's line.
Xeen.VowelessBooks = {
    sleeping_dogs = {hook = "q-d17.book_sleeping_dogs", bit = 11370, vowels = "eeeioie",
        proverbs = {"Let sleeping dogs lie"},
        question = "The book is blank but for one page with the letters: \"Lt slpng dgs l\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    laughs_last = {hook = "q-d17.book_laughs_last", bit = 11371, vowels = "eoauaaue",
        proverbs = {"He who laughs last, laughs best"},
        question = "The book is blank but for one page with the letters: \"H wh lghs lst, lghs bst\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    needs_of_many = {hook = "q-d17.book_needs_of_many", bit = 11372, vowels = "eeeoeaoueieeeoee",
        proverbs = {"The needs of the many outweigh the needs of the few"},
        question = "The book is blank but for one page with the letters: \"Th nds f th mny twgh th nds f th fw\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    love_of_money = {hook = "q-d17.book_love_of_money", bit = 11373, vowels = "oeooeieoooaei",
        proverbs = {"Love of money is the root of all evil"},
        question = "The book is blank but for one page with the letters: \"Lv f mny s th rt f ll vl\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    gift_horse = {hook = "q-d17.book_gift_horse", bit = 11374, vowels = "oooaioeieou",
        proverbs = {"Don't look a gift horse in the mouth"},
        question = "The book is blank but for one page with the letters: \"Dn't lk gft hrs n th mth\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    fool_and_money = {hook = "q-d17.book_fool_and_money", bit = 11375, vowels = "aooaioeaeooae",
        proverbs = {"A fool and his money are soon parted"},
        question = "The book is blank but for one page with the letters: \"Fl nd hs mny r sn prtd\" So say the Voweless Knights. A blank line underneath awaits your answer."},
    wishes_horses = {hook = "q-d17.book_wishes_horses", bit = 11376, vowels = "iieeeoeeeouie",
        proverbs = {"If wishes were horses, beggars would ride", "If wishes were horses, beggers would ride"},
        question = "The book is blank but for one page with the letters: \"F wshs wr hrss, bggrs wld rd\" So say the Voweless Knights. A blank line underneath awaits your answer."},
}

-- The typed forms a book accepts: each proverb as written, without its punctuation, with a closing full stop, and the
-- vowels. The prompt compares case-blind and trimmed.
function Xeen.vowelessBookAnswers(book)
    local answers = {{Answer = book.vowels, Step = 1}}
    for _, proverb in ipairs(book.proverbs) do
        local bare = proverb:gsub("[%.,!']", "")
        for _, form in ipairs({proverb, proverb .. ".", bare, bare .. "."}) do
            table.insert(answers, {Answer = form, Step = 1})
        end
    end
    return answers
end

function Xeen.vowelessBook(key, eventId, continueStep)
    local book = Xeen.VowelessBooks[key]
    if book == nil then
        evt.StatusText("Unknown book: " .. tostring(key))
        return
    end
    if not Xeen.anyMemberLacks(book.bit) then
        if continueStep == nil then
            XeenQuests.hook(book.hook)
        end
        return
    end
    if continueStep == nil then
        AskQuestionWithAnswerSteps(eventId, 2, book.question, Xeen.vowelessBookAnswers(book))
    elseif continueStep == 1 then
        XeenQuests.hook(book.hook)
    else
        XeenQuests.hook("q-d17.book_wrong")
    end
end

-- The Hall of Thrones (Q-D17, DD-08 L4, D-61 Q26; dark/aaze0072:8-12, :21-25). Each throne's event calls
--   function() Xeen.vowelessThrone("depressed") end      ("confused", "heartbroken", "insane", "euphoria", "dunce")
-- A throne of the lows gives the sitter its condition and marks itself (a map variable). The Euphoria Throne, once
-- all four lows are marked, runs q-d17.euphoria (+1 to every statistic for the sitter, once per character) and clears
-- the four, so the next member must sit through the lows too; before that it is q-d17.unworthy. The Throne of the
-- Dunce is q-d17.dunce. The L1 pillow note gives the order: "to appreciate the highs one must experience the lows".
Xeen.VowelessThrones = {
    depressed = "q-d17.throne_depressed",
    confused = "q-d17.throne_confused",
    heartbroken = "q-d17.throne_heartbroken",
    insane = "q-d17.throne_insane",
}

function Xeen.vowelessThrone(key)
    if key == "dunce" then
        XeenQuests.hook("q-d17.dunce")
        return
    end
    if key == "euphoria" then
        for low in pairs(Xeen.VowelessThrones) do
            if evt.GetMapVar("dd08_throne_" .. low, 0) == 0 then
                XeenQuests.hook("q-d17.unworthy")
                return
            end
        end
        for low in pairs(Xeen.VowelessThrones) do
            evt.SetMapVar("dd08_throne_" .. low, 0)
        end
        XeenQuests.hook("q-d17.euphoria")
        return
    end
    local hook = Xeen.VowelessThrones[key]
    if hook == nil then
        evt.StatusText("Unknown throne: " .. tostring(key))
        return
    end
    evt.SetMapVar("dd08_throne_" .. key, 1)
    XeenQuests.hook(hook)
end
