-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TOWNPORTAL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- TownPortal.scr
-- 10/4
-- timmy
-- gives party specific item
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- TOWNPORTAL.scr:27
    if ctx:hasKey("nKey") then -- TOWNPORTAL.scr:30-31
        do return ctx:exit("") end -- TOWNPORTAL.scr:32
    end -- TOWNPORTAL.scr:33
    ctx:giveKey("nKey") -- TOWNPORTAL.scr:35
    ctx:self():setModelFilenames("models\\Props\\Portal-Whole.ABC", "Skins\\Props\\PortalClean.dtx") -- TOWNPORTAL.scr:36
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- TOWNPORTAL.scr:37
    do return ctx:exit("") end -- TOWNPORTAL.scr:38
end

script.labels["FixCheck"] = function(ctx)
    -- TOWNPORTAL.scr:41
    if ctx:hasKey("nKey") then -- TOWNPORTAL.scr:43-44
        ctx:self():setModelFilenames("models\\Props\\Portal-Whole.ABC", "Skins\\Props\\PortalClean.dtx") -- TOWNPORTAL.scr:45
        do return ctx:exit("") end -- TOWNPORTAL.scr:46
    end -- TOWNPORTAL.scr:47
    do return ctx:exit("") end -- TOWNPORTAL.scr:49
end

script.labels["Init"] = function(ctx)
    -- TOWNPORTAL.scr:51
    if ctx:condition("sLocation==Thjorgard") then -- TOWNPORTAL.scr:54
        ctx:state().nKey = 5011 -- TOWNPORTAL.scr:55
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:56
        do return ctx:exit("") end -- TOWNPORTAL.scr:57
    end -- TOWNPORTAL.scr:58
    if ctx:condition("sLocation==Sturmford") then -- TOWNPORTAL.scr:61
        ctx:state().nKey = 5012 -- TOWNPORTAL.scr:62
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:63
        do return ctx:exit("") end -- TOWNPORTAL.scr:64
    end -- TOWNPORTAL.scr:65
    if ctx:condition("sLocation==Drangheim") then -- TOWNPORTAL.scr:68
        ctx:state().nKey = 5013 -- TOWNPORTAL.scr:69
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:70
        do return ctx:exit("") end -- TOWNPORTAL.scr:71
    end -- TOWNPORTAL.scr:72
    if ctx:condition("sLocation==Guberland") then -- TOWNPORTAL.scr:75
        ctx:state().nKey = 5014 -- TOWNPORTAL.scr:76
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:77
        do return ctx:exit("") end -- TOWNPORTAL.scr:78
    end -- TOWNPORTAL.scr:79
    if ctx:condition("sLocation==Frosgard") then -- TOWNPORTAL.scr:82
        ctx:state().nKey = 5015 -- TOWNPORTAL.scr:83
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:84
        do return ctx:exit("") end -- TOWNPORTAL.scr:85
    end -- TOWNPORTAL.scr:86
    if ctx:condition("sLocation==Thronheim") then -- TOWNPORTAL.scr:89
        ctx:state().nKey = 5016 -- TOWNPORTAL.scr:90
        mm9.gosub(script, ctx, "FixCheck") -- TOWNPORTAL.scr:91
        do return ctx:exit("") end -- TOWNPORTAL.scr:92
    end -- TOWNPORTAL.scr:93
    do return ctx:exit("") end -- TOWNPORTAL.scr:95
end

script.labels["Main"] = function(ctx)
    -- TOWNPORTAL.scr:98
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- TOWNPORTAL.scr:103
    ctx:getParam(0, "sLocation") -- TOWNPORTAL.scr:104
    ctx:onEvent("OnPostStartWorld", "Init") -- TOWNPORTAL.scr:105
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- TOWNPORTAL.scr:106
    ctx:onEvent("OnPostSaveLoad", "Init") -- TOWNPORTAL.scr:107
    ctx:wait(1, .1, "Init") -- TOWNPORTAL.scr:108
    do return ctx:exit("") end -- TOWNPORTAL.scr:109
end

return script
