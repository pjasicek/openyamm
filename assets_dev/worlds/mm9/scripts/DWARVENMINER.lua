-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DWARVENMINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "BaseGlobals.inc" }

-- DwarvenMiner.scr
-- by SJR
-- 10-08-01
-- Purpose:lame-ass dwarven
-- busy work for Thjorad
-- ScriptParams are:
-- p0 = Place to mine
-- p1 = Place to dump
-- Triggers:
-- "On"= Start mining
-- "Off"= Stop mining
script.labels["Main"] = function(ctx)
    -- DWARVENMINER.scr:30
    ctx:getParam(0, "sMineName") -- DWARVENMINER.scr:32
    ctx:getParam(1, "sDumpName") -- DWARVENMINER.scr:33
    ctx:onEvent("OnPostStartWorld", "InitDwarvenMiner") -- DWARVENMINER.scr:35
    ctx:onEvent("OnPostMiniSaveLoad", "InitDwarvenMiner") -- DWARVENMINER.scr:36
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- DWARVENMINER.scr:37
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:39
end

script.labels["CacheFiles"] = function(ctx)
    -- DWARVENMINER.scr:42
    ctx:cacheSound("sounds\\animsounds\\dwarfwattack1.wav") -- DWARVENMINER.scr:44
    ctx:cacheSound("sounds\\animsounds\\dwarfwattack2.wav") -- DWARVENMINER.scr:45
    ctx:cacheSound("sounds\\weapons\\bigswordclang.wav") -- DWARVENMINER.scr:46
    ctx:cacheSound("sounds\\weapons\\battleaxethump.wav") -- DWARVENMINER.scr:47
    ctx:cacheSound("sounds\\weapons\\carmorchain.wav") -- DWARVENMINER.scr:48
    ctx:cacheSound("sounds\\animsounds\\dwarf\\aware.wav") -- DWARVENMINER.scr:49
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:51
end

script.labels["InitDwarvenMiner"] = function(ctx)
    -- DWARVENMINER.scr:54
    ctx:self():addFriend("AIBase") -- DWARVENMINER.scr:56
    ctx:self():addFriend("Player") -- DWARVENMINER.scr:57
    ctx:self():addEnemy("Troglodyte") -- DWARVENMINER.scr:58
    ctx:self():addEnemy("Basilisk") -- DWARVENMINER.scr:59
    ctx:self():addEnemy("Nagate") -- DWARVENMINER.scr:60
    ctx:addTrigger("use", "OnRudeEnter") -- DWARVENMINER.scr:62
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- DWARVENMINER.scr:63
    ctx:state().hMine = ctx:objectOrNil("sMineName") -- DWARVENMINER.scr:65
    ctx:state().hDump = ctx:objectOrNil("sDumpName") -- DWARVENMINER.scr:66
    mm9.gosub(script, ctx, "GoMine") -- DWARVENMINER.scr:68
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:70
end

script.labels["OnRudeEnter"] = function(ctx)
    -- DWARVENMINER.scr:73
    ctx:self():loopAnimation("stand", 0) -- DWARVENMINER.scr:75
    do return ctx:exit("FALSE") end -- DWARVENMINER.scr:77
end

script.labels["OnRudeExit"] = function(ctx)
    -- DWARVENMINER.scr:80
    ctx:wait(0, 1, "OnStuck") -- DWARVENMINER.scr:82
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:84
end

script.labels["OnStuck"] = function(ctx)
    -- DWARVENMINER.scr:87
    ctx:self():stop() -- DWARVENMINER.scr:89
    if ctx:condition("bMining==TRUE") then -- DWARVENMINER.scr:91
        mm9.gosub(script, ctx, "GoMine") -- DWARVENMINER.scr:92
    else -- DWARVENMINER.scr:93
        mm9.gosub(script, ctx, "GoDump") -- DWARVENMINER.scr:94
    end -- DWARVENMINER.scr:95
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:97
end

script.labels["GoMine"] = function(ctx)
    -- DWARVENMINER.scr:100
    ctx:state().bMining = true -- DWARVENMINER.scr:102
    mm9.gosub(script, ctx, "AttachProp") -- DWARVENMINER.scr:104
    ctx:self():walkTo(ctx:object("hMine"), 10, "StartMine") -- DWARVENMINER.scr:106
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:108
end

script.labels["StartMine"] = function(ctx)
    -- DWARVENMINER.scr:111
    ctx:self():stop() -- DWARVENMINER.scr:113
    ctx:self():faceObject(ctx:object("hMine"), 180, "DoNothing") -- DWARVENMINER.scr:115
    ctx:randomInt(0, 9, "nRandom") -- DWARVENMINER.scr:117
    if ctx:condition("nRandom<2") then -- DWARVENMINER.scr:118
        if ctx:condition("nRandom==0") then -- DWARVENMINER.scr:119
            ctx:self():playAnimation("rub_beard", "StartMine") -- DWARVENMINER.scr:120
        else -- DWARVENMINER.scr:121
            ctx:self():playAnimation("rock", "StartMine") -- DWARVENMINER.scr:122
        end -- DWARVENMINER.scr:123
        do return ctx:exit("TRUE") end -- DWARVENMINER.scr:124
    else -- DWARVENMINER.scr:125
        if ctx:condition("nRandom==3") then -- DWARVENMINER.scr:126
            mm9.gosub(script, ctx, "GoDump") -- DWARVENMINER.scr:127
        else -- DWARVENMINER.scr:128
            ctx:self():playAnimation("hammer", "StartMine") -- DWARVENMINER.scr:129
        end -- DWARVENMINER.scr:130
    end -- DWARVENMINER.scr:131
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:133
end

script.labels["GoDump"] = function(ctx)
    -- DWARVENMINER.scr:136
    ctx:state().bMining = false -- DWARVENMINER.scr:138
    mm9.gosub(script, ctx, "SafeDetachProp") -- DWARVENMINER.scr:140
    ctx:self():walkTo(ctx:object("hDump"), 10, "StartDump") -- DWARVENMINER.scr:142
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:144
end

script.labels["StartDump"] = function(ctx)
    -- DWARVENMINER.scr:147
    ctx:self():stop() -- DWARVENMINER.scr:149
    ctx:self():faceObject(ctx:object("hDump"), 180, "DoNothing") -- DWARVENMINER.scr:150
    ctx:playSound("sounds\\animsounds\\dwarfwattack1.wav", "DoNothing", 1, 500, "FALSE", 100) -- DWARVENMINER.scr:151
    ctx:self():playAnimation("dump", "GoMine") -- DWARVENMINER.scr:152
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:154
end

script.labels["AttachProp"] = function(ctx)
    -- DWARVENMINER.scr:157
    mm9.gosub(script, ctx, "SafeDetachProp") -- DWARVENMINER.scr:159
    ctx:self():attachProp("dwarfaxe.abc", "dwarfaxe.dtx", "RHand1", ctx:object("hProp")) -- DWARVENMINER.scr:161
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:163
end

script.labels["SafeDetachProp"] = function(ctx)
    -- DWARVENMINER.scr:166
    if ctx:condition("hProp!=0") then -- DWARVENMINER.scr:168
        ctx:self():detachProp(ctx:object("hProp"), "FALSE") -- DWARVENMINER.scr:169
        ctx:object("hProp"):remove() -- DWARVENMINER.scr:170
        ctx:state().hProp = nil -- DWARVENMINER.scr:171
    end -- DWARVENMINER.scr:172
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:174
end

return script
