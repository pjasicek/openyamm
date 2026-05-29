-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BUTTONPUZZLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 29, path = "Flags.inc" }

-- ButtonPuzzle.scr
-- Brett Yagi/Ed Campos/Karl Drown
-- 11/16/2001
-- Script controls the triggering of each individual
-- Button that is apart of a 16 piece Puzzle it also
-- insures only certain Buttons Are Triggered
-- edited by Bones 03/27/03
-- TELP Patch 1.3 -- added warning for turn-based mode
-- -DEDIT NOTES-
-- ScriptParams are:
-- p0 = The Base Rootname of all the Puzzle Doors
-- p1 = The Name of the ButtonPad Trigger Object
-- p2 = The Variable that sets the direction of which the
script.labels["puzzle is setup and of the position of puzzle's"] = function(ctx)
    -- BUTTONPUZZLE.scr:20
end

-- completions (Is set only for vertical use)
-- p3 = Movement for initial Puzzle Door setup
-- p4 = Movement for Puzzle Door movement at puzzle completion
-- p5 = Speed of which Puzzle door will move on completion
-- To match corresponding sound effect
script.labels["DoNothing"] = function(ctx)
    -- BUTTONPUZZLE.scr:48
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:51
end

script.labels["TriggerTrap"] = function(ctx)
    -- BUTTONPUZZLE.scr:54
    ctx:self():moveDir(0, "nMoveDir2", 0, "nMoveDistA", 300, "DoNothing") -- BUTTONPUZZLE.scr:57
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:59
end

script.labels["TriggerMe"] = function(ctx)
    -- BUTTONPUZZLE.scr:62
    ctx:state().nTrig = 1 -- BUTTONPUZZLE.scr:65
    ctx:state().hHandle = ctx:self() -- BUTTONPUZZLE.scr:66
    ctx:trigger("hHandle", "Use") -- BUTTONPUZZLE.scr:67
    ctx:trigger("hHandle", "lock") -- BUTTONPUZZLE.scr:68
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:70
end

script.labels["UseMe"] = function(ctx)
    -- BUTTONPUZZLE.scr:73
    if ctx:condition("nTrig == 0") then -- BUTTONPUZZLE.scr:76
        ctx:getConsoleNumVar("LockButtons", "nLockButtons") -- BUTTONPUZZLE.scr:77
        if ctx:condition("nLockButtons == 0") then -- BUTTONPUZZLE.scr:78
            ctx:object("sButtonPad"):trigger("sButtonName") -- BUTTONPUZZLE.scr:79-80
        end -- BUTTONPUZZLE.scr:81
    else -- BUTTONPUZZLE.scr:82
        ctx:state().nTrig = 0 -- BUTTONPUZZLE.scr:83
    end -- BUTTONPUZZLE.scr:84
    do return ctx:exit(0) end -- BUTTONPUZZLE.scr:86
end

script.labels["UseStart"] = function(ctx)
    -- BUTTONPUZZLE.scr:89
    ctx:addTrigger("Use", "UseMe") -- BUTTONPUZZLE.scr:92
    ctx:state().hHandle = ctx:self() -- BUTTONPUZZLE.scr:93
    ctx:trigger("hHandle", "Unlock") -- BUTTONPUZZLE.scr:94
    ctx:trigger("hHandle", "Use") -- BUTTONPUZZLE.scr:95
    ctx:trigger("hHandle", "lock") -- BUTTONPUZZLE.scr:96
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:98
end

script.labels["MoveDoor"] = function(ctx)
    -- BUTTONPUZZLE.scr:100
    ctx:self():stop() -- BUTTONPUZZLE.scr:103
    ctx:removeTrigger("Use") -- BUTTONPUZZLE.scr:104
    ctx:trigger("hMe", "Lock") -- BUTTONPUZZLE.scr:105
    ctx:playSound("sounds\\Door\\doorlatch02.wav", "DoNothing", 0, 1000, 0, 70) -- BUTTONPUZZLE.scr:107
    ctx:wait(0, .8, "EndDoor") -- BUTTONPUZZLE.scr:108
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:110
end

