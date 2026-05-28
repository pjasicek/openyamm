-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKFOLLOWGOOSE.scr"
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
    -- HONKFOLLOWGOOSE.scr:22
    ctx:getParam(0, "sGooseName") -- HONKFOLLOWGOOSE.scr:24
    ctx:command("onpoststartworld", "InitHonkFollowGoose") -- HONKFOLLOWGOOSE.scr:26
    ctx:command("onpostminisaveload", "InitHonkFollowGoose") -- HONKFOLLOWGOOSE.scr:27
    ctx:command("oncachefiles", "CacheFiles") -- HONKFOLLOWGOOSE.scr:28
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:30
end

script.labels["CacheFiles"] = function(ctx)
    -- HONKFOLLOWGOOSE.scr:33
    ctx:command("cachesound", "\"sounds\\ambient\\crowd01.wav\"") -- HONKFOLLOWGOOSE.scr:35
    ctx:command("cachesound", "\"sounds\\animsounds\\goose\\wince1.wav\"") -- HONKFOLLOWGOOSE.scr:36
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:38
end

script.labels["InitHonkFollowGoose"] = function(ctx)
    -- HONKFOLLOWGOOSE.scr:41
    ctx:command("ontargetdead", "OnTargetDead") -- HONKFOLLOWGOOSE.scr:43
    ctx:command("getobjecthandle", "sGooseName, hGoose") -- HONKFOLLOWGOOSE.scr:45
    if ctx:condition("hGoose==0") then -- HONKFOLLOWGOOSE.scr:47
        ctx:command("wait", "0, 1, InitHonkFollowGoose") -- HONKFOLLOWGOOSE.scr:48
    else -- HONKFOLLOWGOOSE.scr:49
        ctx:command("target", "hGoose, TRUE") -- HONKFOLLOWGOOSE.scr:50
        mm9.gosub(script, ctx, "FollowLoop") -- HONKFOLLOWGOOSE.scr:51
    end -- HONKFOLLOWGOOSE.scr:52
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKFOLLOWGOOSE.scr:54
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:56
end

script.labels["FollowLoop"] = function(ctx)
    -- HONKFOLLOWGOOSE.scr:59
    if ctx:condition("hGoose!=0") then -- HONKFOLLOWGOOSE.scr:61
        ctx:command("runto", "hGoose, 64, CrazyRun") -- HONKFOLLOWGOOSE.scr:62
    end -- HONKFOLLOWGOOSE.scr:63
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:65
end

script.labels["CrazyRun"] = function(ctx)
    -- HONKFOLLOWGOOSE.scr:68
    ctx:command("playsound", "\"sounds\\animsounds\\goose\\wince1.wav\", DoNothing, 1, 100, FALSE, 100") -- HONKFOLLOWGOOSE.scr:70
    ctx:command("getrandomint", "-5000, 5000, diff") -- HONKFOLLOWGOOSE.scr:71
    ctx:command("runtopos", "diff,diff,diff, 0, DoNothing") -- HONKFOLLOWGOOSE.scr:72
    ctx:command("wait", "1, 2, FollowLoop") -- HONKFOLLOWGOOSE.scr:73
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:75
end

script.labels["OnTargetDead"] = function(ctx)
    -- HONKFOLLOWGOOSE.scr:78
    -- null out goose, go hostile
    ctx:command("stop", "") -- HONKFOLLOWGOOSE.scr:81
    ctx:command("hgoose", "= NULL") -- HONKFOLLOWGOOSE.scr:82
    ctx:command("addenemy", "Player") -- HONKFOLLOWGOOSE.scr:84
    do return ctx:exit("TRUE") end -- HONKFOLLOWGOOSE.scr:86
end

return script
