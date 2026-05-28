-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOUNCYBALLFOLLOW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

script.labels["BouncyBallFollow.scr"] = function(ctx)
    -- BOUNCYBALLFOLLOW.scr:2
end

-- Tony Evans
-- This script is used to make the Bouncy Ball Trap follow the
-- nearest player.
-- Parameters:
-- p1 - Velocity of Bouncy Ball
script.labels["CheckPlayer"] = function(ctx)
    -- BOUNCYBALLFOLLOW.scr:42
    ctx:command("getplayerhandle", "PlayerToChase, chasearea") -- BOUNCYBALLFOLLOW.scr:46
    if ctx:condition("PlayerToChase==NULL") then -- BOUNCYBALLFOLLOW.scr:48
        ctx:command("set", "Chasing, 0") -- BOUNCYBALLFOLLOW.scr:49
        mm9.gosub(script, ctx, "ReturnToCenter") -- BOUNCYBALLFOLLOW.scr:50
    end -- BOUNCYBALLFOLLOW.scr:51
    ctx:command("getpos", "PlayerToChase, xplayer, yplayer, zplayer") -- BOUNCYBALLFOLLOW.scr:53
    -- Get the position of the Bouncy Ball
    ctx:command("getmyhandle", "g_hMyObject") -- BOUNCYBALLFOLLOW.scr:56
    ctx:command("getpos", "g_hMyObject, xball, yball, zball") -- BOUNCYBALLFOLLOW.scr:57
    ctx:command("set", "Chasing, 1") -- BOUNCYBALLFOLLOW.scr:59
    -- MoveToPos xplayer, yball, zplayer, velocity
    ctx:command("faceobject", "PlayerToChase, 90") -- BOUNCYBALLFOLLOW.scr:63
    mm9.gosub(script, ctx, "Bounce") -- BOUNCYBALLFOLLOW.scr:65
    ctx:command("wait", ".1, CheckPlayer") -- BOUNCYBALLFOLLOW.scr:67
    do return ctx:exit("") end -- BOUNCYBALLFOLLOW.scr:69
end

script.labels["Bounce"] = function(ctx)
    -- BOUNCYBALLFOLLOW.scr:72
    if ctx:condition("xplayer > xball") then -- BOUNCYBALLFOLLOW.scr:75
        ctx:command("sub", "xball, 1") -- BOUNCYBALLFOLLOW.scr:76
    end -- BOUNCYBALLFOLLOW.scr:77
    if ctx:condition("zplayer > xball") then -- BOUNCYBALLFOLLOW.scr:79
        ctx:command("sub", "xball, 1") -- BOUNCYBALLFOLLOW.scr:80
    end -- BOUNCYBALLFOLLOW.scr:81
    if ctx:condition("xplayer < xball") then -- BOUNCYBALLFOLLOW.scr:83
        ctx:command("add", "xball, 1") -- BOUNCYBALLFOLLOW.scr:84
    end -- BOUNCYBALLFOLLOW.scr:85
    if ctx:condition("zplayer < xball") then -- BOUNCYBALLFOLLOW.scr:87
        ctx:command("add", "xball, 1") -- BOUNCYBALLFOLLOW.scr:88
    end -- BOUNCYBALLFOLLOW.scr:89
    if ctx:condition("up==TRUE") then -- BOUNCYBALLFOLLOW.scr:91
        ctx:command("add", "heightcounter, 16") -- BOUNCYBALLFOLLOW.scr:92
        ctx:command("add", "yball, 16") -- BOUNCYBALLFOLLOW.scr:93
        if ctx:condition("heightcounter > bounceheight") then -- BOUNCYBALLFOLLOW.scr:94
            ctx:command("set", "up, 0") -- BOUNCYBALLFOLLOW.scr:95
        end -- BOUNCYBALLFOLLOW.scr:96
    end -- BOUNCYBALLFOLLOW.scr:97
    if ctx:condition("up=FALSE") then -- BOUNCYBALLFOLLOW.scr:98
        ctx:command("sub", "heightcounter, 16") -- BOUNCYBALLFOLLOW.scr:99
        ctx:command("sub", "yball, 16") -- BOUNCYBALLFOLLOW.scr:100
        if ctx:condition("heightcounter < 0") then -- BOUNCYBALLFOLLOW.scr:101
            ctx:command("set", "up, 1") -- BOUNCYBALLFOLLOW.scr:102
        end -- BOUNCYBALLFOLLOW.scr:103
    end -- BOUNCYBALLFOLLOW.scr:104
    ctx:command("movetopos", "xball, yball, zball, 1000") -- BOUNCYBALLFOLLOW.scr:106
    ctx:command("debugout", "heightcounter") -- BOUNCYBALLFOLLOW.scr:108
    ctx:command("debugout", "xball") -- BOUNCYBALLFOLLOW.scr:109
    ctx:command("debugout", "xplayer") -- BOUNCYBALLFOLLOW.scr:110
    ctx:command("debugout", "yball") -- BOUNCYBALLFOLLOW.scr:111
    ctx:command("debugout", "yplayer") -- BOUNCYBALLFOLLOW.scr:112
    ctx:command("debugout", "zball") -- BOUNCYBALLFOLLOW.scr:113
    ctx:command("debugout", "zplayer") -- BOUNCYBALLFOLLOW.scr:114
    do return ctx:exit("") end -- BOUNCYBALLFOLLOW.scr:117
end

script.labels["ReturnToCenter"] = function(ctx)
    -- BOUNCYBALLFOLLOW.scr:121
    -- MoveToPos xstart, ystart, zstart, velocity
    do return ctx:exit("") end -- BOUNCYBALLFOLLOW.scr:128
end

script.labels["Main"] = function(ctx)
    -- BOUNCYBALLFOLLOW.scr:131
    -- TRACEON
    -- Get the starting position of the Bouncy Ball
    ctx:command("getmyhandle", "g_hMyObject") -- BOUNCYBALLFOLLOW.scr:137
    ctx:command("getpos", "g_hMyObject, xstart, ystart, zstart") -- BOUNCYBALLFOLLOW.scr:138
    -- set up the triggers
    ctx:addTrigger("ChasePlayer", "CheckPlayer") -- BOUNCYBALLFOLLOW.scr:141
    ctx:addTrigger("PlayerGone", "ReturnToCenter") -- BOUNCYBALLFOLLOW.scr:142
    -- get the parameters
    ctx:getParam(0, "g_nTemp") -- BOUNCYBALLFOLLOW.scr:145
    if ctx:condition("g_nTemp!=0") then -- BOUNCYBALLFOLLOW.scr:147
        ctx:command("set", "velocity, g_nTemp") -- BOUNCYBALLFOLLOW.scr:148
    end -- BOUNCYBALLFOLLOW.scr:149
    ctx:getParam(1, "g_nTemp") -- BOUNCYBALLFOLLOW.scr:151
    if ctx:condition("g_nTemp!=0") then -- BOUNCYBALLFOLLOW.scr:153
        ctx:command("set", "chasearea, g_nTemp") -- BOUNCYBALLFOLLOW.scr:154
    end -- BOUNCYBALLFOLLOW.scr:155
    ctx:getParam(2, "g_nTemp") -- BOUNCYBALLFOLLOW.scr:157
    if ctx:condition("g_nTemp!=0") then -- BOUNCYBALLFOLLOW.scr:159
        ctx:command("set", "bounceheight, g_nTemp") -- BOUNCYBALLFOLLOW.scr:160
    end -- BOUNCYBALLFOLLOW.scr:161
    do return ctx:exit("") end -- BOUNCYBALLFOLLOW.scr:163
end

return script
