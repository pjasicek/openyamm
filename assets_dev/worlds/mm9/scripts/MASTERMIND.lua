-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MASTERMIND.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListMaker.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "ThjorgardGamesCommon.inc" }

-- Mastermind.scr
-- by SJR
-- 12-18-01
-- Purpose:
-- ScriptParams:
-- p0 = name of correct flames
-- Triggers:
-- "check" = check for victory
-- "reset" = reset game
-- "update"= update array when color chosen
-- take this out and hardcode
script.labels["Main"] = function(ctx)
    -- MASTERMIND.scr:38
    ctx:getParam(0, "LISTNAME") -- MASTERMIND.scr:40
    ctx:state().LISTFIRST = 0 -- MASTERMIND.scr:42
    ctx:state().LISTLAST = 3 -- MASTERMIND.scr:43
    -- register our name
    ctx:state().LISTOBJECT = ctx:self() -- MASTERMIND.scr:46
    ctx:state().sMyName = ctx:object("LISTOBJECT"):name() -- MASTERMIND.scr:47
    ctx:setConsoleStrVar("MASTERMIND_NAME", "sMyName") -- MASTERMIND.scr:48
    ctx:onEvent("OnPostStartWorld", "InitMastermind") -- MASTERMIND.scr:50
    ctx:onEvent("OnPostMiniSaveLoad", "InitMastermind") -- MASTERMIND.scr:51
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:53
end

script.labels["InitMastermind"] = function(ctx)
    -- MASTERMIND.scr:56
    -- fill array with 'empty'
    ctx:state().nCounter = 0 -- MASTERMIND.scr:59
    while ctx:condition("nCounter<4") do -- MASTERMIND.scr:60
        ctx:arrayPut("npChosen", "nCounter", -1) -- MASTERMIND.scr:61
        ctx:set("nCounter", "nCounter + 1") -- MASTERMIND.scr:62
    end -- MASTERMIND.scr:63
    ctx:addTrigger("check", "CompareColors") -- MASTERMIND.scr:65
    ctx:addTrigger("reset", "GenerateColors") -- MASTERMIND.scr:66
    ctx:addTrigger("update", "ColorChosen") -- MASTERMIND.scr:67
    mm9.gosub(script, ctx, "GenerateColors") -- MASTERMIND.scr:69
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:71
end

script.labels["ColorChosen"] = function(ctx)
    -- MASTERMIND.scr:74
    -- a color was chosen, update npChosen
    if ctx:condition("nChances<=0") then -- MASTERMIND.scr:77
        do return ctx:exit("TRUE") end -- MASTERMIND.scr:78
    end -- MASTERMIND.scr:79
    if ctx:condition("bNeedsTicket==TRUE") then -- MASTERMIND.scr:81
        mm9.gosub(script, ctx, "CheckGameTicket") -- MASTERMIND.scr:82
        if ctx:condition("THJORGARD_RESULT==0") then -- MASTERMIND.scr:83
            do return ctx:exit("TRUE") end -- MASTERMIND.scr:84
        else -- MASTERMIND.scr:85
            ctx:state().bNeedsTicket = false -- MASTERMIND.scr:86
            mm9.gosub(script, ctx, "TakeGameTicket") -- MASTERMIND.scr:87
        end -- MASTERMIND.scr:88
    end -- MASTERMIND.scr:89
    -- get stone number and color
    ctx:getConsoleNumVar("MASTERMIND_INDEX", "nTemp1") -- MASTERMIND.scr:92
    ctx:getConsoleNumVar("MASTERMIND_COLOR", "nTemp2") -- MASTERMIND.scr:93
    -- update array
    ctx:arrayPut("npChosen", "nTemp1", "nTemp2") -- MASTERMIND.scr:95
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:97
end

