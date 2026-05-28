-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WRIT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- writ.scr
-- By Timmy
-- gives the player the writ of Fate (false)
-- and the related key
-- Writ of Fate (false) is item 392
-- edited by Bones 6/12/02, 5/12/03
-- TELP Patch 1.3 -- Writ won't disappear if not picked up.
-- Hijacked to fix teleporter doors in Yanmir's Fortress.
-- flag variables
script.labels["Onuse"] = function(ctx)
    -- WRIT.scr:23
    if not ctx:hasKey(100) then -- WRIT.scr:26-27
        if ctx:hasKey(99) then -- WRIT.scr:28-29
            ctx:giveItem(392) -- WRIT.scr:30
            ctx:giveExp(162000) -- WRIT.scr:31
            ctx:giveKey(100) -- WRIT.scr:32
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- WRIT.scr:33
            ctx:command("getmyhandle", "g_hobject") -- WRIT.scr:34
            ctx:command("removeobject", "g_hobject") -- WRIT.scr:35
            do return ctx:exit("") end -- WRIT.scr:36
        end -- WRIT.scr:37
    end -- WRIT.scr:38
    do return ctx:exit("") end -- WRIT.scr:39
end

script.labels["Init"] = function(ctx)
    -- WRIT.scr:42
    ctx:hasKey(100, "keycheck") -- WRIT.scr:45
    if ctx:condition("keycheck==1") then -- WRIT.scr:46
        ctx:command("getmyhandle", "g_hobject") -- WRIT.scr:47
        ctx:command("removeobject", "g_hobject") -- WRIT.scr:48
        ctx:command("exitscript", "") -- WRIT.scr:49
        do return ctx:exit("") end -- WRIT.scr:50
    end -- WRIT.scr:51
    ctx:command("getmyhandle", "g_hobject") -- WRIT.scr:53
    ctx:hasKey(99, "keycheck") -- WRIT.scr:55
    if ctx:condition("keycheck==0") then -- WRIT.scr:56
        ctx:command("clearflag", "g_hobject, visible") -- WRIT.scr:58
        ctx:command("clearflag", "g_hobject, solid") -- WRIT.scr:59
        ctx:command("clearflag", "g_hobject, gravity") -- WRIT.scr:60
        do return ctx:exit("") end -- WRIT.scr:61
    end -- WRIT.scr:63
end

script.labels["OnInit"] = function(ctx)
    -- WRIT.scr:65
    ctx:command("getmyhandle", "g_hobject") -- WRIT.scr:67
    ctx:command("setflag", "g_hobject, visible") -- WRIT.scr:68
    ctx:command("setflag", "g_hobject, solid") -- WRIT.scr:69
    ctx:command("setflag", "g_hobject, gravity") -- WRIT.scr:70
    ctx:addTrigger("Use", "Onuse") -- WRIT.scr:71
    do return ctx:exit("") end -- WRIT.scr:72
end

script.labels["Main"] = function(ctx)
    -- WRIT.scr:76
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("init", "OnInit") -- WRIT.scr:81
    ctx:command("onpoststartworld", "Init") -- WRIT.scr:82
    ctx:command("onpostminisaveload", "Init") -- WRIT.scr:83
    ctx:command("onpostsaveload", "Init") -- WRIT.scr:84
    ctx:command("wait", "1 .1 Init") -- WRIT.scr:85
    do return ctx:exit("") end -- WRIT.scr:86
end

script.labels["Init"] = function(ctx)
    -- WRIT.scr:90
    -- overloaded -- Bones
    ctx:command("getmyhandle", "g_hMyObject") -- WRIT.scr:94
    ctx:command("getobjectname", "g_hMyObject g_sTemp") -- WRIT.scr:95
    if ctx:condition("g_sTemp == DoorTeleportLeft") then -- WRIT.scr:96
        ctx:command("setpropstring", "DoubleDoorName DoorTeleportRight") -- WRIT.scr:97
        do return ctx:exit("") end -- WRIT.scr:98
    end -- WRIT.scr:99
    do return mm9.gotoLabel(script, ctx, "Init") end -- WRIT.scr:101
end

return script
