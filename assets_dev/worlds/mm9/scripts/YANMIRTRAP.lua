-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRTRAP.scr"
script.includes = {}
script.labels = {}


-- YanmirTrap.scr
-- by SJR
-- 10-26-01
-- Purpose:take care of the
-- giant falling through
-- the floor.
-- edited by Bones 10/17/02
-- TELP Patch 1.3 -- keeps trigger on after re-enter if all beams broken
-- removes perception brushes for broken beams after re-entering
script.labels["Main"] = function(ctx)
    -- YANMIRTRAP.scr:20
    ctx:getParam(0, "sTitanTrapName") -- YANMIRTRAP.scr:22
    ctx:addTrigger("SupportBroken", "CheckCount") -- YANMIRTRAP.scr:24
    do return ctx:exit(1) end -- YANMIRTRAP.scr:26
end

script.labels["CheckCount"] = function(ctx)
    -- YANMIRTRAP.scr:29
    ctx:set("nCounter", "nCounter + 1") -- YANMIRTRAP.scr:31
    if ctx:condition("nCounter>=6") then -- YANMIRTRAP.scr:32
        ctx:removeTrigger("SupportBroken") -- YANMIRTRAP.scr:33
        ctx:state().hTitanTrap = ctx:objectOrNil("sTitanTrapName") -- YANMIRTRAP.scr:35
        if ctx:condition("hTitanTrap!=0") then -- YANMIRTRAP.scr:36
            ctx:trigger("hTitanTrap", "on") -- YANMIRTRAP.scr:37
        end -- YANMIRTRAP.scr:38
    end -- YANMIRTRAP.scr:39
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- YANMIRTRAP.scr:41
    ctx:onEvent("OnPostSaveLoad", "Init") -- YANMIRTRAP.scr:42
    mm9.gosub(script, ctx, "Init") -- YANMIRTRAP.scr:43
    do return ctx:exit(1) end -- YANMIRTRAP.scr:45
end

script.labels["Init"] = function(ctx)
    -- YANMIRTRAP.scr:49
    -- Bones
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush0") -- YANMIRTRAP.scr:53
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:54
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush2") -- YANMIRTRAP.scr:55
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:56
    end -- YANMIRTRAP.scr:57
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush1") -- YANMIRTRAP.scr:59
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:60
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush5") -- YANMIRTRAP.scr:61
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:62
    end -- YANMIRTRAP.scr:63
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush2") -- YANMIRTRAP.scr:65
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:66
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush3") -- YANMIRTRAP.scr:67
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:68
    end -- YANMIRTRAP.scr:69
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush3") -- YANMIRTRAP.scr:71
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:72
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush6") -- YANMIRTRAP.scr:73
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:74
    end -- YANMIRTRAP.scr:75
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush4") -- YANMIRTRAP.scr:77
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:78
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush4") -- YANMIRTRAP.scr:79
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:80
    end -- YANMIRTRAP.scr:81
    ctx:state().hTitanTrap = ctx:objectOrNil("DestructableBrush5") -- YANMIRTRAP.scr:83
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:84
        ctx:state().hTitanTrap = ctx:objectOrNil("PerceptionBrush7") -- YANMIRTRAP.scr:85
        ctx:object("hTitanTrap"):remove() -- YANMIRTRAP.scr:86
    end -- YANMIRTRAP.scr:87
    if ctx:condition("nCounter < 6") then -- YANMIRTRAP.scr:89
        do return ctx:exit("") end -- YANMIRTRAP.scr:90
    end -- YANMIRTRAP.scr:91
    ctx:object("sTitanTrapName"):trigger("on") -- YANMIRTRAP.scr:93-94
    do return ctx:exit("") end -- YANMIRTRAP.scr:96
end

return script
