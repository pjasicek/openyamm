-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EFFECTSMGR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 26, path = "BaseGlobals.inc" }

-- EffectsMgr.scr
-- by SJR
-- 10-16-01
-- See also: CinemaMgr.scr
-- Purpose:incorporate letterbox,
-- text, quaking, sound.
-- Must be run by
-- an earthquake object.
-- Triggers:
-- "StartQuake"		= executes all current effects
-- Style Changes
-- "Quake[On\Off]"			= allows\restricts earthquakes
-- --	"Text[On\Off]"			= allows\restricts text display
-- "Box[On\Off]"			= allows\restricts letterbox usage
-- "Quake[Strong\Weak]"	= sets intensity of quake (100%, 50%)
-- "Duration[Long\Short\Instant]"	= sets duration (12, 6, 1 seconds)
script.labels["Main"] = function(ctx)
    -- EFFECTSMGR.scr:43
    ctx:wait(0, 2, "InitEffectsMgr") -- EFFECTSMGR.scr:45
    ctx:cacheSound("sounds\\weapons\\eqhammerpostimpactloop.wav") -- EFFECTSMGR.scr:46
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:47
end

script.labels["InitEffectsMgr"] = function(ctx)
    -- EFFECTSMGR.scr:50
    mm9.gosub(script, ctx, "SetupQuakeObject") -- EFFECTSMGR.scr:52
    mm9.gosub(script, ctx, "SetupAllTriggers") -- EFFECTSMGR.scr:53
    ctx:addTrigger("StartScene", "DoScene") -- EFFECTSMGR.scr:55
    -- turn me on just in case
    ctx:trigger("hMe", "On") -- EFFECTSMGR.scr:61
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:63
end

script.labels["DoScene"] = function(ctx)
    -- EFFECTSMGR.scr:66
    ctx:set("nLoopCount", "nCountHolder") -- EFFECTSMGR.scr:68
    if ctx:condition("bQuakeOn==TRUE") then -- EFFECTSMGR.scr:69
        mm9.gosub(script, ctx, "DoQuake") -- EFFECTSMGR.scr:70
    end -- EFFECTSMGR.scr:71
    if ctx:condition("bBoxOn==TRUE") then -- EFFECTSMGR.scr:72
        mm9.gosub(script, ctx, "DoLetterBox") -- EFFECTSMGR.scr:73
    end -- EFFECTSMGR.scr:74
    if ctx:condition("bTextOn==TRUE") then -- EFFECTSMGR.scr:75
        mm9.gosub(script, ctx, "DoText") -- EFFECTSMGR.scr:76
    end -- EFFECTSMGR.scr:77
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:78
end

script.labels["DoQuake"] = function(ctx)
    -- EFFECTSMGR.scr:81
    -- move eq object to player
    mm9.gosub(script, ctx, "UpdatePOS") -- EFFECTSMGR.scr:84
    -- start rumble loop
    mm9.gosub(script, ctx, "PlaySoundLoop") -- EFFECTSMGR.scr:86
    -- turn quake on
    ctx:trigger("hMe", "trigger") -- EFFECTSMGR.scr:88
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:89
end

script.labels["DoText"] = function(ctx)
    -- EFFECTSMGR.scr:92
    -- put excel text thing here
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:95
end

script.labels["DoLetterBox"] = function(ctx)
    -- EFFECTSMGR.scr:98
    ctx:letterBox("TRUE") -- EFFECTSMGR.scr:100
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:101
end

script.labels["PlaySoundLoop"] = function(ctx)
    -- EFFECTSMGR.scr:104
    -- loop sound according to duration
    if ctx:condition("nLoopCount==0") then -- EFFECTSMGR.scr:107
        mm9.gosub(script, ctx, "EndScene") -- EFFECTSMGR.scr:108
        do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:109
    end -- EFFECTSMGR.scr:110
    ctx:set("nLoopCount", "nLoopCount - 1") -- EFFECTSMGR.scr:111
    ctx:playSound("sounds\\weapons\\eqhammerpostimpactloop.wav", "PlaySoundLoop", 1, 1000, "FALSE", 100) -- EFFECTSMGR.scr:112
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:113
end

script.labels["EndScene"] = function(ctx)
    -- EFFECTSMGR.scr:116
    ctx:letterBox("FALSE") -- EFFECTSMGR.scr:118
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:119
end

script.labels["UpdatePOS"] = function(ctx)
    -- EFFECTSMGR.scr:122
    -- move EQobject to player
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:player():pos() -- EFFECTSMGR.scr:125
    ctx:self():setPos("x", "y", "z") -- EFFECTSMGR.scr:126
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:127
end

