-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRAININGENTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- gives party specific item
-- edited by Bones 3/27/03
-- TELP Patch 1.3 -- moved reward from TRAININGHALLEXIT.SCR (all THall loads)
-- removed unnecessary PerceptionBrushes (new Thjorgard loads)
-- Parameters
-- P0 Item number of item to give
script.labels["OnBreak"] = function(ctx)
    -- TRAININGENTER.scr:29
    ctx:command("getobjecthandle", "ExitTrigger0 g_hobject") -- TRAININGENTER.scr:32
    ctx:trigger("g_hobject", "on") -- TRAININGENTER.scr:33
    do return ctx:exit("") end -- TRAININGENTER.scr:34
end

script.labels["Init"] = function(ctx)
    -- TRAININGENTER.scr:37
    if ctx:hasKey(301) then -- TRAININGENTER.scr:40-41
        if ctx:condition("sLocation==TrainingHall") then -- TRAININGENTER.scr:42
            ctx:command("getobjecthandle", "ExitTrigger0 g_hobject") -- TRAININGENTER.scr:43
            ctx:trigger("g_hobject", "on") -- TRAININGENTER.scr:44
        else -- TRAININGENTER.scr:45
            ctx:command("getobjecthandle", "ExitTrigger6 g_hobject") -- TRAININGENTER.scr:46
            ctx:trigger("g_hobject", "on") -- TRAININGENTER.scr:47
        end -- TRAININGENTER.scr:48
        do return ctx:exit("") end -- TRAININGENTER.scr:49
    end -- TRAININGENTER.scr:50
    do return ctx:exit("") end -- TRAININGENTER.scr:51
end

script.labels["Main"] = function(ctx)
    -- TRAININGENTER.scr:54
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sLocation") -- TRAININGENTER.scr:59
    ctx:addTrigger("Break", "OnBreak") -- TRAININGENTER.scr:60
    ctx:command("onpoststartworld", "Init") -- TRAININGENTER.scr:61
    ctx:command("onpostminisaveload", "Init") -- TRAININGENTER.scr:62
    ctx:command("onpostsaveload", "Init") -- TRAININGENTER.scr:63
    ctx:command("wait", "1 .1 Init") -- TRAININGENTER.scr:64
    do return ctx:exit("") end -- TRAININGENTER.scr:65
end

script.labels["OnBreak"] = function(ctx)
    -- TRAININGENTER.scr:68
    -- overloaded
    if not ctx:hasKey(301) then -- TRAININGENTER.scr:72-73
        ctx:giveKey(301) -- TRAININGENTER.scr:74
        ctx:command("giveattribute", "0 5 1") -- TRAININGENTER.scr:75
        ctx:command("giveattribute", "1 5 1") -- TRAININGENTER.scr:76
        ctx:giveExp(20000) -- TRAININGENTER.scr:77
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 5000, FALSE, 100") -- TRAININGENTER.scr:78
    end -- TRAININGENTER.scr:79
    do return mm9.gotoLabel(script, ctx, "OnBreak") end -- TRAININGENTER.scr:80
end

script.labels["Init"] = function(ctx)
    -- TRAININGENTER.scr:83
    -- overloaded -- Bones
    if ctx:condition("sLocation == TrainingHall") then -- TRAININGENTER.scr:87
        if ctx:hasKey(301) then -- TRAININGENTER.scr:88-89
            ctx:command("getobjecthandle", "DestructableBrush12 g_hObject") -- TRAININGENTER.scr:90
            ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:91
        end -- TRAININGENTER.scr:92
        do return mm9.gotoLabel(script, ctx, "Init") end -- TRAININGENTER.scr:93
    end -- TRAININGENTER.scr:94
    ctx:command("getobjecthandle", "DestructableBrush7 g_hObject") -- TRAININGENTER.scr:96
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:97
        ctx:command("getobjecthandle", "PerceptionBrush6 g_hObject") -- TRAININGENTER.scr:98
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:99
    end -- TRAININGENTER.scr:100
    ctx:command("getobjecthandle", "DestructableBrush8 g_hObject") -- TRAININGENTER.scr:102
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:103
        ctx:command("getobjecthandle", "PerceptionBrush8 g_hObject") -- TRAININGENTER.scr:104
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:105
    end -- TRAININGENTER.scr:106
    ctx:command("getobjecthandle", "DestructableBrush9 g_hObject") -- TRAININGENTER.scr:108
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:109
        ctx:command("getobjecthandle", "PerceptionBrush10 g_hObject") -- TRAININGENTER.scr:110
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:111
    end -- TRAININGENTER.scr:112
    ctx:command("getobjecthandle", "DestructableBrush10 g_hObject") -- TRAININGENTER.scr:114
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:115
        ctx:command("getobjecthandle", "PerceptionBrush11 g_hObject") -- TRAININGENTER.scr:116
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:117
    end -- TRAININGENTER.scr:118
    ctx:command("getobjecthandle", "DestructableBrush11 g_hObject") -- TRAININGENTER.scr:120
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:121
        ctx:command("getobjecthandle", "PerceptionBrush7 g_hObject") -- TRAININGENTER.scr:122
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:123
    end -- TRAININGENTER.scr:124
    ctx:command("getobjecthandle", "DestructableBrush12 g_hObject") -- TRAININGENTER.scr:126
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:127
        ctx:command("getobjecthandle", "PerceptionBrush9 g_hObject") -- TRAININGENTER.scr:128
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:129
    end -- TRAININGENTER.scr:130
    ctx:command("getobjecthandle", "DestructableBrush13 g_hObject") -- TRAININGENTER.scr:132
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:133
        ctx:command("getobjecthandle", "PerceptionBrush5 g_hObject") -- TRAININGENTER.scr:134
        ctx:command("removeobject", "g_hObject") -- TRAININGENTER.scr:135
    end -- TRAININGENTER.scr:136
    do return mm9.gotoLabel(script, ctx, "Init") end -- TRAININGENTER.scr:138
end

return script
