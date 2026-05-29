-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PASSAGEMIRROR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }

-- PassageMirror.scr
-- by SJR
-- 11-06-01
-- Purpose:puzzle reflector
-- mirrors in desert
script.labels["Main"] = function(ctx)
    -- PASSAGEMIRROR.scr:30
    -- angle in clockwise degrees to target mirror
    ctx:getParam(0, "nTargetAngle") -- PASSAGEMIRROR.scr:33
    ctx:getParam(1, "sNextMirror") -- PASSAGEMIRROR.scr:34
    ctx:getParam(2, "sLightName") -- PASSAGEMIRROR.scr:35
    ctx:onEvent("OnPostStartWorld", "InitPassageMirror") -- PASSAGEMIRROR.scr:37
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- PASSAGEMIRROR.scr:38
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:40
end

script.labels["CacheFiles"] = function(ctx)
    -- PASSAGEMIRROR.scr:43
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:45
end

script.labels["InitPassageMirror"] = function(ctx)
    -- PASSAGEMIRROR.scr:48
    ctx:set("nTargetAngle", "nTargetAngle / dA") -- PASSAGEMIRROR.scr:50
    ctx:set("nMod", "360 / dA") -- PASSAGEMIRROR.scr:51
    ctx:addTrigger("use", "Rotate") -- PASSAGEMIRROR.scr:53
    ctx:addTrigger("off", "TakeFocus") -- PASSAGEMIRROR.scr:54
    ctx:addTrigger("trigger", "GiveFocus") -- PASSAGEMIRROR.scr:55
    ctx:state().hMirror = ctx:objectOrNil("sNextMirror") -- PASSAGEMIRROR.scr:58
    ctx:state().hLight = ctx:objectOrNil("sLightName") -- PASSAGEMIRROR.scr:59
    ctx:trigger("hLight", "on") -- PASSAGEMIRROR.scr:61
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:63
end

script.labels["Rotate"] = function(ctx)
    -- PASSAGEMIRROR.scr:66
    ctx:set("nCounter", "nCounter + 1") -- PASSAGEMIRROR.scr:68
    ctx:mod("nCounter", "nMod") -- PASSAGEMIRROR.scr:69
    ctx:self():rotate(0, 1, 0, "dA", 180, "DoNothing") -- PASSAGEMIRROR.scr:71
    if ctx:condition("nCounter!=nTargetAngle") then -- PASSAGEMIRROR.scr:73
        ctx:trigger("hMirror", "off") -- PASSAGEMIRROR.scr:74
    end -- PASSAGEMIRROR.scr:75
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:77
end

script.labels["TakeFocus"] = function(ctx)
    -- PASSAGEMIRROR.scr:80
    ctx:state().bOff = true -- PASSAGEMIRROR.scr:82
    ctx:trigger("hMirror", "off") -- PASSAGEMIRROR.scr:84
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:86
end

script.labels["GiveFocus"] = function(ctx)
    -- PASSAGEMIRROR.scr:89
    if ctx:condition("nCounter<30") then -- PASSAGEMIRROR.scr:91
        if ctx:condition("nCounter>6") then -- PASSAGEMIRROR.scr:92
            do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:93
        end -- PASSAGEMIRROR.scr:94
    end -- PASSAGEMIRROR.scr:95
    ctx:trigger("hLight", "rotate") -- PASSAGEMIRROR.scr:97
    if ctx:condition("nCounter==nTargetAngle") then -- PASSAGEMIRROR.scr:99
        ctx:state().bOff = false -- PASSAGEMIRROR.scr:100
        ctx:trigger("hMirror", "trigger") -- PASSAGEMIRROR.scr:101
    end -- PASSAGEMIRROR.scr:102
    do return ctx:exit("TRUE") end -- PASSAGEMIRROR.scr:104
end

return script
