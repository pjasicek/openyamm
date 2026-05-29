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
    ctx:object("healinside2"):trigger("DamageOn") -- ILSHURTROOM.scr:36-37
    ctx:self():playAnimation("OpenBook") -- ILSHURTROOM.scr:38
    ctx:state().BookOpen = true -- ILSHURTROOM.scr:39
    do return ctx:exit("") end -- ILSHURTROOM.scr:40
end

script.labels["Onopen"] = function(ctx)
    -- ILSHURTROOM.scr:42
    ctx:state().doorclosed = false -- ILSHURTROOM.scr:45
    ctx:object("healinside2"):trigger("DamageOff") -- ILSHURTROOM.scr:47-48
    do return ctx:exit("") end -- ILSHURTROOM.scr:49
end

script.labels["Onclose"] = function(ctx)
    -- ILSHURTROOM.scr:52
    ctx:state().doorclosed = true -- ILSHURTROOM.scr:55
    do return ctx:exit("") end -- ILSHURTROOM.scr:56
end

script.labels["Onbreak"] = function(ctx)
    -- ILSHURTROOM.scr:60
    ctx:state().broken = true -- ILSHURTROOM.scr:63
    ctx:object("healinside2"):trigger("DamageOff") -- ILSHURTROOM.scr:65-66
    do return ctx:exit("") end -- ILSHURTROOM.scr:67
end

script.labels["CloseBook"] = function(ctx)
    -- ILSHURTROOM.scr:72
    ctx:self():playAnimation("CloseBook") -- ILSHURTROOM.scr:75
    ctx:object("healinside2"):trigger("DamageOff") -- ILSHURTROOM.scr:76-77
    ctx:state().BookOpen = false -- ILSHURTROOM.scr:78
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
