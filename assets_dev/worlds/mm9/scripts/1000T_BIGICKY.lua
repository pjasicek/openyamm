-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_BIGICKY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "Flags.inc" }

-- 1000T_BigIcky.scr
-- Karl Drown 12-10-01
-- Flying creature (Big Bat)
-- p0 = MarkerPath name
-- p1 = Index Starting Number
-- p2 = Index Stopping Number
script.labels["DoNothing"] = function(ctx)
    -- 1000T_BIGICKY.scr:24
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:27
end

script.labels["Triggered"] = function(ctx)
    -- 1000T_BIGICKY.scr:29
    ctx:state().n_IsTriggered = 1 -- 1000T_BIGICKY.scr:31
    mm9.gosub(script, ctx, "CheckTrigger") -- 1000T_BIGICKY.scr:32
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:33
end

script.labels["WaitHere"] = function(ctx)
    -- 1000T_BIGICKY.scr:35
    ctx:self():loopAnimation("Hang", 0, "CheckTrigger") -- 1000T_BIGICKY.scr:38
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:39
end

script.labels["CheckTrigger"] = function(ctx)
    -- 1000T_BIGICKY.scr:42
    if ctx:condition("n_IsTriggered==1") then -- 1000T_BIGICKY.scr:44
        mm9.gosub(script, ctx, "TraverseBegin") -- 1000T_BIGICKY.scr:45
    else -- 1000T_BIGICKY.scr:46
        mm9.gosub(script, ctx, "WaitHere") -- 1000T_BIGICKY.scr:47
    end -- 1000T_BIGICKY.scr:48
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:50
end

script.labels["OnTraverseDone"] = function(ctx)
    -- 1000T_BIGICKY.scr:53
    ctx:state().n_IsTriggered = 0 -- 1000T_BIGICKY.scr:55
    if ctx:condition("b_Direction==0") then -- 1000T_BIGICKY.scr:56
        if ctx:condition("LISTINDEX==LISTLAST") then -- 1000T_BIGICKY.scr:57
            ctx:state().b_Direction = 1 -- 1000T_BIGICKY.scr:58
            mm9.gosub(script, ctx, "WaitHere") -- 1000T_BIGICKY.scr:59
        end -- 1000T_BIGICKY.scr:60
    else -- 1000T_BIGICKY.scr:61
        if ctx:condition("LISTINDEX==LISTLAST") then -- 1000T_BIGICKY.scr:62
            mm9.gosub(script, ctx, "ReversePath") -- 1000T_BIGICKY.scr:63
            mm9.gosub(script, ctx, "TraverseResume") -- 1000T_BIGICKY.scr:64
        end -- 1000T_BIGICKY.scr:65
        if ctx:condition("LISTINDEX==LISTFIRST") then -- 1000T_BIGICKY.scr:66
            ctx:state().b_Direction = 0 -- 1000T_BIGICKY.scr:67
            mm9.gosub(script, ctx, "WaitHere") -- 1000T_BIGICKY.scr:68
        end -- 1000T_BIGICKY.scr:69
    end -- 1000T_BIGICKY.scr:70
    ctx:playSound("Sounds\\AnimSounds\\evileyeflap.wav", "DoNothing", 1000, 400, "FALSE", 90) -- 1000T_BIGICKY.scr:71
    ctx:playSound("Sounds\\Ambient\\flag_flap02.wav", "DoNothing", 200, 1000, "FALSE", 100) -- 1000T_BIGICKY.scr:72
    ctx:playSound("Sounds\\DeathSounds\\mummydie1.wav", "DoNothing", 200, 1000, "FALSE", 100) -- 1000T_BIGICKY.scr:73
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:75
end

script.labels["Main2"] = function(ctx)
    -- 1000T_BIGICKY.scr:77
    ctx:randomInt(0, 100, "TRAVERSERADIUS") -- 1000T_BIGICKY.scr:79
    ctx:randomInt(2, 3, "nTemp") -- 1000T_BIGICKY.scr:80
    ctx:self():setModelFilenames("models\\flyingicky.abc", "TEXTURES\\LevelTextures\\Misc\\black.dtx") -- 1000T_BIGICKY.scr:81
    ctx:state().b_Direction = 0 -- 1000T_BIGICKY.scr:82
    ctx:self():setFlag("FLAG_SOLID", false) -- 1000T_BIGICKY.scr:84
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- 1000T_BIGICKY.scr:85
    ctx:state().nSpeed = ctx:self():getStat("FlyVel") -- 1000T_BIGICKY.scr:86
    ctx:set("nSpeed", "nSpeed * nTemp") -- 1000T_BIGICKY.scr:87
    ctx:self():setStat("FlyVel", "nSpeed") -- 1000T_BIGICKY.scr:88
    ctx:addTrigger("Go", "Triggered") -- 1000T_BIGICKY.scr:89
    ctx:onEvent("OnStuck", "TraverseResume") -- 1000T_BIGICKY.scr:90
    mm9.gosub(script, ctx, "WaitHere") -- 1000T_BIGICKY.scr:91
    do return ctx:exit("True") end -- 1000T_BIGICKY.scr:92
end

script.labels["Main"] = function(ctx)
    -- 1000T_BIGICKY.scr:95
    mm9.gosub(script, ctx, "SetTraverseRun") -- 1000T_BIGICKY.scr:97
    ctx:getParam(0, "LISTNAME") -- 1000T_BIGICKY.scr:98
    ctx:getParam(1, "LISTFIRST") -- 1000T_BIGICKY.scr:99
    ctx:getParam(2, "LISTLAST") -- 1000T_BIGICKY.scr:100
    ctx:wait(0, 0.5, "Main2") -- 1000T_BIGICKY.scr:101
    do return ctx:exit("") end -- 1000T_BIGICKY.scr:102
end

return script
