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
        local object = ctx:object("DestructableProp0") -- NPC215.scr:21
        object:setFlag("visible", true) -- NPC215.scr:22
        object:setFlag("solid", true) -- NPC215.scr:23
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
        ctx:object("Shooter6"):trigger("On") -- NPC215.scr:44-45
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
    ctx:object("Shooter6"):trigger("Off") -- NPC215.scr:64-65
    do return ctx:exit("") end -- NPC215.scr:66
end

script.labels["Init"] = function(ctx)
    -- NPC215.scr:69
    if ctx:hasKey(1022) then -- NPC215.scr:74-75
        do return ctx:exit("") end -- NPC215.scr:76
    end -- NPC215.scr:77
    local object = ctx:object("DestructableProp0") -- NPC215.scr:79
    object:setFlag("visible", false) -- NPC215.scr:80
    object:setFlag("solid", false) -- NPC215.scr:81
    object:setFlag("gravity", false) -- NPC215.scr:82
    do return ctx:exit("") end -- NPC215.scr:84
end

script.labels["Main"] = function(ctx)
    -- NPC215.scr:86
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC215.scr:93
    -- Addtrigger Use, OnUse
    ctx:atTime(22, 0, "OnFire", "OnFire") -- NPC215.scr:96
    ctx:atTime(4, 0, "Off", "Off") -- NPC215.scr:97
    ctx:wait(1, 1, "Init") -- NPC215.scr:98
    do return ctx:exit("") end -- NPC215.scr:99
end

return script
