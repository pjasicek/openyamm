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
    ctx:command("onpoststartworld", "InitMonsterFight") -- BC_MANAGER.scr:43
    ctx:command("oncachefiles", "CacheFiles") -- BC_MANAGER.scr:44
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:46
end

script.labels["CacheFiles"] = function(ctx)
    -- BC_MANAGER.scr:49
    ctx:command("cachescript", "\"BC_MonsterFight.scr\"") -- BC_MANAGER.scr:51
    ctx:command("cachescript", "\"BC_MonsterOpen.scr\"") -- BC_MANAGER.scr:52
    ctx:command("cachescript", "\"EvilSorcerer.scr\"") -- BC_MANAGER.scr:53
    ctx:command("cachescript", "\"flyrange.scr\"") -- BC_MANAGER.scr:54
    ctx:command("cacheclientfx", "SPELL_MIST") -- BC_MANAGER.scr:56
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:58
end

script.labels["InitMonsterFight"] = function(ctx)
    -- BC_MANAGER.scr:61
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:63
    ctx:addTrigger("open", "StartOpen") -- BC_MANAGER.scr:64
    ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- BC_MANAGER.scr:66
    ctx:command("getobjecthandle", "sSpawnLoc0, hLocation") -- BC_MANAGER.scr:68
    ctx:command("getpos", "hLocation, x0,y0,z0") -- BC_MANAGER.scr:69
    ctx:command("getobjecthandle", "sSpawnLoc1, hLocation") -- BC_MANAGER.scr:70
    ctx:command("getpos", "hLocation, x1,y1,z1") -- BC_MANAGER.scr:71
    ctx:command("getobjecthandle", "sSpawnLoc2, hLocation") -- BC_MANAGER.scr:72
    ctx:command("getpos", "hLocation, x2,y2,z2") -- BC_MANAGER.scr:73
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:75
end

script.labels["StartFight"] = function(ctx)
    -- BC_MANAGER.scr:78
    ctx:command("removetrigger", "fight") -- BC_MANAGER.scr:80
    ctx:command("spawn", "hSpawn0, x0,y0,z0, SPAWN_PARAM_0") -- BC_MANAGER.scr:82
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:83
        ctx:command("doclientfx", "hSpawn0, SPELL_MIST, FALSE, TRUE") -- BC_MANAGER.scr:84
        ctx:command("createobjectlink", "hSpawn0") -- BC_MANAGER.scr:85
    end -- BC_MANAGER.scr:86
    ctx:command("spawn", "hSpawn1, x1,y1,z1, SPAWN_PARAM_1") -- BC_MANAGER.scr:88
    if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:89
        ctx:command("doclientfx", "hSpawn1, SPELL_MIST, FALSE, TRUE") -- BC_MANAGER.scr:90
        ctx:command("createobjectlink", "hSpawn1") -- BC_MANAGER.scr:91
    end -- BC_MANAGER.scr:92
    ctx:command("wait", "0, 120, ForceEndFight") -- BC_MANAGER.scr:94
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:96
end

script.labels["StartOpen"] = function(ctx)
    -- BC_MANAGER.scr:99
    ctx:command("removetrigger", "open") -- BC_MANAGER.scr:101
    ctx:command("spawn", "hOpener, x2,y2,z2, SPAWN_PARAM_2") -- BC_MANAGER.scr:103
    if ctx:condition("hOpener!=0") then -- BC_MANAGER.scr:104
        ctx:command("doclientfx", "hOpener, SPELL_MIST, FALSE, TRUE") -- BC_MANAGER.scr:105
        ctx:command("createobjectlink", "hOpener") -- BC_MANAGER.scr:106
    end -- BC_MANAGER.scr:107
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:109
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- BC_MANAGER.scr:112
    ctx:getParam(0, "hLink") -- BC_MANAGER.scr:114
    if ctx:condition("hLink==hSpawn0") then -- BC_MANAGER.scr:116
        ctx:command("hspawn0", "= NULL") -- BC_MANAGER.scr:117
        if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:118
            ctx:command("doclientfx", "hSpawn1, SPELL_MIST, FALSE, TRUE") -- BC_MANAGER.scr:119
            ctx:command("wait", "1, 2, RemoveCreature") -- BC_MANAGER.scr:120
        end -- BC_MANAGER.scr:121
    else -- BC_MANAGER.scr:122
        if ctx:condition("hLink==hSpawn1") then -- BC_MANAGER.scr:123
            ctx:command("hspawn1", "= NULL") -- BC_MANAGER.scr:124
            if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:125
                ctx:command("doclientfx", "hSpawn0, SPELL_MIST, FALSE, TRUE") -- BC_MANAGER.scr:126
                ctx:command("wait", "2, 2, RemoveCreature") -- BC_MANAGER.scr:127
            end -- BC_MANAGER.scr:128
        else -- BC_MANAGER.scr:129
            if ctx:condition("hLink==hOpener") then -- BC_MANAGER.scr:130
                ctx:command("hopener", "= NULL") -- BC_MANAGER.scr:131
                ctx:addTrigger("open", "StartOpen") -- BC_MANAGER.scr:132
            end -- BC_MANAGER.scr:133
        end -- BC_MANAGER.scr:134
    end -- BC_MANAGER.scr:135
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:137
end

script.labels["RemoveCreature"] = function(ctx)
    -- BC_MANAGER.scr:140
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:142
        ctx:command("removeobject", "hSpawn0") -- BC_MANAGER.scr:143
        ctx:command("hspawn0", "= NULL") -- BC_MANAGER.scr:144
    else -- BC_MANAGER.scr:145
        if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:146
            ctx:command("removeobject", "hSpawn1") -- BC_MANAGER.scr:147
            ctx:command("hspawn1", "= NULL") -- BC_MANAGER.scr:148
        end -- BC_MANAGER.scr:149
    end -- BC_MANAGER.scr:150
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:152
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:154
end

script.labels["ForceEndFight"] = function(ctx)
    -- BC_MANAGER.scr:157
    if ctx:condition("hSpawn0!=0") then -- BC_MANAGER.scr:159
        ctx:command("removeobject", "hSpawn0") -- BC_MANAGER.scr:160
        ctx:command("hspawn0", "= NULL") -- BC_MANAGER.scr:161
    end -- BC_MANAGER.scr:162
    if ctx:condition("hSpawn1!=0") then -- BC_MANAGER.scr:164
        ctx:command("removeobject", "hSpawn1") -- BC_MANAGER.scr:165
        ctx:command("hspawn1", "= NULL") -- BC_MANAGER.scr:166
    end -- BC_MANAGER.scr:167
    ctx:addTrigger("fight", "StartFight") -- BC_MANAGER.scr:169
    do return ctx:exit("TRUE") end -- BC_MANAGER.scr:171
end

return script
