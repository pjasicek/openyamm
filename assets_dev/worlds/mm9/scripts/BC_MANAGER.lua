-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BC_MANAGER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- BC_MonsterFight.scr
-- by SJR
-- Purpose:two monsters duke it out
-- to show the player a fight
script.labels["Main"] = function(ctx)
    -- BC_MANAGER.scr:37
    ctx:getParam(0, "sSpawnLoc0") -- BC_MANAGER.scr:39
    ctx:getParam(1, "sSpawnLoc1") -- BC_MANAGER.scr:40
    ctx:getParam(2, "sSpawnLoc2") -- BC_MANAGER.scr:41
    ctx:onEvent("OnPostStartWorld", "InitMonsterFight") -- BC_MANAGER.scr:43
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- BC_MANAGER.scr:44
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:46
end

script.labels["CacheFiles"] = function(ctx)
    -- BC_MANAGER.scr:49
    ctx:cacheScript("BC_MonsterFight.scr") -- BC_MANAGER.scr:51
    ctx:cacheScript("BC_MonsterOpen.scr") -- BC_MANAGER.scr:52
    ctx:cacheScript("EvilSorcerer.scr") -- BC_MANAGER.scr:53
    ctx:cacheScript("flyrange.scr") -- BC_MANAGER.scr:54
    ctx:cacheClientFx("SPELL_MIST") -- BC_MANAGER.scr:56
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:58
end

script.labels["InitMonsterFight"] = function(ctx)
    -- BC_MANAGER.scr:61
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:63
    ctx:addTrigger("open", "StartOpen") -- BC_MANAGER.scr:64
    ctx:onEvent("OnObjectLinkBroken", "OnObjectLinkBroken") -- BC_MANAGER.scr:66
    ctx:state().x0, ctx:state().y0, ctx:state().z0 = ctx:object("sSpawnLoc0"):pos() -- BC_MANAGER.scr:68-69
    ctx:state().x1, ctx:state().y1, ctx:state().z1 = ctx:object("sSpawnLoc1"):pos() -- BC_MANAGER.scr:70-71
    ctx:state().x2, ctx:state().y2, ctx:state().z2 = ctx:object("sSpawnLoc2"):pos() -- BC_MANAGER.scr:72-73
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:75
end

script.labels["StartFight"] = function(ctx)
    -- BC_MANAGER.scr:78
    ctx:removeTrigger("fight") -- BC_MANAGER.scr:80
    ctx:state().hSpawn0 = ctx:spawn("x0", "y0", "z0", "SPAWN_PARAM_0") -- BC_MANAGER.scr:82
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:83
        ctx:object("hSpawn0"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- BC_MANAGER.scr:84
        ctx:self():link(ctx:object("hSpawn0")) -- BC_MANAGER.scr:85
    end -- BC_MANAGER.scr:86
    ctx:state().hSpawn1 = ctx:spawn("x1", "y1", "z1", "SPAWN_PARAM_1") -- BC_MANAGER.scr:88
    if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:89
        ctx:object("hSpawn1"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- BC_MANAGER.scr:90
        ctx:self():link(ctx:object("hSpawn1")) -- BC_MANAGER.scr:91
    end -- BC_MANAGER.scr:92
    ctx:wait(0, 120, "ForceEndFight") -- BC_MANAGER.scr:94
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:96
end

script.labels["StartOpen"] = function(ctx)
    -- BC_MANAGER.scr:99
    ctx:removeTrigger("open") -- BC_MANAGER.scr:101
    ctx:state().hOpener = ctx:spawn("x2", "y2", "z2", "SPAWN_PARAM_2") -- BC_MANAGER.scr:103
    if ctx:condition("hOpener!=0") then -- BC_MANAGER.scr:104
        ctx:object("hOpener"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- BC_MANAGER.scr:105
        ctx:self():link(ctx:object("hOpener")) -- BC_MANAGER.scr:106
    end -- BC_MANAGER.scr:107
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:109
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- BC_MANAGER.scr:112
    ctx:getParam(0, "hLink") -- BC_MANAGER.scr:114
    if ctx:condition("hLink==hSpawn0") then -- BC_MANAGER.scr:116
        ctx:state().hSpawn0 = nil -- BC_MANAGER.scr:117
        if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:118
            ctx:object("hSpawn1"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- BC_MANAGER.scr:119
            ctx:wait(1, 2, "RemoveCreature") -- BC_MANAGER.scr:120
        end -- BC_MANAGER.scr:121
    else -- BC_MANAGER.scr:122
        if ctx:condition("hLink==hSpawn1") then -- BC_MANAGER.scr:123
            ctx:state().hSpawn1 = nil -- BC_MANAGER.scr:124
            if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:125
                ctx:object("hSpawn0"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- BC_MANAGER.scr:126
                ctx:wait(2, 2, "RemoveCreature") -- BC_MANAGER.scr:127
            end -- BC_MANAGER.scr:128
        else -- BC_MANAGER.scr:129
            if ctx:condition("hLink==hOpener") then -- BC_MANAGER.scr:130
                ctx:state().hOpener = nil -- BC_MANAGER.scr:131
                ctx:addTrigger("open", "StartOpen") -- BC_MANAGER.scr:132
            end -- BC_MANAGER.scr:133
        end -- BC_MANAGER.scr:134
    end -- BC_MANAGER.scr:135
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:137
end

script.labels["RemoveCreature"] = function(ctx)
    -- BC_MANAGER.scr:140
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:142
        ctx:object("hSpawn0"):remove() -- BC_MANAGER.scr:143
        ctx:state().hSpawn0 = nil -- BC_MANAGER.scr:144
    else -- BC_MANAGER.scr:145
        if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:146
            ctx:object("hSpawn1"):remove() -- BC_MANAGER.scr:147
            ctx:state().hSpawn1 = nil -- BC_MANAGER.scr:148
        end -- BC_MANAGER.scr:149
    end -- BC_MANAGER.scr:150
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:152
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:154
end

script.labels["ForceEndFight"] = function(ctx)
    -- BC_MANAGER.scr:157
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:159
        ctx:object("hSpawn0"):remove() -- BC_MANAGER.scr:160
        ctx:state().hSpawn0 = nil -- BC_MANAGER.scr:161
    end -- BC_MANAGER.scr:162
    if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:164
        ctx:object("hSpawn1"):remove() -- BC_MANAGER.scr:165
        ctx:state().hSpawn1 = nil -- BC_MANAGER.scr:166
    end -- BC_MANAGER.scr:167
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:169
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:171
end

return script
