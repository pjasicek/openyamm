-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PENTAGRAMPUZZLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }

-- PentagramPuzzle.scr
-- by SJR
-- 10-29-01
-- Purpose:puzzle used to get
-- the capstone from
-- VerhoffinRuins. step
-- on points in certain order
script.labels["Main"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:26
    ctx:getParam(0, "sDoorRName") -- PENTAGRAMPUZZLE.scr:28
    ctx:getParam(1, "sDoorLName") -- PENTAGRAMPUZZLE.scr:29
    ctx:onEvent("OnPostStartWorld", "InitPentagramPuzzle") -- PENTAGRAMPUZZLE.scr:31
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:33
end

script.labels["InitPentagramPuzzle"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:36
    ctx:state().hDoorR = ctx:objectOrNil("sDoorRName") -- PENTAGRAMPUZZLE.scr:38
    ctx:state().hDoorL = ctx:objectOrNil("sDoorLName") -- PENTAGRAMPUZZLE.scr:39
    ctx:state().hTriggerOn = ctx:objectOrNil("TriggerPuzzleOn") -- PENTAGRAMPUZZLE.scr:40
    ctx:state().hTriggerOff = ctx:objectOrNil("TriggerPuzzleOff") -- PENTAGRAMPUZZLE.scr:41
    ctx:trigger("hDoorR", "close") -- PENTAGRAMPUZZLE.scr:43
    ctx:trigger("hDoorL", "close") -- PENTAGRAMPUZZLE.scr:44
    ctx:trigger("hDoorR", "lock") -- PENTAGRAMPUZZLE.scr:46
    ctx:trigger("hDoorL", "lock") -- PENTAGRAMPUZZLE.scr:47
    ctx:addTrigger("start", "StartPuzzle") -- PENTAGRAMPUZZLE.scr:49
    ctx:arrayPut("spFlames", 0, "PentaFire1") -- PENTAGRAMPUZZLE.scr:51
    ctx:arrayPut("spFlames", 1, "PentaFire2") -- PENTAGRAMPUZZLE.scr:52
    ctx:arrayPut("spFlames", 2, "PentaFire3") -- PENTAGRAMPUZZLE.scr:53
    ctx:arrayPut("spFlames", 3, "PentaFire4") -- PENTAGRAMPUZZLE.scr:54
    ctx:arrayPut("spFlames", 4, "PentaFire5") -- PENTAGRAMPUZZLE.scr:55
    ctx:arrayPut("spPoints", 0, "TriggerPentagram1") -- PENTAGRAMPUZZLE.scr:57
    ctx:arrayPut("spPoints", 1, "TriggerPentagram2") -- PENTAGRAMPUZZLE.scr:58
    ctx:arrayPut("spPoints", 2, "TriggerPentagram3") -- PENTAGRAMPUZZLE.scr:59
    ctx:arrayPut("spPoints", 3, "TriggerPentagram4") -- PENTAGRAMPUZZLE.scr:60
    ctx:arrayPut("spPoints", 4, "TriggerPentagram5") -- PENTAGRAMPUZZLE.scr:61
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:63
end

script.labels["StartPuzzle"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:66
    if ctx:condition("hTriggerOn!=NULL") then -- PENTAGRAMPUZZLE.scr:68
        ctx:trigger("hTriggerOn", "trigger") -- PENTAGRAMPUZZLE.scr:69
    end -- PENTAGRAMPUZZLE.scr:70
    ctx:addTrigger("first", "FirstStep") -- PENTAGRAMPUZZLE.scr:72
    ctx:addTrigger("second", "SecondStep") -- PENTAGRAMPUZZLE.scr:73
    ctx:addTrigger("third", "ThirdStep") -- PENTAGRAMPUZZLE.scr:74
    ctx:addTrigger("fourth", "FourthStep") -- PENTAGRAMPUZZLE.scr:75
    ctx:addTrigger("fifth", "FifthStep") -- PENTAGRAMPUZZLE.scr:76
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:78
end

script.labels["FirstStep"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:81
    if ctx:condition("nProgress!=0") then -- PENTAGRAMPUZZLE.scr:83
        mm9.gosub(script, ctx, "OnFailure") -- PENTAGRAMPUZZLE.scr:84
        do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:85
    end -- PENTAGRAMPUZZLE.scr:86
    ctx:state().nProgress = 1 -- PENTAGRAMPUZZLE.scr:87
    mm9.gosub(script, ctx, "OnSuccess") -- PENTAGRAMPUZZLE.scr:88
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:89
end

script.labels["SecondStep"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:92
    if ctx:condition("nProgress!=1") then -- PENTAGRAMPUZZLE.scr:94
        mm9.gosub(script, ctx, "OnFailure") -- PENTAGRAMPUZZLE.scr:95
        do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:96
    end -- PENTAGRAMPUZZLE.scr:97
    ctx:state().nProgress = 2 -- PENTAGRAMPUZZLE.scr:98
    mm9.gosub(script, ctx, "OnSuccess") -- PENTAGRAMPUZZLE.scr:99
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:100
end

script.labels["ThirdStep"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:103
    if ctx:condition("nProgress!=2") then -- PENTAGRAMPUZZLE.scr:105
        mm9.gosub(script, ctx, "OnFailure") -- PENTAGRAMPUZZLE.scr:106
        do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:107
    end -- PENTAGRAMPUZZLE.scr:108
    ctx:state().nProgress = 3 -- PENTAGRAMPUZZLE.scr:109
    mm9.gosub(script, ctx, "OnSuccess") -- PENTAGRAMPUZZLE.scr:110
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:111
end

script.labels["FourthStep"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:114
    if ctx:condition("nProgress!=3") then -- PENTAGRAMPUZZLE.scr:116
        mm9.gosub(script, ctx, "OnFailure") -- PENTAGRAMPUZZLE.scr:117
        do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:118
    end -- PENTAGRAMPUZZLE.scr:119
    ctx:state().nProgress = 4 -- PENTAGRAMPUZZLE.scr:120
    mm9.gosub(script, ctx, "OnSuccess") -- PENTAGRAMPUZZLE.scr:121
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:122
end

script.labels["FifthStep"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:125
    if ctx:condition("nProgress!=4") then -- PENTAGRAMPUZZLE.scr:127
        mm9.gosub(script, ctx, "OnFailure") -- PENTAGRAMPUZZLE.scr:128
        do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:129
    end -- PENTAGRAMPUZZLE.scr:130
    mm9.gosub(script, ctx, "OnSuccess") -- PENTAGRAMPUZZLE.scr:131
    mm9.gosub(script, ctx, "UnlockDoor") -- PENTAGRAMPUZZLE.scr:132
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:133
end

script.labels["OnSuccess"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:136
    ctx:playSound("sounds\\door\\doorlatch01.wav", "DoNothing", 1, 500, 0, 100) -- PENTAGRAMPUZZLE.scr:138
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:140
end

script.labels["OnFailure"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:143
    if ctx:condition("hTriggerOn!=NULL") then -- PENTAGRAMPUZZLE.scr:145
        ctx:trigger("hTriggerOn", "trigger") -- PENTAGRAMPUZZLE.scr:146
    end -- PENTAGRAMPUZZLE.scr:147
    ctx:state().nProgress = 0 -- PENTAGRAMPUZZLE.scr:148
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:150
end

script.labels["UnlockDoor"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:153
    if ctx:condition("hTriggerOff!=NULL") then -- PENTAGRAMPUZZLE.scr:155
        ctx:trigger("hTriggerOff", "trigger") -- PENTAGRAMPUZZLE.scr:156
    end -- PENTAGRAMPUZZLE.scr:157
    if ctx:condition("hDoorR!=NULL") then -- PENTAGRAMPUZZLE.scr:158
        ctx:trigger("hDoorR", "unlock") -- PENTAGRAMPUZZLE.scr:159
        ctx:trigger(nil, "open") -- PENTAGRAMPUZZLE.scr:160
    end -- PENTAGRAMPUZZLE.scr:161
    if ctx:condition("hDoorL!=NULL") then -- PENTAGRAMPUZZLE.scr:162
        ctx:trigger("hDoorL", "unlock") -- PENTAGRAMPUZZLE.scr:163
        ctx:trigger("hDoorL", "open") -- PENTAGRAMPUZZLE.scr:164
    end -- PENTAGRAMPUZZLE.scr:165
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:167
end

script.labels["InitPentagramPuzzle"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:170
    -- overloaded -- Bones
    ctx:onEvent("OnPostSaveLoad", "StopMoving") -- PENTAGRAMPUZZLE.scr:173
    ctx:onEvent("OnPostMiniSaveLoad", "StopMoving") -- PENTAGRAMPUZZLE.scr:174
    do return mm9.gotoLabel(script, ctx, "InitPentagramPuzzle") end -- PENTAGRAMPUZZLE.scr:175
end

script.labels["StopMoving"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:178
    -- overloaded -- Bones
    if ctx:condition("FALSE == 0") then -- PENTAGRAMPUZZLE.scr:181
        ctx:state().hDoorR = ctx:objectOrNil("sDoorRName") -- PENTAGRAMPUZZLE.scr:182
        if ctx:condition("hDoorR == NULL") then -- PENTAGRAMPUZZLE.scr:183
            ctx:wait(0, .2, "StopMoving") -- PENTAGRAMPUZZLE.scr:184
        else -- PENTAGRAMPUZZLE.scr:185
            ctx:state().hDoorL = ctx:objectOrNil("sDoorLName") -- PENTAGRAMPUZZLE.scr:186
            ctx:state().hTriggerOn = ctx:objectOrNil("TriggerPuzzleOn") -- PENTAGRAMPUZZLE.scr:188
            ctx:state().hTriggerOff = ctx:objectOrNil("TriggerPuzzleOff") -- PENTAGRAMPUZZLE.scr:189
            ctx:trigger("hDoorR", "close") -- PENTAGRAMPUZZLE.scr:191
            ctx:trigger("hDoorL", "close") -- PENTAGRAMPUZZLE.scr:192
            ctx:object("hDoorR"):setStat("Locked", "TRUE") -- PENTAGRAMPUZZLE.scr:194
            ctx:object("hDoorL"):setStat("Locked", "TRUE") -- PENTAGRAMPUZZLE.scr:195
        end -- PENTAGRAMPUZZLE.scr:196
    end -- PENTAGRAMPUZZLE.scr:197
    do return ctx:exit("") end -- PENTAGRAMPUZZLE.scr:199
end

script.labels["UnlockDoor"] = function(ctx)
    -- PENTAGRAMPUZZLE.scr:202
    -- overloaded -- Bones
    ctx:state().hTriggerOff = ctx:objectOrNil("TriggerPuzzleOff") -- PENTAGRAMPUZZLE.scr:205
    if ctx:condition("hTriggerOff != NULL") then -- PENTAGRAMPUZZLE.scr:206
        ctx:trigger("hTriggerOff", "trigger") -- PENTAGRAMPUZZLE.scr:207
    end -- PENTAGRAMPUZZLE.scr:208
    ctx:state().hDoorR = ctx:objectOrNil("sDoorRName") -- PENTAGRAMPUZZLE.scr:210
    if ctx:condition("hDoorR != NULL") then -- PENTAGRAMPUZZLE.scr:211
        ctx:object("hDoorR"):setStat("Locked", "FALSE") -- PENTAGRAMPUZZLE.scr:212
    end -- PENTAGRAMPUZZLE.scr:213
    ctx:state().hDoorL = ctx:objectOrNil("sDoorLName") -- PENTAGRAMPUZZLE.scr:215
    if ctx:condition("hDoorL != NULL") then -- PENTAGRAMPUZZLE.scr:216
        ctx:object("hDoorL"):setStat("Locked", "FALSE") -- PENTAGRAMPUZZLE.scr:217
        ctx:trigger("hDoorL", "open") -- PENTAGRAMPUZZLE.scr:218
    end -- PENTAGRAMPUZZLE.scr:219
    ctx:state().FALSE = 1 -- PENTAGRAMPUZZLE.scr:221
    do return ctx:exit("TRUE") end -- PENTAGRAMPUZZLE.scr:223
end

return script
