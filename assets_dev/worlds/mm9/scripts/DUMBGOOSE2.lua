-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DUMBGOOSE2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "HonkHostility.inc" }

-- DumbGoose2.scr
-- by SJR
-- 10-08-01
-- Foyer Goose stuff
script.labels["TurnHostilityOn"] = function(ctx)
    -- DUMBGOOSE2.scr:12
    -- overloaded so dumb goose death
    -- won't set of Hostility
    ctx:state().g_ntemp = 10 -- DUMBGOOSE2.scr:19
    ctx:self():setStat("HitPoints", "g_ntemp") -- DUMBGOOSE2.scr:20
    ctx:state().g_ntemp = 1 -- DUMBGOOSE2.scr:21
    ctx:state().g_ntemp = ctx:self():getStat("AC") -- DUMBGOOSE2.scr:22
    mm9.gosub(script, ctx, "BecomeHostile") -- DUMBGOOSE2.scr:24
    do return ctx:exit("") end -- DUMBGOOSE2.scr:26
end

script.labels["Main"] = function(ctx)
    -- DUMBGOOSE2.scr:29
    -- OnPostStartWorld InitDumbGoose
    ctx:wait(0, 5, "InitDumbGoose") -- DUMBGOOSE2.scr:32
    do return ctx:exit(1) end -- DUMBGOOSE2.scr:34
end

script.labels["InitDumbGoose"] = function(ctx)
    -- DUMBGOOSE2.scr:37
    ctx:state().g_nTemp = ctx:self():getStat("RunVel") -- DUMBGOOSE2.scr:43
    ctx:self():setStat("RunVel", "g_nTemp") -- DUMBGOOSE2.scr:44
    ctx:self():setStat("WalkVel", "g_nTemp") -- DUMBGOOSE2.scr:45
    mm9.gosub(script, ctx, "InitHonkHostility") -- DUMBGOOSE2.scr:47
    mm9.gosub(script, ctx, "RunLoop") -- DUMBGOOSE2.scr:49
    do return ctx:exit(1) end -- DUMBGOOSE2.scr:51
end

script.labels["RunLoop"] = function(ctx)
    -- DUMBGOOSE2.scr:57
    ctx:randomInt(-5000, 5000, "g_nTemp") -- DUMBGOOSE2.scr:59
    ctx:self():runToPos("g_nTemp", "g_nTemp", "g_nTemp") -- DUMBGOOSE2.scr:61
    ctx:wait(0, 2, "RunLoop") -- DUMBGOOSE2.scr:65
    do return ctx:exit("TRUE") end -- DUMBGOOSE2.scr:67
end

return script
