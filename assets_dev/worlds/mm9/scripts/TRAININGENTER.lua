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
    ctx:object("ExitTrigger0"):trigger("on") -- TRAININGENTER.scr:32-33
    do return ctx:exit("") end -- TRAININGENTER.scr:34
end

script.labels["Init"] = function(ctx)
    -- TRAININGENTER.scr:37
    if ctx:hasKey(301) then -- TRAININGENTER.scr:40-41
        if ctx:condition("sLocation==TrainingHall") then -- TRAININGENTER.scr:42
            ctx:object("ExitTrigger0"):trigger("on") -- TRAININGENTER.scr:43-44
        else -- TRAININGENTER.scr:45
            ctx:object("ExitTrigger6"):trigger("on") -- TRAININGENTER.scr:46-47
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
    ctx:onEvent("OnPostStartWorld", "Init") -- TRAININGENTER.scr:61
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- TRAININGENTER.scr:62
    ctx:onEvent("OnPostSaveLoad", "Init") -- TRAININGENTER.scr:63
    ctx:wait(1, .1, "Init") -- TRAININGENTER.scr:64
    do return ctx:exit("") end -- TRAININGENTER.scr:65
end

script.labels["OnBreak"] = function(ctx)
    -- TRAININGENTER.scr:68
    -- overloaded
    if not ctx:hasKey(301) then -- TRAININGENTER.scr:72-73
        ctx:giveKey(301) -- TRAININGENTER.scr:74
        ctx:giveAttribute(0, 5, 1) -- TRAININGENTER.scr:75
        ctx:giveAttribute(1, 5, 1) -- TRAININGENTER.scr:76
        ctx:giveExp(20000) -- TRAININGENTER.scr:77
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 5000, "FALSE", 100) -- TRAININGENTER.scr:78
    end -- TRAININGENTER.scr:79
    do return mm9.gotoLabel(script, ctx, "OnBreak") end -- TRAININGENTER.scr:80
end

script.labels["Init"] = function(ctx)
    -- TRAININGENTER.scr:83
    -- overloaded -- Bones
    if ctx:condition("sLocation == TrainingHall") then -- TRAININGENTER.scr:87
        if ctx:hasKey(301) then -- TRAININGENTER.scr:88-89
            ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush12") -- TRAININGENTER.scr:90
            ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:91
        end -- TRAININGENTER.scr:92
        do return mm9.gotoLabel(script, ctx, "Init") end -- TRAININGENTER.scr:93
    end -- TRAININGENTER.scr:94
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush7") -- TRAININGENTER.scr:96
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:97
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush6") -- TRAININGENTER.scr:98
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:99
    end -- TRAININGENTER.scr:100
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush8") -- TRAININGENTER.scr:102
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:103
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush8") -- TRAININGENTER.scr:104
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:105
    end -- TRAININGENTER.scr:106
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush9") -- TRAININGENTER.scr:108
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:109
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush10") -- TRAININGENTER.scr:110
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:111
    end -- TRAININGENTER.scr:112
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush10") -- TRAININGENTER.scr:114
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:115
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush11") -- TRAININGENTER.scr:116
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:117
    end -- TRAININGENTER.scr:118
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush11") -- TRAININGENTER.scr:120
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:121
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush7") -- TRAININGENTER.scr:122
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:123
    end -- TRAININGENTER.scr:124
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush12") -- TRAININGENTER.scr:126
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:127
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush9") -- TRAININGENTER.scr:128
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:129
    end -- TRAININGENTER.scr:130
    ctx:state().g_hObject = ctx:objectOrNil("DestructableBrush13") -- TRAININGENTER.scr:132
    if ctx:condition("g_hObject == 0") then -- TRAININGENTER.scr:133
        ctx:state().g_hObject = ctx:objectOrNil("PerceptionBrush5") -- TRAININGENTER.scr:134
        ctx:object("g_hObject"):remove() -- TRAININGENTER.scr:135
    end -- TRAININGENTER.scr:136
    do return mm9.gotoLabel(script, ctx, "Init") end -- TRAININGENTER.scr:138
end

return script
