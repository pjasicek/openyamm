-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ENDDEMON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "range.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "Flags.inc" }

script.labels["EndDemon.scr"] = function(ctx)
    -- ENDDEMON.scr:2
end

-- Timmy
-- This Controls the Demon and tells him to open the last door
-- in the Tomb of a Thousand Terrors
script.labels["OnDeath"] = function(ctx)
    -- ENDDEMON.scr:25
    ctx:cprint("Died!!") -- ENDDEMON.scr:28
    ctx:object("sDoorA"):trigger("Open") -- ENDDEMON.scr:30-31
    ctx:object("sDoorB"):trigger("Open") -- ENDDEMON.scr:32-33
    mm9.gosub(script, ctx, "OnDeath") -- ENDDEMON.scr:36
    do return ctx:exit("") end -- ENDDEMON.scr:37
end

script.labels["AwareDone"] = function(ctx)
    -- ENDDEMON.scr:42
    mm9.gosub(script, ctx, "Begin") -- ENDDEMON.scr:44
    do return ctx:exit("") end -- ENDDEMON.scr:46
end

script.labels["SpawnDone"] = function(ctx)
    -- ENDDEMON.scr:49
    ctx:self():aware("AwareDone") -- ENDDEMON.scr:51
    do return ctx:exit("") end -- ENDDEMON.scr:53
end

script.labels["DoSpawnAnim"] = function(ctx)
    -- ENDDEMON.scr:56
    ctx:self():playAnimation("Spawn", "SpawnDone") -- ENDDEMON.scr:59
    ctx:self():setFlag("FLAG_VISIBLE", true) -- ENDDEMON.scr:60
    do return ctx:exit("") end -- ENDDEMON.scr:62
end

script.labels["SpawnIn"] = function(ctx)
    -- ENDDEMON.scr:65
    -- Play our animation and do our special FX
    ctx:self():doClientFx("GreaterDemon") -- ENDDEMON.scr:71
    ctx:wait(29, 1, "DoSpawnAnim") -- ENDDEMON.scr:73
    do return ctx:exit("") end -- ENDDEMON.scr:76
end

script.labels["Begin"] = function(ctx)
    -- ENDDEMON.scr:80
    mm9.gosub(script, ctx, "BaseInit") -- ENDDEMON.scr:83
    mm9.gosub(script, ctx, "RangeInit") -- ENDDEMON.scr:84
    do return ctx:exit("") end -- ENDDEMON.scr:85
end

script.labels["Main"] = function(ctx)
    -- ENDDEMON.scr:88
    ctx:state().g_ntemp = ctx:self():getStat("HitPoints") -- ENDDEMON.scr:95
    ctx:set("g_ntemp", "g_ntemp * nHPMod") -- ENDDEMON.scr:96
    ctx:self():setStat("Hitpoints", "g_ntemp") -- ENDDEMON.scr:97
    ctx:state().g_ntemp = ctx:self():getStat("AC") -- ENDDEMON.scr:99
    ctx:set("g_ntemp", "g_ntemp * nACMod") -- ENDDEMON.scr:100
    ctx:self():setStat("Hitpoints", "g_ntemp") -- ENDDEMON.scr:101
    ctx:getParam(0, "g_bTemp") -- ENDDEMON.scr:103
    ctx:state().g_bTemp = true -- ENDDEMON.scr:105
    if ctx:condition("g_bTemp==TRUE") then -- ENDDEMON.scr:107
        ctx:self():setFlag("FLAG_VISIBLE", false) -- ENDDEMON.scr:109
        ctx:wait(0, 0.1, "SpawnIn") -- ENDDEMON.scr:110
    else -- ENDDEMON.scr:111
        mm9.gosub(script, ctx, "Begin") -- ENDDEMON.scr:112
    end -- ENDDEMON.scr:113
    do return ctx:exit("") end -- ENDDEMON.scr:116
end

return script
