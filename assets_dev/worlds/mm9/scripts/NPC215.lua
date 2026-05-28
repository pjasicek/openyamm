-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC215.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC100.scr
-- timmy
-- handles Bodvar's sunflower stuff
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC215.scr:16
    if ctx:hasKey(1022) then -- NPC215.scr:19-20
        ctx:command("getobjecthandle", "DestructableProp0 g_hobject") -- NPC215.scr:21
        ctx:command("setflag", "g_hobject, visible") -- NPC215.scr:22
        ctx:command("setflag", "g_hobject, solid") -- NPC215.scr:23
        -- setflag g_hobject, gravity
        do return ctx:exit("") end -- NPC215.scr:25
    end -- NPC215.scr:26
    do return ctx:exit("") end -- NPC215.scr:28
end

script.labels["OnFire"] = function(ctx)
    -- NPC215.scr:34
    if ctx:hasKey(72) then -- NPC215.scr:37-38
        do return ctx:exit("") end -- NPC215.scr:39
    end -- NPC215.scr:40
    if ctx:hasKey(71) then -- NPC215.scr:42-43
        ctx:command("getobjecthandle", "Shooter6 g_hobject") -- NPC215.scr:44
        ctx:trigger("g_hobject", "On") -- NPC215.scr:45
        do return ctx:exit("") end -- NPC215.scr:46
    end -- NPC215.scr:47
    do return ctx:exit("") end -- NPC215.scr:48
end

script.labels["Off"] = function(ctx)
    -- NPC215.scr:51
    if ctx:hasKey(72) then -- NPC215.scr:54-55
        do return ctx:exit("") end -- NPC215.scr:56
    end -- NPC215.scr:57
    if not ctx:hasKey(71) then -- NPC215.scr:59-60
        do return ctx:exit("") end -- NPC215.scr:61
    end -- NPC215.scr:62
    ctx:command("getobjecthandle", "Shooter6 g_hobject") -- NPC215.scr:64
    ctx:trigger("g_hobject", "Off") -- NPC215.scr:65
    do return ctx:exit("") end -- NPC215.scr:66
end

script.labels["Init"] = function(ctx)
    -- NPC215.scr:69
    if ctx:hasKey(1022) then -- NPC215.scr:74-75
        do return ctx:exit("") end -- NPC215.scr:76
    end -- NPC215.scr:77
    ctx:command("getobjecthandle", "DestructableProp0 g_hobject") -- NPC215.scr:79
    ctx:command("clearflag", "g_hobject, visible") -- NPC215.scr:80
    ctx:command("clearflag", "g_hobject, solid") -- NPC215.scr:81
    ctx:command("clearflag", "g_hobject, gravity") -- NPC215.scr:82
    do return ctx:exit("") end -- NPC215.scr:84
end

script.labels["Main"] = function(ctx)
    -- NPC215.scr:86
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC215.scr:93
    -- Addtrigger Use, OnUse
    ctx:command("@m", "22 : 00 OnFire OnFire") -- NPC215.scr:96
    ctx:command("@m", "4 : 00 Off Off") -- NPC215.scr:97
    ctx:command("wait", "1 1 Init") -- NPC215.scr:98
    do return ctx:exit("") end -- NPC215.scr:99
end

return script
