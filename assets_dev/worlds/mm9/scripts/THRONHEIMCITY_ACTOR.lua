-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THRONHEIMCITY_ACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "NPCBase.Inc" }

-- ThronHeimCity_Actor.scr
-- Jeff Leggett
-- 12/18/2001
-- Handles:
-- Various NPCs.
script.labels["RunNormalScript"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:18
    ctx:self():stop() -- THRONHEIMCITY_ACTOR.scr:20
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_FORWARD") -- THRONHEIMCITY_ACTOR.scr:22
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- THRONHEIMCITY_ACTOR.scr:23
    ctx:runScript("g_sTemp") -- THRONHEIMCITY_ACTOR.scr:24
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:26
end

script.labels["ShmoeDamage"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:29
    ctx:self():die() -- THRONHEIMCITY_ACTOR.scr:31
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:self():rotation() -- THRONHEIMCITY_ACTOR.scr:33
    ctx:state().g_dirX, ctx:state().g_dirY, ctx:state().g_dirZ = ctx:vecScale("g_dirX", "g_dirY", "g_dirZ", -1) -- THRONHEIMCITY_ACTOR.scr:34
    ctx:set("g_dirY", 0.45) -- THRONHEIMCITY_ACTOR.scr:35
    ctx:self():setPushBack("g_dirX", "g_dirY", "g_dirZ", 1) -- THRONHEIMCITY_ACTOR.scr:36
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_ACTOR.scr:38
end

script.labels["OnHereComesBadAssShmoe"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:41
    mm9.gosub(script, ctx, "DisableWandering") -- THRONHEIMCITY_ACTOR.scr:43
    mm9.gosub(script, ctx, "DisableChat") -- THRONHEIMCITY_ACTOR.scr:44
    ctx:self():stop() -- THRONHEIMCITY_ACTOR.scr:45
    ctx:getParam(0, "g_hObject") -- THRONHEIMCITY_ACTOR.scr:47
    ctx:self():setTarget(ctx:object("g_hObject")) -- THRONHEIMCITY_ACTOR.scr:48
    -- SetStat g_hMyObject,WalkRunMode,WALKRUNMODE_TARGET
    -- GetFaceDir g_hObject,g_dirX,g_dirY,g_dirZ
    -- Walk g_dirX,g_dirY,g_dirZ
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:55
end

script.labels["SetupShmoe"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:58
    mm9.gosub(script, ctx, "NPCBaseInit") -- THRONHEIMCITY_ACTOR.scr:60
    ctx:state().g_bSocializeEnabled = false -- THRONHEIMCITY_ACTOR.scr:62
    ctx:addTrigger("HereComesBadAss", "OnHereComesBadAssShmoe") -- THRONHEIMCITY_ACTOR.scr:64
    ctx:onEvent("OnDamage", "ShmoeDamage") -- THRONHEIMCITY_ACTOR.scr:65
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:67
end

script.labels["BenDamage"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:70
    ctx:self():die() -- THRONHEIMCITY_ACTOR.scr:72
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_ACTOR.scr:73
end

script.labels["YellForHelp"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:76
    ctx:self():help(ctx:object("g_hTarget")) -- THRONHEIMCITY_ACTOR.scr:78
    ctx:wait(0, 1, "YellForHelp") -- THRONHEIMCITY_ACTOR.scr:79
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:81
end

script.labels["BenAtGuard"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:85
    ctx:self():stop() -- THRONHEIMCITY_ACTOR.scr:87
    mm9.gosub(script, ctx, "YellForHelp") -- THRONHEIMCITY_ACTOR.scr:88
    ctx:wait(0, 0, "DoNothing") -- THRONHEIMCITY_ACTOR.scr:89
    mm9.gosub(script, ctx, "RunNormalScript") -- THRONHEIMCITY_ACTOR.scr:90
    do return ctx:exit("TRUE") end -- THRONHEIMCITY_ACTOR.scr:92
end

script.labels["RunAwayFromBadAss"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:95
    ctx:state().g_hObject = ctx:objectOrNil("BadAss") -- THRONHEIMCITY_ACTOR.scr:98
    if ctx:condition("g_hObject==NULL") then -- THRONHEIMCITY_ACTOR.scr:100
        do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:101
    end -- THRONHEIMCITY_ACTOR.scr:102
    ctx:set("g_hRunAwayTrigger", "g_hObject") -- THRONHEIMCITY_ACTOR.scr:104
    ctx:set("g_hTarget", "g_hObject") -- THRONHEIMCITY_ACTOR.scr:105
    ctx:state().g_hObject = ctx:objectOrNil("Guard1") -- THRONHEIMCITY_ACTOR.scr:107
    ctx:self():setTarget(ctx:object("g_hTarget")) -- THRONHEIMCITY_ACTOR.scr:109
    ctx:self():runTo(ctx:object("g_hObject"), 0, "BenAtGuard") -- THRONHEIMCITY_ACTOR.scr:111
    ctx:wait(0, 1, "YellForHelp") -- THRONHEIMCITY_ACTOR.scr:112
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:114
end

script.labels["BenAtMarker"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:117
    ctx:self():stop() -- THRONHEIMCITY_ACTOR.scr:119
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_FORWARD") -- THRONHEIMCITY_ACTOR.scr:121
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:123
end

script.labels["OnHereComesBadAssBen"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:126
    mm9.gosub(script, ctx, "DisableWandering") -- THRONHEIMCITY_ACTOR.scr:129
    mm9.gosub(script, ctx, "DisableChat") -- THRONHEIMCITY_ACTOR.scr:130
    ctx:self():stop() -- THRONHEIMCITY_ACTOR.scr:132
    ctx:getParam(0, "g_hObject") -- THRONHEIMCITY_ACTOR.scr:134
    ctx:self():setTarget(ctx:object("g_hObject")) -- THRONHEIMCITY_ACTOR.scr:135
    ctx:self():setStat("WalkRunMode", "WALKRUNMODE_TARGET") -- THRONHEIMCITY_ACTOR.scr:137
    ctx:state().g_hObject = ctx:objectOrNil("BenMarker") -- THRONHEIMCITY_ACTOR.scr:139
    ctx:self():runTo(ctx:object("g_hObject"), 0, "BenAtMarker") -- THRONHEIMCITY_ACTOR.scr:141
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:144
end

script.labels["SetupBen"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:147
    mm9.gosub(script, ctx, "NPCBaseInit") -- THRONHEIMCITY_ACTOR.scr:150
    ctx:removeTrigger("RunAwayFromMe") -- THRONHEIMCITY_ACTOR.scr:152
    ctx:addTrigger("RunAwayFromMe", "RunAwayFromBadAss") -- THRONHEIMCITY_ACTOR.scr:153
    ctx:addTrigger("HereComesBadAss", "OnHereComesBadAssBen") -- THRONHEIMCITY_ACTOR.scr:154
    ctx:state().g_bSocializeEnabled = false -- THRONHEIMCITY_ACTOR.scr:156
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:158
end

script.labels["Main"] = function(ctx)
    -- THRONHEIMCITY_ACTOR.scr:162
    ctx:state().sMyName = ctx:self():name() -- THRONHEIMCITY_ACTOR.scr:166
    if ctx:condition("sMyName==Shmoe") then -- THRONHEIMCITY_ACTOR.scr:168
        do return mm9.gotoLabel(script, ctx, "SetupShmoe") end -- THRONHEIMCITY_ACTOR.scr:169
    end -- THRONHEIMCITY_ACTOR.scr:170
    if ctx:condition("sMyName==Ben") then -- THRONHEIMCITY_ACTOR.scr:172
        do return mm9.gotoLabel(script, ctx, "SetupBen") end -- THRONHEIMCITY_ACTOR.scr:173
    end -- THRONHEIMCITY_ACTOR.scr:174
    -- If we're here, then we are a NPC that needs to
    do return ctx:exit("") end -- THRONHEIMCITY_ACTOR.scr:180
end

return script