script.labels["CompareColors"] = function(ctx)
    -- MASTERMIND.scr:100
    -- compares npCorrect with npChosen
    -- lights fire at each correct one
    if ctx:condition("nChances<=0") then -- MASTERMIND.scr:104
        do return ctx:exit("TRUE") end -- MASTERMIND.scr:105
    end -- MASTERMIND.scr:106
    if ctx:condition("bNeedsTicket==TRUE") then -- MASTERMIND.scr:108
        mm9.gosub(script, ctx, "CheckGameTicket") -- MASTERMIND.scr:109
        if ctx:condition("THJORGARD_RESULT==0") then -- MASTERMIND.scr:110
            do return ctx:exit("TRUE") end -- MASTERMIND.scr:111
        else -- MASTERMIND.scr:112
            ctx:state().bNeedsTicket = false -- MASTERMIND.scr:113
            mm9.gosub(script, ctx, "TakeGameTicket") -- MASTERMIND.scr:114
        end -- MASTERMIND.scr:115
    end -- MASTERMIND.scr:116
    ctx:state().nStoneCount = 0 -- MASTERMIND.scr:118
    ctx:state().nCounter = 0 -- MASTERMIND.scr:119
    while ctx:condition("nCounter<4") do -- MASTERMIND.scr:120
        ctx:arrayGet("npCorrect", "nCounter", "nTemp1") -- MASTERMIND.scr:121
        ctx:arrayGet("npChosen", "nCounter", "nTemp2") -- MASTERMIND.scr:122
        if ctx:condition("nTemp1==nTemp2") then -- MASTERMIND.scr:123
            ctx:set("nStoneCount", "nStoneCount + 1") -- MASTERMIND.scr:124
            ctx:set("LISTINDEX", "nCounter") -- MASTERMIND.scr:125
            mm9.gosub(script, ctx, "GetCurrentObject") -- MASTERMIND.scr:126
            ctx:trigger("LISTOBJECT", "on") -- MASTERMIND.scr:127
        end -- MASTERMIND.scr:128
        ctx:set("nCounter", "nCounter + 1") -- MASTERMIND.scr:129
    end -- MASTERMIND.scr:130
    ctx:set("nChances", "nChances - 1") -- MASTERMIND.scr:132
    if ctx:condition("nChances==3") then -- MASTERMIND.scr:133
        ctx:rolloverText("TEXT_THREE", 1, 3000, 2000) -- MASTERMIND.scr:134
    else -- MASTERMIND.scr:135
        if ctx:condition("nChances==2") then -- MASTERMIND.scr:136
            ctx:rolloverText("TEXT_TWO", 1, 3000, 2000) -- MASTERMIND.scr:137
        else -- MASTERMIND.scr:138
            if ctx:condition("nChances==1") then -- MASTERMIND.scr:139
                ctx:rolloverText("TEXT_ONE", 1, 3000, 2000) -- MASTERMIND.scr:140
            else -- MASTERMIND.scr:141
            end -- MASTERMIND.scr:142
        end -- MASTERMIND.scr:143
    end -- MASTERMIND.scr:144
    if ctx:condition("nStoneCount==4") then -- MASTERMIND.scr:146
        mm9.gosub(script, ctx, "Correct") -- MASTERMIND.scr:147
    else -- MASTERMIND.scr:148
        mm9.gosub(script, ctx, "Incorrect") -- MASTERMIND.scr:149
    end -- MASTERMIND.scr:150
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:152
end

script.labels["GenerateColors"] = function(ctx)
    -- MASTERMIND.scr:155
    -- picks random colors for npCorrect
    ctx:state().bNeedsTicket = true -- MASTERMIND.scr:158
    ctx:set("nChances", "NUMCHANCES") -- MASTERMIND.scr:159
    ctx:state().nCounter = 0 -- MASTERMIND.scr:160
    while ctx:condition("nCounter<4") do -- MASTERMIND.scr:162
        ctx:set("LISTINDEX", "LISTFIRST + nCounter") -- MASTERMIND.scr:163
        mm9.gosub(script, ctx, "GetCurrentObject") -- MASTERMIND.scr:164
        ctx:trigger("LISTOBJECT", "off") -- MASTERMIND.scr:165
        ctx:randomInt(0, 4, "nTemp1") -- MASTERMIND.scr:167
        ctx:arrayPut("npCorrect", "nCounter", "nTemp1") -- MASTERMIND.scr:168
        ctx:set("nCounter", "nCounter + 1") -- MASTERMIND.scr:169
    end -- MASTERMIND.scr:170
    ctx:addTrigger("check", "CompareColors") -- MASTERMIND.scr:172
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:174
end

script.labels["Correct"] = function(ctx)
    -- MASTERMIND.scr:177
    ctx:removeTrigger("check") -- MASTERMIND.scr:179
    ctx:playSound("sounds\\spells\\bless.wav", "DoNothing", 1, 5000, "FALSE", 100) -- MASTERMIND.scr:181
    ctx:wait(0, 2, "GenerateColors") -- MASTERMIND.scr:183
    mm9.gosub(script, ctx, "RecordRunesWin") -- MASTERMIND.scr:185
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:187
end

script.labels["Incorrect"] = function(ctx)
    -- MASTERMIND.scr:190
    if ctx:condition("nChances==0") then -- MASTERMIND.scr:192
        ctx:removeTrigger("check") -- MASTERMIND.scr:193
        ctx:rolloverText("TEXT_DEFEAT", 1, 3000, 2000) -- MASTERMIND.scr:194
        mm9.gosub(script, ctx, "GenerateColors") -- MASTERMIND.scr:195
    end -- MASTERMIND.scr:196
    do return ctx:exit("TRUE") end -- MASTERMIND.scr:198
end

return script
