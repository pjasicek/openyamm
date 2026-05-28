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
    ctx:command("onpoststartworld", "InitDwarvenMiner") -- DWARVENMINER.scr:35
    ctx:command("onpostminisaveload", "InitDwarvenMiner") -- DWARVENMINER.scr:36
    ctx:command("oncachefiles", "CacheFiles") -- DWARVENMINER.scr:37
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:39
end

script.labels["CacheFiles"] = function(ctx)
    -- DWARVENMINER.scr:42
    ctx:command("cachesound", "\"sounds\\animsounds\\dwarfwattack1.wav\"") -- DWARVENMINER.scr:44
    ctx:command("cachesound", "\"sounds\\animsounds\\dwarfwattack2.wav\"") -- DWARVENMINER.scr:45
    ctx:command("cachesound", "\"sounds\\weapons\\bigswordclang.wav\"") -- DWARVENMINER.scr:46
    ctx:command("cachesound", "\"sounds\\weapons\\battleaxethump.wav\"") -- DWARVENMINER.scr:47
    ctx:command("cachesound", "\"sounds\\weapons\\carmorchain.wav\"") -- DWARVENMINER.scr:48
    ctx:command("cachesound", "\"sounds\\animsounds\\dwarf\\aware.wav\"") -- DWARVENMINER.scr:49
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:51
end

script.labels["InitDwarvenMiner"] = function(ctx)
    -- DWARVENMINER.scr:54
    ctx:command("addfriend", "AIBase") -- DWARVENMINER.scr:56
    ctx:command("addfriend", "Player") -- DWARVENMINER.scr:57
    ctx:command("addenemy", "Troglodyte") -- DWARVENMINER.scr:58
    ctx:command("addenemy", "Basilisk") -- DWARVENMINER.scr:59
    ctx:command("addenemy", "Nagate") -- DWARVENMINER.scr:60
    ctx:addTrigger("use", "OnRudeEnter") -- DWARVENMINER.scr:62
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- DWARVENMINER.scr:63
    ctx:command("getobjecthandle", "sMineName, hMine") -- DWARVENMINER.scr:65
    ctx:command("getobjecthandle", "sDumpName, hDump") -- DWARVENMINER.scr:66
    mm9.gosub(script, ctx, "GoMine") -- DWARVENMINER.scr:68
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:70
end

script.labels["OnRudeEnter"] = function(ctx)
    -- DWARVENMINER.scr:73
    ctx:command("loopanim", "stand, 0") -- DWARVENMINER.scr:75
    do return ctx:exit("FALSE") end -- DWARVENMINER.scr:77
end

script.labels["OnRudeExit"] = function(ctx)
    -- DWARVENMINER.scr:80
    ctx:command("wait", "0, 1, OnStuck") -- DWARVENMINER.scr:82
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:84
end

script.labels["OnStuck"] = function(ctx)
    -- DWARVENMINER.scr:87
    ctx:command("stop", "") -- DWARVENMINER.scr:89
    if ctx:condition("bMining==TRUE") then -- DWARVENMINER.scr:91
        mm9.gosub(script, ctx, "GoMine") -- DWARVENMINER.scr:92
    else -- DWARVENMINER.scr:93
        mm9.gosub(script, ctx, "GoDump") -- DWARVENMINER.scr:94
    end -- DWARVENMINER.scr:95
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:97
end

script.labels["GoMine"] = function(ctx)
    -- DWARVENMINER.scr:100
    ctx:command("bmining", "= TRUE") -- DWARVENMINER.scr:102
    mm9.gosub(script, ctx, "AttachProp") -- DWARVENMINER.scr:104
    ctx:command("walkto", "hMine, 10, StartMine") -- DWARVENMINER.scr:106
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:108
end

script.labels["StartMine"] = function(ctx)
    -- DWARVENMINER.scr:111
    ctx:command("stop", "") -- DWARVENMINER.scr:113
    ctx:command("faceobject", "hMine, 180, DoNothing") -- DWARVENMINER.scr:115
    ctx:command("getrandomint", "0, 9, nRandom") -- DWARVENMINER.scr:117
    if ctx:condition("nRandom<2") then -- DWARVENMINER.scr:118
        if ctx:condition("nRandom==0") then -- DWARVENMINER.scr:119
            ctx:command("playanim", "\"rub_beard\", StartMine") -- DWARVENMINER.scr:120
        else -- DWARVENMINER.scr:121
            ctx:command("playanim", "\"rock\", StartMine") -- DWARVENMINER.scr:122
        end -- DWARVENMINER.scr:123
        do return ctx:exit("TRUE") end -- DWARVENMINER.scr:124
    else -- DWARVENMINER.scr:125
        if ctx:condition("nRandom==3") then -- DWARVENMINER.scr:126
            mm9.gosub(script, ctx, "GoDump") -- DWARVENMINER.scr:127
        else -- DWARVENMINER.scr:128
            ctx:command("playanim", "\"hammer\", StartMine") -- DWARVENMINER.scr:129
        end -- DWARVENMINER.scr:130
    end -- DWARVENMINER.scr:131
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:133
end

script.labels["GoDump"] = function(ctx)
    -- DWARVENMINER.scr:136
    ctx:command("bmining", "= FALSE") -- DWARVENMINER.scr:138
    mm9.gosub(script, ctx, "SafeDetachProp") -- DWARVENMINER.scr:140
    ctx:command("walkto", "hDump, 10, StartDump") -- DWARVENMINER.scr:142
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:144
end

script.labels["StartDump"] = function(ctx)
    -- DWARVENMINER.scr:147
    ctx:command("stop", "") -- DWARVENMINER.scr:149
    ctx:command("faceobject", "hDump, 180, DoNothing") -- DWARVENMINER.scr:150
    ctx:command("playsound", "\"sounds\\animsounds\\dwarfwattack1.wav\", DoNothing, 1, 500, FALSE, 100") -- DWARVENMINER.scr:151
    ctx:command("playanim", "\"dump\", GoMine") -- DWARVENMINER.scr:152
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:154
end

script.labels["AttachProp"] = function(ctx)
    -- DWARVENMINER.scr:157
    mm9.gosub(script, ctx, "SafeDetachProp") -- DWARVENMINER.scr:159
    ctx:command("attachprop", "\"dwarfaxe.abc\", \"dwarfaxe.dtx\", RHand1, hProp") -- DWARVENMINER.scr:161
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:163
end

script.labels["SafeDetachProp"] = function(ctx)
    -- DWARVENMINER.scr:166
    if ctx:condition("hProp!=0") then -- DWARVENMINER.scr:168
        ctx:command("detachprop", "hProp, FALSE") -- DWARVENMINER.scr:169
        ctx:command("removeobject", "hProp") -- DWARVENMINER.scr:170
        ctx:command("hprop", "= NULL") -- DWARVENMINER.scr:171
    end -- DWARVENMINER.scr:172
    do return ctx:exit("TRUE") end -- DWARVENMINER.scr:174
end

return script
