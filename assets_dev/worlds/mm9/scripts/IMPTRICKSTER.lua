-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IMPTRICKSTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 16, path = "flags.inc" }

-- ImpTrickster.scr
-- by SJR
-- 10-12-01
-- Purpose:bathhouse imp will run away,
-- call buddies, generally be
-- a punk.
-- Triggers:
-- "Phase1" =  starts the first part
-- "Phase2" =  starts the second part
script.labels["Main"] = function(ctx)
    -- IMPTRICKSTER.scr:35
    ctx:getParam(0, "LISTNAME") -- IMPTRICKSTER.scr:37
    ctx:getParam(1, "LISTFIRST") -- IMPTRICKSTER.scr:38
    ctx:getParam(2, "LISTLAST") -- IMPTRICKSTER.scr:39
    mm9.gosub(script, ctx, "SetTraverseRun") -- IMPTRICKSTER.scr:41
    mm9.gosub(script, ctx, "SetTraverseOnce") -- IMPTRICKSTER.scr:42
    ctx:state().TRAVERSERADIUS = 25 -- IMPTRICKSTER.scr:43
    ctx:onEvent("OnPostStartWorld", "InitImpTrickster") -- IMPTRICKSTER.scr:45
    ctx:wait(0, 5, "InitImpTrickster") -- IMPTRICKSTER.scr:46
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:48
end

script.labels["InitImpTrickster"] = function(ctx)
    -- IMPTRICKSTER.scr:51
    ctx:addTrigger("Phase1", "OpeningRoom") -- IMPTRICKSTER.scr:53
    ctx:addTrigger("Phase2", "FloodRoom") -- IMPTRICKSTER.scr:54
    ctx:onEvent("OnStuck", "TraverseResume") -- IMPTRICKSTER.scr:55
    ctx:onEvent("OnDamage", "PreemtScene") -- IMPTRICKSTER.scr:56
    ctx:onEvent("OnDeath", "DisableScene") -- IMPTRICKSTER.scr:57
    ctx:addTrigger("reappear", "Reappear") -- IMPTRICKSTER.scr:59
    ctx:addTrigger("disappear", "Disappear") -- IMPTRICKSTER.scr:60
    ctx:state().hTrigger = ctx:objectOrNil("TriggerFrontImp") -- IMPTRICKSTER.scr:63
    ctx:state().hHenchman1 = ctx:objectOrNil("sColloidal1Name") -- IMPTRICKSTER.scr:64
    ctx:state().hHenchman2 = ctx:objectOrNil("sColloidal2Name") -- IMPTRICKSTER.scr:65
    mm9.gosub(script, ctx, "BaseWanderInit") -- IMPTRICKSTER.scr:67
    mm9.gosub(script, ctx, "BaseWanderStartup") -- IMPTRICKSTER.scr:68
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:70
end

script.labels["PreemtScene"] = function(ctx)
    -- IMPTRICKSTER.scr:73
    ctx:onEvent("OnDamage", "DoNothing") -- IMPTRICKSTER.scr:75
    ctx:trigger("hTrigger", "trigger") -- IMPTRICKSTER.scr:76
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:78
end

script.labels["DisableScene"] = function(ctx)
    -- IMPTRICKSTER.scr:81
    ctx:onEvent("OnDeath", "DoNothing") -- IMPTRICKSTER.scr:83
    ctx:trigger("hTrigger", "off") -- IMPTRICKSTER.scr:84
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:86
end

