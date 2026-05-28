-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKFOLLOWGOOSE2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "HonkHostility.inc" }

-- HonkFollowGoose.scr
-- by SJR
-- 10-09-01
-- Purpose:follow a goose around and
-- make it look more interesting
-- than it actually is...
script.labels["Main"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:22
    ctx:getParam(0, "sGooseName") -- HONKFOLLOWGOOSE2.scr:24
    ctx:command("onpoststartworld", "InitHonkFollowGoose") -- HONKFOLLOWGOOSE2.scr:26
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE2.scr:28
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:31
    -- overloaded so dumb goose death
    -- won't set of Hostility
    -- and wimping them out
    ctx:command("getmyhandle", "g_hmyobject") -- HONKFOLLOWGOOSE2.scr:41
    ctx:command("g_ntemp", "= 10") -- HONKFOLLOWGOOSE2.scr:42
    ctx:command("setstat", "g_hmyobject HitPoints g_ntemp") -- HONKFOLLOWGOOSE2.scr:43
    ctx:command("g_ntemp", "= 1") -- HONKFOLLOWGOOSE2.scr:44
    ctx:command("getstat", "g_hmyobject AC g_ntemp") -- HONKFOLLOWGOOSE2.scr:45
    mm9.gosub(script, ctx, "BecomeHostile") -- HONKFOLLOWGOOSE2.scr:49
    do return ctx:exit("") end -- HONKFOLLOWGOOSE2.scr:51
end

script.labels["InitHonkFollowGoose"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:56
    ctx:command("cachesound", "sounds\\ambient\\crowd01.wav") -- HONKFOLLOWGOOSE2.scr:63
    ctx:command("ontargetdead", "OnTargetDead") -- HONKFOLLOWGOOSE2.scr:64
    ctx:command("getobjecthandle", "sGooseName, hGoose") -- HONKFOLLOWGOOSE2.scr:66
    if ctx:condition("hGoose==0") then -- HONKFOLLOWGOOSE2.scr:68
        ctx:command("wait", "0, 1, InitHonkFollowGoose") -- HONKFOLLOWGOOSE2.scr:69
    else -- HONKFOLLOWGOOSE2.scr:70
        ctx:command("target", "hGoose, TRUE") -- HONKFOLLOWGOOSE2.scr:71
        mm9.gosub(script, ctx, "FollowLoop") -- HONKFOLLOWGOOSE2.scr:72
    end -- HONKFOLLOWGOOSE2.scr:73
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKFOLLOWGOOSE2.scr:75
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE2.scr:77
end

script.labels["FollowLoop"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:80
    if ctx:condition("hGoose!=0") then -- HONKFOLLOWGOOSE2.scr:82
        ctx:command("runto", "hGoose, 64, CrazyRun") -- HONKFOLLOWGOOSE2.scr:83
    end -- HONKFOLLOWGOOSE2.scr:84
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE2.scr:86
end

script.labels["CrazyRun"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:89
    ctx:command("playsound", "\"sounds\\animsounds\\goose\\wince1.wav\", DoNothing, 1, 100, FALSE, 100") -- HONKFOLLOWGOOSE2.scr:91
    ctx:command("getrandomint", "-5000, 5000, diff") -- HONKFOLLOWGOOSE2.scr:92
    ctx:command("runtopos", "diff,diff,diff, 0, DoNothing") -- HONKFOLLOWGOOSE2.scr:93
    ctx:command("wait", "1, 2, FollowLoop") -- HONKFOLLOWGOOSE2.scr:94
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE2.scr:96
end

script.labels["OnTargetDead"] = function(ctx)
    -- HONKFOLLOWGOOSE2.scr:99
    -- null out goose, go hostile
    ctx:command("stop", "") -- HONKFOLLOWGOOSE2.scr:102
    ctx:command("hgoose", "= NULL") -- HONKFOLLOWGOOSE2.scr:103
    ctx:command("addenemy", "Player") -- HONKFOLLOWGOOSE2.scr:105
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE2.scr:107
end

return script
