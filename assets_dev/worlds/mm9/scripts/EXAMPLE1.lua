-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EXAMPLE1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }

-- example1.scr
-- Jeff Leggett
-- This script uses the base.inc script
-- but actually just enhances it a little..
-- This does a few extra things..
script.labels["TauntDone"] = function(ctx)
    -- EXAMPLE1.scr:17
    ctx:command("runto", "g_hTarget") -- EXAMPLE1.scr:20
    do return ctx:exit("") end -- EXAMPLE1.scr:21
end

script.labels["FoundPlayer"] = function(ctx)
    -- EXAMPLE1.scr:25
    -- This is called when we currently do not
    -- have a player targeted and one has
    -- appeared within our viewable range
    -- Randomly Taunt the player when you first
    -- see him
    ctx:command("getrandomint", "1,100,g_nRandom") -- EXAMPLE1.scr:38
    if ctx:condition("g_nRandom < 80") then -- EXAMPLE1.scr:40
        -- 80 % chance we'll just do the base functionality
        -- found in base.inc
        mm9.gosub(script, ctx, "BaseFoundPlayer") -- EXAMPLE1.scr:44
    else -- EXAMPLE1.scr:45
        ctx:command("getplayerhandle", "g_hTarget") -- EXAMPLE1.scr:46
        if ctx:condition("g_hTarget>0") then -- EXAMPLE1.scr:48
            ctx:command("target", "g_hTarget") -- EXAMPLE1.scr:49
            ctx:command("taunt", "TauntDone") -- EXAMPLE1.scr:50
        end -- EXAMPLE1.scr:51
    end -- EXAMPLE1.scr:52
    do return ctx:exit("") end -- EXAMPLE1.scr:54
end

script.labels["FoundHidingPlace"] = function(ctx)
    -- EXAMPLE1.scr:58
    ctx:command("turnleft", "90") -- EXAMPLE1.scr:60
    -- Now that we've done our Hide, go back
    -- to using the base damage handler...
    ctx:command("ondamagedone", "BaseDamageDone") -- EXAMPLE1.scr:66
    do return ctx:exit("") end -- EXAMPLE1.scr:68
end

script.labels["DamageDone"] = function(ctx)
    -- EXAMPLE1.scr:71
    -- If we are hit, and we can't see the player,
    -- Run away to the nearest hiding place...
    -- Call the base version of this first...
    mm9.gosub(script, ctx, "BaseDamageDone") -- EXAMPLE1.scr:80
    -- If the target is NULL, then we can
    -- assume that we were unable to see the
    -- attacker.  So, let's run to our hiding
    -- place...
    if ctx:condition("g_hTarget == 0") then -- EXAMPLE1.scr:87
        ctx:command("getobjecthandle", "HideTest1, hHideObject") -- EXAMPLE1.scr:88
        if ctx:condition("hHideObject > 0") then -- EXAMPLE1.scr:89
            -- we found the hide object, run for it!
            ctx:command("runto", "hHideObject, FoundHidingPlace") -- EXAMPLE1.scr:91
            do return ctx:exit("") end -- EXAMPLE1.scr:92
        end -- EXAMPLE1.scr:93
        -- 0 means that the AI will do it's default response to this event.
        do return ctx:exit(0) end -- EXAMPLE1.scr:96
    end -- EXAMPLE1.scr:97
    do return ctx:exit("") end -- EXAMPLE1.scr:99
end

script.labels["Main"] = function(ctx)
    -- EXAMPLE1.scr:102
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "InitBase") -- EXAMPLE1.scr:107
    -- Note: we are overwriting some of
    -- base.inc's callbacks here..
    ctx:command("onfoundplayer", "FoundPlayer") -- EXAMPLE1.scr:114
    -- Here, we want to change the functionality in base.inc and handle
    -- damage our own special way....
    ctx:command("ondamagedone", "DamageDone") -- EXAMPLE1.scr:120
    do return ctx:exit("") end -- EXAMPLE1.scr:122
end

return script
