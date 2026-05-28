-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Honk.scr
-- By Timmy
-- gives the player the Golden Honk
-- item 369
script.labels["Onuse"] = function(ctx)
    -- HONK.scr:11
    if ctx:hasKey(343) then -- HONK.scr:14-15
        if not ctx:hasKey(344) then -- HONK.scr:16-17
            -- SJR
            mm9.gosub(script, ctx, "TurnHostilityOn") -- HONK.scr:19
            -- SJR
            ctx:giveItem(369) -- HONK.scr:21
            ctx:giveKey(344) -- HONK.scr:22
            ctx:command("getmyhandle", "g_hmyobject") -- HONK.scr:23
            ctx:command("removeobject", "g_hmyobject") -- HONK.scr:24
            do return ctx:exit("") end -- HONK.scr:25
        end -- HONK.scr:26
    else -- HONK.scr:27
        if not ctx:hasKey(345) then -- HONK.scr:28-29
            -- SJR
            mm9.gosub(script, ctx, "TurnHostilityOn") -- HONK.scr:31
            -- SJR
            ctx:giveItem(369) -- HONK.scr:33
            ctx:giveKey(345) -- HONK.scr:34
            ctx:command("getmyhandle", "g_hmyobject") -- HONK.scr:35
            ctx:command("removeobject", "g_hmyobject") -- HONK.scr:36
            do return ctx:exit("") end -- HONK.scr:37
        end -- HONK.scr:38
    end -- HONK.scr:39
    do return ctx:exit("") end -- HONK.scr:41
end

-- SJR
script.labels["TurnHostilityOn"] = function(ctx)
    -- HONK.scr:45
    ctx:command("getobjecthandle", "HONK_FRIENDLY, g_hObject") -- HONK.scr:47
    ctx:command("removeobject", "g_hObject") -- HONK.scr:48
    do return ctx:exit(1) end -- HONK.scr:50
end

-- SJR
script.labels["Init"] = function(ctx)
    -- HONK.scr:54
    -- unlock the door if you're on the quest
    if ctx:hasKey(343) then -- HONK.scr:59-60
        ctx:command("getobjecthandle", "DoubleDoorL13 g_hobject") -- HONK.scr:61
        ctx:trigger("g_hobject", "Unlock") -- HONK.scr:62
        ctx:command("getobjecthandle", "DoubleDoorR13 g_hobject") -- HONK.scr:63
        ctx:trigger("g_hobject", "Unlock") -- HONK.scr:64
    else -- HONK.scr:65
        ctx:command("getobjecthandle", "DoubleDoorL13 g_hobject") -- HONK.scr:66
        ctx:trigger("g_hobject", "lock") -- HONK.scr:67
        ctx:command("getobjecthandle", "DoubleDoorR13 g_hobject") -- HONK.scr:68
        ctx:trigger("g_hobject", "lock") -- HONK.scr:69
    end -- HONK.scr:70
    if ctx:hasKey(344) then -- HONK.scr:73-74
        ctx:command("getmyhandle", "g_hmyobject") -- HONK.scr:75
        ctx:command("removeobject", "g_hmyobject") -- HONK.scr:76
        do return ctx:exit("") end -- HONK.scr:77
    end -- HONK.scr:78
    if ctx:hasKey(345) then -- HONK.scr:80-81
        ctx:command("getmyhandle", "g_hmyobject") -- HONK.scr:82
        ctx:command("removeobject", "g_hmyobject") -- HONK.scr:83
        do return ctx:exit("") end -- HONK.scr:84
    end -- HONK.scr:85
    do return ctx:exit("") end -- HONK.scr:86
end

script.labels["Main"] = function(ctx)
    -- HONK.scr:90
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- HONK.scr:94
    ctx:command("onpoststartworld", "Init") -- HONK.scr:95
    ctx:command("onpostminisaveload", "Init") -- HONK.scr:96
    ctx:command("onpostsaveload", "Init") -- HONK.scr:97
    ctx:command("wait", "1 .1 Init") -- HONK.scr:98
    do return ctx:exit("") end -- HONK.scr:99
end

return script
