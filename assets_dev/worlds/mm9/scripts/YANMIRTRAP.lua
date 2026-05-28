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
    ctx:command("ncounter", "= nCounter + 1") -- YANMIRTRAP.scr:31
    if ctx:condition("nCounter>=6") then -- YANMIRTRAP.scr:32
        ctx:command("removetrigger", "SupportBroken") -- YANMIRTRAP.scr:33
        ctx:command("getobjecthandle", "sTitanTrapName, hTitanTrap") -- YANMIRTRAP.scr:35
        if ctx:condition("hTitanTrap!=0") then -- YANMIRTRAP.scr:36
            ctx:trigger("hTitanTrap", "on") -- YANMIRTRAP.scr:37
        end -- YANMIRTRAP.scr:38
    end -- YANMIRTRAP.scr:39
    ctx:command("onpostminisaveload", "Init") -- YANMIRTRAP.scr:41
    ctx:command("onpostsaveload", "Init") -- YANMIRTRAP.scr:42
    mm9.gosub(script, ctx, "Init") -- YANMIRTRAP.scr:43
    do return ctx:exit(1) end -- YANMIRTRAP.scr:45
end

script.labels["Init"] = function(ctx)
    -- YANMIRTRAP.scr:49
    -- Bones
    ctx:command("getobjecthandle", "DestructableBrush0 hTitanTrap") -- YANMIRTRAP.scr:53
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:54
        ctx:command("getobjecthandle", "PerceptionBrush2 hTitanTrap") -- YANMIRTRAP.scr:55
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:56
    end -- YANMIRTRAP.scr:57
    ctx:command("getobjecthandle", "DestructableBrush1 hTitanTrap") -- YANMIRTRAP.scr:59
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:60
        ctx:command("getobjecthandle", "PerceptionBrush5 hTitanTrap") -- YANMIRTRAP.scr:61
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:62
    end -- YANMIRTRAP.scr:63
    ctx:command("getobjecthandle", "DestructableBrush2 hTitanTrap") -- YANMIRTRAP.scr:65
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:66
        ctx:command("getobjecthandle", "PerceptionBrush3 hTitanTrap") -- YANMIRTRAP.scr:67
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:68
    end -- YANMIRTRAP.scr:69
    ctx:command("getobjecthandle", "DestructableBrush3 hTitanTrap") -- YANMIRTRAP.scr:71
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:72
        ctx:command("getobjecthandle", "PerceptionBrush6 hTitanTrap") -- YANMIRTRAP.scr:73
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:74
    end -- YANMIRTRAP.scr:75
    ctx:command("getobjecthandle", "DestructableBrush4 hTitanTrap") -- YANMIRTRAP.scr:77
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:78
        ctx:command("getobjecthandle", "PerceptionBrush4 hTitanTrap") -- YANMIRTRAP.scr:79
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:80
    end -- YANMIRTRAP.scr:81
    ctx:command("getobjecthandle", "DestructableBrush5 hTitanTrap") -- YANMIRTRAP.scr:83
    if ctx:condition("hTitanTrap == 0") then -- YANMIRTRAP.scr:84
        ctx:command("getobjecthandle", "PerceptionBrush7 hTitanTrap") -- YANMIRTRAP.scr:85
        ctx:command("removeobject", "hTitanTrap") -- YANMIRTRAP.scr:86
    end -- YANMIRTRAP.scr:87
    if ctx:condition("nCounter < 6") then -- YANMIRTRAP.scr:89
        do return ctx:exit("") end -- YANMIRTRAP.scr:90
    end -- YANMIRTRAP.scr:91
    ctx:command("getobjecthandle", "sTitanTrapName hTitanTrap") -- YANMIRTRAP.scr:93
    ctx:trigger("hTitanTrap", "on") -- YANMIRTRAP.scr:94
    do return ctx:exit("") end -- YANMIRTRAP.scr:96
end

return script