script.labels["SetupAllTriggers"] = function(ctx)
    -- EFFECTSMGR.scr:130
    -- setup dedit triggerable options
    ctx:addTrigger("QuakeOn", "TurnQuakeOn") -- EFFECTSMGR.scr:133
    ctx:addTrigger("QuakeOff", "TurnQuakeOff") -- EFFECTSMGR.scr:134
    ctx:addTrigger("TextOn", "TurnTextOn") -- EFFECTSMGR.scr:135
    ctx:addTrigger("TextOff", "TurnTextOff") -- EFFECTSMGR.scr:136
    ctx:addTrigger("BoxOn", "TurnBoxOn") -- EFFECTSMGR.scr:137
    ctx:addTrigger("BoxOff", "TurnBoxOff") -- EFFECTSMGR.scr:138
    ctx:addTrigger("DurationLong", "SetDurationLong") -- EFFECTSMGR.scr:140
    ctx:addTrigger("DurationShort", "SetDurationShort") -- EFFECTSMGR.scr:141
    ctx:addTrigger("DurationInstant", "SetDurationInstant") -- EFFECTSMGR.scr:142
    ctx:addTrigger("QuakeStrong", "SetQuakeHigh") -- EFFECTSMGR.scr:144
    ctx:addTrigger("QuakeWeak", "SetQuakeMed") -- EFFECTSMGR.scr:145
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:147
end

script.labels["SetupQuakeObject"] = function(ctx)
    -- EFFECTSMGR.scr:150
    -- init all the dedit options
    -- if user set 0, eq wont end ever!
    ctx:self():setNumberProperty("DecayRate", 1) -- EFFECTSMGR.scr:154
    -- no damage, effect only
    ctx:self():setNumberProperty("InnerDamage", 0) -- EFFECTSMGR.scr:156
    ctx:self():setNumberProperty("InnerRadius", 1) -- EFFECTSMGR.scr:157
    ctx:self():setNumberProperty("OuterRadius", 500) -- EFFECTSMGR.scr:158
    -- default duration
    ctx:self():setNumberProperty("QuakeDuration", 12) -- EFFECTSMGR.scr:160
    -- max eq is 12
    ctx:self():setNumberProperty("ShakeAmount", 12) -- EFFECTSMGR.scr:162
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:164
end

-- settings
script.labels["TurnQuakeOn"] = function(ctx)
    -- EFFECTSMGR.scr:169
    ctx:state().bQuakeOn = true -- EFFECTSMGR.scr:170
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:171
end

script.labels["TurnQuakeOff"] = function(ctx)
    -- EFFECTSMGR.scr:172
    ctx:state().bQuakeOn = false -- EFFECTSMGR.scr:173
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:174
end

script.labels["TurnTextOn"] = function(ctx)
    -- EFFECTSMGR.scr:175
    ctx:state().bTextOn = true -- EFFECTSMGR.scr:176
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:177
end

script.labels["TurnTextOff"] = function(ctx)
    -- EFFECTSMGR.scr:178
    ctx:state().bTextOn = false -- EFFECTSMGR.scr:179
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:180
end

script.labels["TurnBoxOn"] = function(ctx)
    -- EFFECTSMGR.scr:181
    ctx:state().bBoxOn = true -- EFFECTSMGR.scr:182
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:183
end

script.labels["TurnBoxOff"] = function(ctx)
    -- EFFECTSMGR.scr:184
    ctx:state().bBoxOn = false -- EFFECTSMGR.scr:185
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:186
end

script.labels["SetDurationLong"] = function(ctx)
    -- EFFECTSMGR.scr:188
    ctx:self():setNumberProperty("QuakeDuration", 12) -- EFFECTSMGR.scr:189
    ctx:state().nCountHolder = 4 -- EFFECTSMGR.scr:190
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:191
end

script.labels["SetDurationShort"] = function(ctx)
    -- EFFECTSMGR.scr:192
    ctx:self():setNumberProperty("QuakeDuration", 6) -- EFFECTSMGR.scr:193
    ctx:state().nCountHolder = 2 -- EFFECTSMGR.scr:194
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:195
end

script.labels["SetDurationInstant"] = function(ctx)
    -- EFFECTSMGR.scr:196
    ctx:self():setNumberProperty("QuakeDuration", 1) -- EFFECTSMGR.scr:197
    ctx:state().nCountHolder = 0 -- EFFECTSMGR.scr:198
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:199
end

script.labels["SetQuakeHigh"] = function(ctx)
    -- EFFECTSMGR.scr:201
    ctx:self():setNumberProperty("ShakeAmount", 12) -- EFFECTSMGR.scr:202
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:203
end

script.labels["SetQuakeMed"] = function(ctx)
    -- EFFECTSMGR.scr:204
    ctx:self():setNumberProperty("ShakeAmount", 6) -- EFFECTSMGR.scr:205
    do return ctx:exit("TRUE") end -- EFFECTSMGR.scr:206
end

return script