script.labels["EndDoor"] = function(ctx)
    -- BUTTONPUZZLE.scr:113
    ctx:playSound("sounds\\Door\\stonedoorslide02.wav", "DoNothing", 0, 1000, 0, 70) -- BUTTONPUZZLE.scr:116
    ctx:self():moveDir(0, "nMoveDir", 0, "nMoveDistB", "nMoveSpeed", "EndScript") -- BUTTONPUZZLE.scr:117
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:119
end

script.labels["EndScript"] = function(ctx)
    -- BUTTONPUZZLE.scr:122
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:125
end

script.labels["Main2"] = function(ctx)
    -- BUTTONPUZZLE.scr:128
    ctx:set("nMoveDir2", "nMoveDir - 2") -- BUTTONPUZZLE.scr:131
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- BUTTONPUZZLE.scr:133
    ctx:self():moveDir(0, "nMoveDir", 0, "nMoveDistA", 0, "DoNothing") -- BUTTONPUZZLE.scr:134
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:136
end

script.labels["Main"] = function(ctx)
    -- BUTTONPUZZLE.scr:139
    -- TraceOn
    ctx:getParam(0, "sButtonName") -- BUTTONPUZZLE.scr:144
    ctx:getParam(1, "sButtonPad") -- BUTTONPUZZLE.scr:145
    ctx:getParam(2, "nMoveDir") -- BUTTONPUZZLE.scr:146
    ctx:getParam(3, "nMoveDistA") -- BUTTONPUZZLE.scr:147
    ctx:getParam(4, "nMoveDistB") -- BUTTONPUZZLE.scr:148
    ctx:getParam(5, "nMoveSpeed") -- BUTTONPUZZLE.scr:149
    ctx:addTrigger("TriggerMe", "TriggerMe") -- BUTTONPUZZLE.scr:152
    ctx:addTrigger("MoveDoor", "MoveDoor") -- BUTTONPUZZLE.scr:153
    ctx:addTrigger("TriggerTrap", "TriggerTrap") -- BUTTONPUZZLE.scr:154
    ctx:addTrigger("UseStart", "UseStart") -- BUTTONPUZZLE.scr:155
    mm9.gosub(script, ctx, "Main2") -- BUTTONPUZZLE.scr:156
    do return ctx:exit(1) end -- BUTTONPUZZLE.scr:158
end

script.labels["UseMe"] = function(ctx)
    -- BUTTONPUZZLE.scr:161
    -- Bones
    -- overloaded
    if ctx:condition("nTrig == 0") then -- BUTTONPUZZLE.scr:166
        ctx:isTurnBased("nTrig") -- BUTTONPUZZLE.scr:167
        if ctx:condition("nTrig == 1") then -- BUTTONPUZZLE.scr:168
            ctx:state().nTrig = 0 -- BUTTONPUZZLE.scr:169
            ctx:rolloverText(19, 0) -- BUTTONPUZZLE.scr:170
            ctx:wait(30, 1, "UseMe") -- BUTTONPUZZLE.scr:171
            do return ctx:exit("") end -- BUTTONPUZZLE.scr:172
        else -- BUTTONPUZZLE.scr:173
            ctx:state().nTrig = 0 -- BUTTONPUZZLE.scr:174
        end -- BUTTONPUZZLE.scr:175
    else -- BUTTONPUZZLE.scr:177
        ctx:isTurnBased("nTrig") -- BUTTONPUZZLE.scr:178
        if ctx:condition("nTrig == 1") then -- BUTTONPUZZLE.scr:179
            ctx:state().nTrig = 1 -- BUTTONPUZZLE.scr:180
            ctx:rolloverText(19, 0) -- BUTTONPUZZLE.scr:181
            ctx:wait(30, 1, "UseMe") -- BUTTONPUZZLE.scr:182
            do return ctx:exit("") end -- BUTTONPUZZLE.scr:183
        else -- BUTTONPUZZLE.scr:184
            ctx:state().nTrig = 1 -- BUTTONPUZZLE.scr:185
        end -- BUTTONPUZZLE.scr:186
    end -- BUTTONPUZZLE.scr:187
    do return mm9.gotoLabel(script, ctx, "UseMe") end -- BUTTONPUZZLE.scr:189
end

return script
