-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIRCHILD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "FollowPlayer.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "baseDoor.inc" }

-- YanmirChild.Scr
-- edited by Bones -- 4/20/03, 6/12/03
-- TELP Patch 1.3 -- cries for help harder to miss
-- children will routinely look for exit
script.labels["Main"] = function(ctx)
    -- YANMIRCHILD.scr:18
    ctx:getParam(0, "sEscapeName") -- YANMIRCHILD.scr:20
    ctx:setConsoleNumVar("YANMIR_CHILD_HELP", 0) -- YANMIRCHILD.scr:22
    ctx:command("onpoststartworld", "InitYanmirChild") -- YANMIRCHILD.scr:24
    ctx:command("onpostminisaveload", "InitYanmirChild") -- YANMIRCHILD.scr:25
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:27
end

script.labels["InitYanmirChild"] = function(ctx)
    -- YANMIRCHILD.scr:30
    ctx:addTrigger("use", "OnUse") -- YANMIRCHILD.scr:32
    ctx:command("onfoundplayer", "ShoutForHelp") -- YANMIRCHILD.scr:34
    ctx:command("setidle", "") -- YANMIRCHILD.scr:36
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:38
end

script.labels["OnUse"] = function(ctx)
    -- YANMIRCHILD.scr:41
    -- only follow if they unlocked the cage
    ctx:hasKey(7001, "nTemp") -- YANMIRCHILD.scr:44
    if ctx:condition("nTemp==TRUE") then -- YANMIRCHILD.scr:45
        mm9.gosub(script, ctx, "BaseDoorInit") -- YANMIRCHILD.scr:46
        mm9.gosub(script, ctx, "FollowInit") -- YANMIRCHILD.scr:47
        mm9.gosub(script, ctx, "FollowStart") -- YANMIRCHILD.scr:48
        ctx:command("onstuckdone", "FollowStart") -- YANMIRCHILD.scr:49
    else -- YANMIRCHILD.scr:50
        -- RolloverText 200, 1, 4000, 3000
    end -- YANMIRCHILD.scr:52
    do return ctx:exit("FALSE") end -- YANMIRCHILD.scr:54
end

script.labels["ShoutForHelp"] = function(ctx)
    -- YANMIRCHILD.scr:57
    -- to text to tell the player "Help!"
    ctx:getConsoleNumVar("YANMIR_CHILD_HELP", "nTemp") -- YANMIRCHILD.scr:60
    if ctx:condition("nTemp==0") then -- YANMIRCHILD.scr:61
        ctx:setConsoleNumVar("YANMIR_CHILD_HELP", 1) -- YANMIRCHILD.scr:62
        ctx:hasKey(7001, "nTemp") -- YANMIRCHILD.scr:63
        if ctx:condition("nTemp==TRUE") then -- YANMIRCHILD.scr:64
            ctx:command("rollovertext", "201 0") -- YANMIRCHILD.scr:65
        else -- YANMIRCHILD.scr:66
            ctx:command("rollovertext", "200 0") -- YANMIRCHILD.scr:67
        end -- YANMIRCHILD.scr:68
    end -- YANMIRCHILD.scr:69
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:71
end

script.labels["OnFollowDone"] = function(ctx)
    -- YANMIRCHILD.scr:74
    -- check to see if near escape point
    -- if( hEscape==0 )
    ctx:command("getobjecthandle", "sEscapeName, hEscape") -- YANMIRCHILD.scr:78
    -- endif
    if ctx:condition("hEscape!=0") then -- YANMIRCHILD.scr:81
        ctx:command("aigetdistance", "hEscape, nTemp") -- YANMIRCHILD.scr:82
        if ctx:condition("nTemp<ESCAPE_RADIUS") then -- YANMIRCHILD.scr:83
            mm9.gosub(script, ctx, "EscapeLevel") -- YANMIRCHILD.scr:84
        end -- YANMIRCHILD.scr:85
    end -- YANMIRCHILD.scr:86
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:88
end

script.labels["EscapeLevel"] = function(ctx)
    -- YANMIRCHILD.scr:91
    -- run to teleporter
    -- if( hEscape!=0 )
    ctx:command("runtopos", "6528 71 279 0 Escape") -- YANMIRCHILD.scr:95
    ctx:command("onobstacle", "Escape") -- YANMIRCHILD.scr:96
    -- endif
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:99
end

script.labels["Escape"] = function(ctx)
    -- YANMIRCHILD.scr:102
    -- disappear
    ctx:command("stop", "") -- YANMIRCHILD.scr:105
    ctx:command("hescape", "= NULL") -- YANMIRCHILD.scr:106
    ctx:command("getmyhandle", "hEscape") -- YANMIRCHILD.scr:107
    ctx:command("removeobject", "hEscape") -- YANMIRCHILD.scr:108
    do return ctx:exit("TRUE") end -- YANMIRCHILD.scr:110
end

return script
