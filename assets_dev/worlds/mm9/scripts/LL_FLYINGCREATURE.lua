-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LL_FLYINGCREATURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "Flags.inc" }

-- LL_FlyingCreature.scr
-- Karl Drown 12-8-01
-- Flying creatures (Bats)
-- p0 = MarkerPath name
-- p1 = Index Starting Number
-- p2 = Index Stopping Number
script.labels["DoNothing"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:24
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:27
end

script.labels["Triggered"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:29
    ctx:command("n_istriggered", "= 1") -- LL_FLYINGCREATURE.scr:31
    mm9.gosub(script, ctx, "CheckTrigger") -- LL_FLYINGCREATURE.scr:32
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:33
end

script.labels["WaitHere"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:35
    ctx:command("loopanim", "Hang, 0, CheckTrigger") -- LL_FLYINGCREATURE.scr:38
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:39
end

script.labels["CheckTrigger"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:42
    if ctx:condition("n_IsTriggered==1") then -- LL_FLYINGCREATURE.scr:44
        mm9.gosub(script, ctx, "TraverseBegin") -- LL_FLYINGCREATURE.scr:45
    else -- LL_FLYINGCREATURE.scr:46
        mm9.gosub(script, ctx, "WaitHere") -- LL_FLYINGCREATURE.scr:47
    end -- LL_FLYINGCREATURE.scr:48
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:50
end

script.labels["OnTraverseDone"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:53
    ctx:command("n_istriggered", "= 0") -- LL_FLYINGCREATURE.scr:55
    if ctx:condition("b_Direction==0") then -- LL_FLYINGCREATURE.scr:56
        if ctx:condition("LISTINDEX==LISTLAST") then -- LL_FLYINGCREATURE.scr:57
            ctx:command("b_direction", "= 1") -- LL_FLYINGCREATURE.scr:58
            mm9.gosub(script, ctx, "WaitHere") -- LL_FLYINGCREATURE.scr:59
        end -- LL_FLYINGCREATURE.scr:60
    else -- LL_FLYINGCREATURE.scr:61
        if ctx:condition("LISTINDEX==LISTLAST") then -- LL_FLYINGCREATURE.scr:62
            mm9.gosub(script, ctx, "ReversePath") -- LL_FLYINGCREATURE.scr:63
            mm9.gosub(script, ctx, "TraverseResume") -- LL_FLYINGCREATURE.scr:64
        end -- LL_FLYINGCREATURE.scr:65
        if ctx:condition("LISTINDEX==LISTFIRST") then -- LL_FLYINGCREATURE.scr:66
            ctx:command("b_direction", "= 0") -- LL_FLYINGCREATURE.scr:67
            mm9.gosub(script, ctx, "WaitHere") -- LL_FLYINGCREATURE.scr:68
        end -- LL_FLYINGCREATURE.scr:69
    end -- LL_FLYINGCREATURE.scr:70
    ctx:command("playsound", "Sounds\\AnimSounds\\evileyeflap.wav DoNothing 200 400 FALSE 80") -- LL_FLYINGCREATURE.scr:71
    ctx:command("playsound", "Sounds\\Ambient\\flag_flap02.wav DoNothing 200 500 FALSE 100") -- LL_FLYINGCREATURE.scr:72
    ctx:command("playsound", "Sounds\\DeathSounds\\mummydie1.wav DoNothing 200 500 FALSE 100") -- LL_FLYINGCREATURE.scr:73
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:75
end

script.labels["Main2"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:77
    ctx:command("getrandomint", "0, 100, TRAVERSERADIUS") -- LL_FLYINGCREATURE.scr:79
    ctx:command("getrandomint", "2, 3, nTemp") -- LL_FLYINGCREATURE.scr:80
    ctx:command("setmodelfilenames", "models\\flyingicky.abc TEXTURES\\LevelTextures\\Misc\\black.dtx") -- LL_FLYINGCREATURE.scr:81
    ctx:command("b_direction", "= 0") -- LL_FLYINGCREATURE.scr:82
    ctx:command("getmyhandle", "hMe") -- LL_FLYINGCREATURE.scr:83
    ctx:command("clearflag", "hMe, FLAG_SOLID") -- LL_FLYINGCREATURE.scr:84
    ctx:command("setflag", "hMe, FLAG_GOTHRUWORLD") -- LL_FLYINGCREATURE.scr:85
    ctx:command("getstat", "hMe, FlyVel, nSpeed") -- LL_FLYINGCREATURE.scr:86
    ctx:command("nspeed", "= nSpeed * nTemp") -- LL_FLYINGCREATURE.scr:87
    ctx:command("setstat", "hMe, FlyVel, nSpeed") -- LL_FLYINGCREATURE.scr:88
    ctx:addTrigger("Go", "Triggered") -- LL_FLYINGCREATURE.scr:89
    ctx:command("onstuck", "TraverseResume") -- LL_FLYINGCREATURE.scr:90
    mm9.gosub(script, ctx, "WaitHere") -- LL_FLYINGCREATURE.scr:91
    do return ctx:exit("True") end -- LL_FLYINGCREATURE.scr:92
end

script.labels["Main"] = function(ctx)
    -- LL_FLYINGCREATURE.scr:95
    mm9.gosub(script, ctx, "SetTraverseRun") -- LL_FLYINGCREATURE.scr:97
    ctx:getParam(0, "LISTNAME") -- LL_FLYINGCREATURE.scr:98
    ctx:getParam(1, "LISTFIRST") -- LL_FLYINGCREATURE.scr:99
    ctx:getParam(2, "LISTLAST") -- LL_FLYINGCREATURE.scr:100
    ctx:command("wait", "0, 0.5, Main2") -- LL_FLYINGCREATURE.scr:101
    do return ctx:exit("") end -- LL_FLYINGCREATURE.scr:102
end

return script
