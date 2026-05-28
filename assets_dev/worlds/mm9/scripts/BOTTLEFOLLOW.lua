-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTTLEFOLLOW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "ListTraverseNONAI.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "flags.inc" }

-- BottleFollow.scr
-- by SJR
-- 11-08-01
-- Purpose:bottle floats away and leads
-- the player somewhere
script.labels["Main"] = function(ctx)
    -- BOTTLEFOLLOW.scr:39
    ctx:getParam(0, "STARTNAME") -- BOTTLEFOLLOW.scr:41
    ctx:getParam(1, "STARTFIRST") -- BOTTLEFOLLOW.scr:42
    ctx:getParam(2, "STARTLAST") -- BOTTLEFOLLOW.scr:43
    ctx:getParam(3, "FINISHNAME") -- BOTTLEFOLLOW.scr:45
    ctx:getParam(4, "FINISHFIRST") -- BOTTLEFOLLOW.scr:46
    ctx:getParam(5, "FINISHLAST") -- BOTTLEFOLLOW.scr:47
    ctx:command("listname", "= STARTNAME") -- BOTTLEFOLLOW.scr:49
    ctx:command("listfirst", "= STARTFIRST") -- BOTTLEFOLLOW.scr:50
    ctx:command("listlast", "= STARTLAST") -- BOTTLEFOLLOW.scr:51
    mm9.gosub(script, ctx, "SetTraverseOnce") -- BOTTLEFOLLOW.scr:53
    ctx:command("traverse_speed", "= 40") -- BOTTLEFOLLOW.scr:54
    ctx:command("getmyhandle", "hMe") -- BOTTLEFOLLOW.scr:56
    mm9.gosub(script, ctx, "FloatLoop") -- BOTTLEFOLLOW.scr:58
    do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:60
end

script.labels["OnTraverseDone"] = function(ctx)
    -- BOTTLEFOLLOW.scr:63
    if ctx:condition("bFinishing==FALSE") then -- BOTTLEFOLLOW.scr:65
        if ctx:condition("LISTINDEX==LISTLAST") then -- BOTTLEFOLLOW.scr:67
            ctx:command("bfinishing", "= TRUE") -- BOTTLEFOLLOW.scr:68
            mm9.gosub(script, ctx, "TraversePause") -- BOTTLEFOLLOW.scr:69
            mm9.gosub(script, ctx, "GotoFinishing") -- BOTTLEFOLLOW.scr:70
            mm9.gosub(script, ctx, "TraverseResume") -- BOTTLEFOLLOW.scr:71
            ctx:command("bcontinue", "= 1") -- BOTTLEFOLLOW.scr:72
        end -- BOTTLEFOLLOW.scr:73
    else -- BOTTLEFOLLOW.scr:75
        if ctx:condition("LISTINDEX==LISTLAST") then -- BOTTLEFOLLOW.scr:77
            ctx:command("bfinishing", "= FALSE") -- BOTTLEFOLLOW.scr:78
            mm9.gosub(script, ctx, "TraversePause") -- BOTTLEFOLLOW.scr:79
            mm9.gosub(script, ctx, "GotoBeginning") -- BOTTLEFOLLOW.scr:80
            mm9.gosub(script, ctx, "TraverseResume") -- BOTTLEFOLLOW.scr:81
            ctx:command("bcontinue", "= 1") -- BOTTLEFOLLOW.scr:82
        end -- BOTTLEFOLLOW.scr:83
    end -- BOTTLEFOLLOW.scr:85
    do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:87
end

script.labels["FloatLoop"] = function(ctx)
    -- BOTTLEFOLLOW.scr:90
    -- bob and rotate the bottle
    if ctx:condition("nCounter>=6") then -- BOTTLEFOLLOW.scr:93
        ctx:command("ncounter", "= 0") -- BOTTLEFOLLOW.scr:94
        ctx:command("bfinishing", "= FALSE") -- BOTTLEFOLLOW.scr:95
        mm9.gosub(script, ctx, "TraverseBegin") -- BOTTLEFOLLOW.scr:96
        do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:97
    end -- BOTTLEFOLLOW.scr:98
    ctx:command("rotate", "0,1,0, ANGLE_DIST, ANGLE_RATE, DoNothing") -- BOTTLEFOLLOW.scr:100
    ctx:command("ndir", "= nDir * -1") -- BOTTLEFOLLOW.scr:102
    ctx:command("movedir", "0,nDir,0, FLOAT_DIST, FLOAT_RATE, FloatLoop") -- BOTTLEFOLLOW.scr:104
    ctx:command("ncounter", "= nCounter + 1") -- BOTTLEFOLLOW.scr:106
    do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:108
end

script.labels["GotoBeginning"] = function(ctx)
    -- BOTTLEFOLLOW.scr:111
    ctx:command("listname", "= STARTNAME") -- BOTTLEFOLLOW.scr:113
    ctx:command("listfirst", "= STARTFIRST") -- BOTTLEFOLLOW.scr:114
    ctx:command("listlast", "= STARTLAST") -- BOTTLEFOLLOW.scr:115
    mm9.gosub(script, ctx, "GetFirstObject") -- BOTTLEFOLLOW.scr:117
    ctx:command("getpos", "LISTOBJECT, xMe,yMe,zMe") -- BOTTLEFOLLOW.scr:119
    ctx:command("setpos", "hMe, xMe,yMe,zMe") -- BOTTLEFOLLOW.scr:120
    do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:122
end

script.labels["GotoFinishing"] = function(ctx)
    -- BOTTLEFOLLOW.scr:125
    ctx:command("listname", "= FINISHNAME") -- BOTTLEFOLLOW.scr:127
    ctx:command("listfirst", "= FINISHFIRST") -- BOTTLEFOLLOW.scr:128
    ctx:command("listlast", "= FINISHLAST") -- BOTTLEFOLLOW.scr:129
    mm9.gosub(script, ctx, "GetFirstObject") -- BOTTLEFOLLOW.scr:131
    ctx:command("getpos", "LISTOBJECT, xMe,yMe,zMe") -- BOTTLEFOLLOW.scr:133
    ctx:command("setpos", "hMe, xMe,yMe,zMe") -- BOTTLEFOLLOW.scr:134
    do return ctx:exit("TRUE") end -- BOTTLEFOLLOW.scr:136
end

return script
