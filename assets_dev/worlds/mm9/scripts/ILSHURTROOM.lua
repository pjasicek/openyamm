-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSHURTROOM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- ILShurtroom.scr
-- Timmy
-- This script Handles the hurting room
-- Parameters:
script.labels["OnUse"] = function(ctx)
    -- ILSHURTROOM.scr:24
    if ctx:condition("BookOpen==true") then -- ILSHURTROOM.scr:27
        do return mm9.gotoLabel(script, ctx, "closebook") end -- ILSHURTROOM.scr:28
    end -- ILSHURTROOM.scr:29
    if ctx:condition("doorclosed==False") then -- ILSHURTROOM.scr:31
        do return ctx:exit("") end -- ILSHURTROOM.scr:32
    end -- ILSHURTROOM.scr:33
    ctx:command("getobjecthandle", "healinside2, g_hobject") -- ILSHURTROOM.scr:36
    ctx:trigger("g_hobject", "DamageOn") -- ILSHURTROOM.scr:37
    ctx:command("playanim", "OpenBook") -- ILSHURTROOM.scr:38
    ctx:command("set", "BookOpen, true") -- ILSHURTROOM.scr:39
    do return ctx:exit("") end -- ILSHURTROOM.scr:40
end

script.labels["Onopen"] = function(ctx)
    -- ILSHURTROOM.scr:42
    ctx:command("set", "doorclosed, false") -- ILSHURTROOM.scr:45
    ctx:command("getobjecthandle", "healinside2, g_hobject") -- ILSHURTROOM.scr:47
    ctx:trigger("g_hobject", "DamageOff") -- ILSHURTROOM.scr:48
    do return ctx:exit("") end -- ILSHURTROOM.scr:49
end

script.labels["Onclose"] = function(ctx)
    -- ILSHURTROOM.scr:52
    ctx:command("set", "doorclosed, true") -- ILSHURTROOM.scr:55
    do return ctx:exit("") end -- ILSHURTROOM.scr:56
end

script.labels["Onbreak"] = function(ctx)
    -- ILSHURTROOM.scr:60
    ctx:command("set", "broken, true") -- ILSHURTROOM.scr:63
    ctx:command("getobjecthandle", "healinside2, g_hobject") -- ILSHURTROOM.scr:65
    ctx:trigger("g_hobject", "DamageOff") -- ILSHURTROOM.scr:66
    do return ctx:exit("") end -- ILSHURTROOM.scr:67
end

script.labels["CloseBook"] = function(ctx)
    -- ILSHURTROOM.scr:72
    ctx:command("playanim", "CloseBook") -- ILSHURTROOM.scr:75
    ctx:command("getobjecthandle", "healinside2, g_hobject") -- ILSHURTROOM.scr:76
    ctx:trigger("g_hobject", "DamageOff") -- ILSHURTROOM.scr:77
    ctx:command("set", "BookOpen, false") -- ILSHURTROOM.scr:78
end

script.labels["Main"] = function(ctx)
    -- ILSHURTROOM.scr:81
    -- TRACEON
    ctx:addTrigger("use", "OnUse") -- ILSHURTROOM.scr:91
    ctx:addTrigger("open", "Onopen") -- ILSHURTROOM.scr:92
    ctx:addTrigger("close", "Onclose") -- ILSHURTROOM.scr:93
    ctx:addTrigger("break", "Onbreak") -- ILSHURTROOM.scr:94
    do return ctx:exit("") end -- ILSHURTROOM.scr:95
end

return script