script.labels["OnTraverseDone"] = function(ctx)
    -- IMPTRICKSTER.scr:89
    if ctx:condition("LISTINDEX==0") then -- IMPTRICKSTER.scr:91
        ctx:set("hTrigger", "LISTOBJECT") -- IMPTRICKSTER.scr:92
        mm9.gosub(script, ctx, "TraversePause") -- IMPTRICKSTER.scr:93
        ctx:setCallback(0, "EndOpeningRoom") -- IMPTRICKSTER.scr:94
        mm9.gosub(script, ctx, "AlertHenchman1") -- IMPTRICKSTER.scr:95
        do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:96
    end -- IMPTRICKSTER.scr:97
    if ctx:condition("LISTINDEX==5") then -- IMPTRICKSTER.scr:98
        mm9.gosub(script, ctx, "TraversePause") -- IMPTRICKSTER.scr:99
        ctx:killCallback(0) -- IMPTRICKSTER.scr:100
        ctx:setCallback(0, "TraverseResume") -- IMPTRICKSTER.scr:101
        mm9.gosub(script, ctx, "AlertHenchman1") -- IMPTRICKSTER.scr:102
        do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:103
    end -- IMPTRICKSTER.scr:104
    if ctx:condition("LISTINDEX==7") then -- IMPTRICKSTER.scr:105
        mm9.gosub(script, ctx, "TraversePause") -- IMPTRICKSTER.scr:106
        mm9.gosub(script, ctx, "EscapeEnd") -- IMPTRICKSTER.scr:107
    end -- IMPTRICKSTER.scr:108
    ctx:playSound("sounds\\AnimSounds\\DragonflyHattackair1.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:109
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:110
end

script.labels["OpeningRoom"] = function(ctx)
    -- IMPTRICKSTER.scr:113
    mm9.gosub(script, ctx, "BaseWanderStop") -- IMPTRICKSTER.scr:115
    ctx:self():playAnimation("HAttack1", "DoNothing") -- IMPTRICKSTER.scr:116
    ctx:playSound("sounds\\AnimSounds\\DragonflyHattackair1.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:117
    ctx:state().g_hTarget = ctx:player() -- IMPTRICKSTER.scr:118
    ctx:self():faceObject(ctx:player(), 360, "TraverseBegin") -- IMPTRICKSTER.scr:119
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:120
end

script.labels["EndOpeningRoom"] = function(ctx)
    -- IMPTRICKSTER.scr:123
    ctx:object("hTrigger"):doClientFx("SPELL_ELEMBLAST", 0, 1) -- IMPTRICKSTER.scr:125
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("LISTOBJECT"):pos() -- IMPTRICKSTER.scr:126
    ctx:playSound("sounds\\magic\\protectionfrommagic.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:127
    ctx:self():setPos("x", "y", "z") -- IMPTRICKSTER.scr:128
    -- gosub Disappear
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:130
end

script.labels["FloodRoom"] = function(ctx)
    -- IMPTRICKSTER.scr:133
    ctx:state().hHenchman1 = ctx:objectOrNil("sColloidal3Name") -- IMPTRICKSTER.scr:135
    ctx:state().hHenchman2 = ctx:objectOrNil("sColloidal4Name") -- IMPTRICKSTER.scr:136
    mm9.gosub(script, ctx, "TraverseResume") -- IMPTRICKSTER.scr:137
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:138
end

script.labels["EscapeEnd"] = function(ctx)
    -- IMPTRICKSTER.scr:141
    ctx:self():stop() -- IMPTRICKSTER.scr:143
    mm9.gosub(script, ctx, "BaseInit") -- IMPTRICKSTER.scr:145
    mm9.gosub(script, ctx, "SetupTarget") -- IMPTRICKSTER.scr:146
    mm9.gosub(script, ctx, "AggressiveStart") -- IMPTRICKSTER.scr:147
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:148
end

script.labels["AlertHenchman1"] = function(ctx)
    -- IMPTRICKSTER.scr:151
    ctx:self():faceObject(ctx:object("hHenchman1"), 360, "DoTaunt") -- IMPTRICKSTER.scr:153
    ctx:playSound("sounds\\AnimSounds\\DragonflyHattackair1.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:154
    ctx:trigger("hHenchman1", "Help") -- IMPTRICKSTER.scr:155
    ctx:wait(0, 1, "AlertHenchman2") -- IMPTRICKSTER.scr:156
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:157
end

script.labels["AlertHenchman2"] = function(ctx)
    -- IMPTRICKSTER.scr:160
    ctx:self():faceObject(ctx:object("hHenchman2"), 360, "DoTaunt") -- IMPTRICKSTER.scr:162
    ctx:playSound("sounds\\AnimSounds\\DragonflyHattackair1.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:163
    ctx:trigger("hHenchman2", "Help") -- IMPTRICKSTER.scr:164
    ctx:wait(0, 2, "EndPhase") -- IMPTRICKSTER.scr:165
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:166
end

script.labels["DoTaunt"] = function(ctx)
    -- IMPTRICKSTER.scr:169
    ctx:playSound("sounds\\AnimSounds\\DragonflyHattackair1.wav", "DoNothing", 1, 5000, "FALSE", 100) -- IMPTRICKSTER.scr:171
    ctx:self():playAnimation("HAttack1") -- IMPTRICKSTER.scr:172
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:173
end

script.labels["EndPhase"] = function(ctx)
    -- IMPTRICKSTER.scr:176
    ctx:doCallback(0) -- IMPTRICKSTER.scr:178
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:179
end

script.labels["Disappear"] = function(ctx)
    -- IMPTRICKSTER.scr:182
    ctx:self():setFlag("FLAG_SOLID", false) -- IMPTRICKSTER.scr:184
    ctx:self():setFlag("FLAG_VISIBLE", false) -- IMPTRICKSTER.scr:185
    ctx:self():setNumberProperty("CanDamage", "FALSE") -- IMPTRICKSTER.scr:186
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:188
end

script.labels["Reappear"] = function(ctx)
    -- IMPTRICKSTER.scr:191
    ctx:self():setFlag("FLAG_SOLID", true) -- IMPTRICKSTER.scr:193
    ctx:self():setFlag("FLAG_VISIBLE", true) -- IMPTRICKSTER.scr:194
    ctx:self():setNumberProperty("CanDamage", "TRUE") -- IMPTRICKSTER.scr:195
    do return ctx:exit("TRUE") end -- IMPTRICKSTER.scr:197
end

return script
