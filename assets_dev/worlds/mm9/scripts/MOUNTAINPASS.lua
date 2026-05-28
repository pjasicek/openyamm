-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MOUNTAINPASS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Yanmir.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["OnAward"] = function(ctx)
    -- MOUNTAINPASS.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(80, "g_ntemp") -- MOUNTAINPASS.scr:19
    if ctx:condition("g_ntemp==0") then -- MOUNTAINPASS.scr:21
        ctx:hasKey(79, "keycheck") -- MOUNTAINPASS.scr:23
        if ctx:condition("keycheck==1") then -- MOUNTAINPASS.scr:24
            ctx:giveKey("", 80) -- MOUNTAINPASS.scr:26
            ctx:giveExp(14000) -- MOUNTAINPASS.scr:27
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- MOUNTAINPASS.scr:28
            do return ctx:exit("") end -- MOUNTAINPASS.scr:29
        end -- MOUNTAINPASS.scr:30
    end -- MOUNTAINPASS.scr:31
    ctx:hasKey(176, "keycheck") -- MOUNTAINPASS.scr:33
    if ctx:condition("keycheck==0") then -- MOUNTAINPASS.scr:34
        ctx:giveKey("", 176) -- MOUNTAINPASS.scr:36
        ctx:giveExp(14000) -- MOUNTAINPASS.scr:37
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- MOUNTAINPASS.scr:38
        do return ctx:exit("") end -- MOUNTAINPASS.scr:39
    end -- MOUNTAINPASS.scr:40
    do return ctx:exit("") end -- MOUNTAINPASS.scr:41
end

script.labels["OnStep"] = function(ctx)
    -- MOUNTAINPASS.scr:45
    ctx:command("g_ncounter", "= g_ncounter + 1") -- MOUNTAINPASS.scr:48
    if ctx:condition("g_ncounter==2") then -- MOUNTAINPASS.scr:49
        mm9.gosub(script, ctx, "OnAward") -- MOUNTAINPASS.scr:50
    end -- MOUNTAINPASS.scr:51
    do return ctx:exit("") end -- MOUNTAINPASS.scr:52
end

script.labels["Main"] = function(ctx)
    -- MOUNTAINPASS.scr:56
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "OnStep") -- MOUNTAINPASS.scr:61
    ctx:command("g_ncounter", "= 0") -- MOUNTAINPASS.scr:62
    do return ctx:exit("") end -- MOUNTAINPASS.scr:63
end

return script
