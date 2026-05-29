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
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- WRIT.scr:33
            ctx:state().g_hobject = ctx:self() -- WRIT.scr:34
            ctx:object("g_hobject"):remove() -- WRIT.scr:35
            do return ctx:exit("") end -- WRIT.scr:36
        end -- WRIT.scr:37
    end -- WRIT.scr:38
    do return ctx:exit("") end -- WRIT.scr:39
end

script.labels["Init"] = function(ctx)
    -- WRIT.scr:42
    ctx:hasKey(100, "keycheck") -- WRIT.scr:45
    if ctx:condition("keycheck==1") then -- WRIT.scr:46
        ctx:state().g_hobject = ctx:self() -- WRIT.scr:47
        ctx:object("g_hobject"):remove() -- WRIT.scr:48
        ctx:exitScript() -- WRIT.scr:49
        do return ctx:exit("") end -- WRIT.scr:50
    end -- WRIT.scr:51
    ctx:state().g_hobject = ctx:self() -- WRIT.scr:53
    ctx:hasKey(99, "keycheck") -- WRIT.scr:55
    if ctx:condition("keycheck==0") then -- WRIT.scr:56
        ctx:self():setFlag("visible", false) -- WRIT.scr:58
        ctx:self():setFlag("solid", false) -- WRIT.scr:59
        ctx:self():setFlag("gravity", false) -- WRIT.scr:60
        do return ctx:exit("") end -- WRIT.scr:61
    end -- WRIT.scr:63
end

script.labels["OnInit"] = function(ctx)
    -- WRIT.scr:65
    ctx:state().g_hobject = ctx:self() -- WRIT.scr:67
    ctx:self():setFlag("visible", true) -- WRIT.scr:68
    ctx:self():setFlag("solid", true) -- WRIT.scr:69
    ctx:self():setFlag("gravity", true) -- WRIT.scr:70
    ctx:addTrigger("Use", "Onuse") -- WRIT.scr:71
    do return ctx:exit("") end -- WRIT.scr:72
end

script.labels["Main"] = function(ctx)
    -- WRIT.scr:76
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("init", "OnInit") -- WRIT.scr:81
    ctx:onEvent("OnPostStartWorld", "Init") -- WRIT.scr:82
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- WRIT.scr:83
    ctx:onEvent("OnPostSaveLoad", "Init") -- WRIT.scr:84
    ctx:wait(1, .1, "Init") -- WRIT.scr:85
    do return ctx:exit("") end -- WRIT.scr:86
end

script.labels["Init"] = function(ctx)
    -- WRIT.scr:90
    -- overloaded -- Bones
    ctx:state().g_sTemp = ctx:self():name() -- WRIT.scr:95
    if ctx:condition("g_sTemp == DoorTeleportLeft") then -- WRIT.scr:96
        ctx:self():setStringProperty("DoubleDoorName", "DoorTeleportRight") -- WRIT.scr:97
        do return ctx:exit("") end -- WRIT.scr:98
    end -- WRIT.scr:99
    do return mm9.gotoLabel(script, ctx, "Init") end -- WRIT.scr:101
end

return script
