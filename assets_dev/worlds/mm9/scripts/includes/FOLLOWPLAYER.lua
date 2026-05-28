-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOLLOWPLAYER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 17, path = "BaseGlobals.inc" }

-- FollowPlayer.inc
-- by SJR
-- 10-13-01
-- Purpose:more cooperative follow
-- script.
-- Triggers:
-- "Use" = follows the sender
-- "Follow" = follows the player
-- "Halt" = stops following
-- Script will call "OnFollowDone" each time it
-- reaches the target. Call FollowInit first.
-- edited by Bones 5/6/03
-- TELP Patch 1.3 -- avoid timer crashes
script.labels["FollowInit"] = function(ctx)
    -- FOLLOWPLAYER.inc:28
    -- sets up triggers
    ctx:command("getmyhandle", "follow_hMe") -- FOLLOWPLAYER.inc:31
    ctx:addTrigger("Use", "FollowOnUse") -- FOLLOWPLAYER.inc:33
    ctx:addTrigger("Follow", "FollowStart") -- FOLLOWPLAYER.inc:34
    ctx:addTrigger("Halt", "FollowStop") -- FOLLOWPLAYER.inc:35
    ctx:command("ontouchnotify", "follow_CheckLadder") -- FOLLOWPLAYER.inc:37
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:39
end

script.labels["FollowStart"] = function(ctx)
    -- FOLLOWPLAYER.inc:42
    -- follow player
    ctx:command("wait", "16 0 DoNothing") -- FOLLOWPLAYER.inc:45
    ctx:command("getplayerhandle", "follow_hPlayer") -- FOLLOWPLAYER.inc:46
    ctx:command("getmyhandle", "follow_hMe") -- FOLLOWPLAYER.inc:47
    ctx:command("follow_bfollowing", "= 1") -- FOLLOWPLAYER.inc:49
    mm9.gosub(script, ctx, "FollowLoop") -- FOLLOWPLAYER.inc:51
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:53
end

script.labels["FollowStop"] = function(ctx)
    -- FOLLOWPLAYER.inc:56
    -- pause following
    ctx:command("wait", "16 0 DoNothing") -- FOLLOWPLAYER.inc:59
    ctx:command("stop", "") -- FOLLOWPLAYER.inc:60
    ctx:command("follow_bfollowing", "= 0") -- FOLLOWPLAYER.inc:61
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:63
end

script.labels["FollowResume"] = function(ctx)
    -- FOLLOWPLAYER.inc:66
    -- follow player
    if ctx:condition("follow_hPlayer!=0") then -- FOLLOWPLAYER.inc:69
        ctx:command("follow_bfollowing", "= 1") -- FOLLOWPLAYER.inc:71
        mm9.gosub(script, ctx, "FollowLoop") -- FOLLOWPLAYER.inc:72
    end -- FOLLOWPLAYER.inc:73
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:75
end

script.labels["OnFollowDone"] = function(ctx)
    -- FOLLOWPLAYER.inc:78
    -- called each time we reach the target
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:81
end

-- private
script.labels["FollowLoop"] = function(ctx)
    -- FOLLOWPLAYER.inc:87
    if ctx:condition("follow_bFollowing==0") then -- FOLLOWPLAYER.inc:88
        do return ctx:exit(1) end -- FOLLOWPLAYER.inc:89
    end -- FOLLOWPLAYER.inc:90
    ctx:command("aigetdistance", "follow_hPlayer, follow_ds") -- FOLLOWPLAYER.inc:91
    -- run radius
    if ctx:condition("follow_ds>200") then -- FOLLOWPLAYER.inc:93
        ctx:command("runto", "follow_hPlayer, 32, FollowDone") -- FOLLOWPLAYER.inc:94
    else -- FOLLOWPLAYER.inc:95
        -- walk radius
        if ctx:condition("follow_ds>100") then -- FOLLOWPLAYER.inc:97
            ctx:command("walkto", "follow_hPlayer, 32, FollowDone") -- FOLLOWPLAYER.inc:98
        else -- FOLLOWPLAYER.inc:99
            ctx:command("setidle", "") -- FOLLOWPLAYER.inc:100
            mm9.gosub(script, ctx, "OnFollowDone") -- FOLLOWPLAYER.inc:101
        end -- FOLLOWPLAYER.inc:102
    end -- FOLLOWPLAYER.inc:103
    -- refresh action every 3 secs
    ctx:command("wait", "16, 3, FollowLoop") -- FOLLOWPLAYER.inc:105
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:106
end

script.labels["FollowDone"] = function(ctx)
    -- FOLLOWPLAYER.inc:108
    mm9.gosub(script, ctx, "OnFollowDone") -- FOLLOWPLAYER.inc:109
    mm9.gosub(script, ctx, "FollowLoop") -- FOLLOWPLAYER.inc:110
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:111
end

script.labels["FollowOnUse"] = function(ctx)
    -- FOLLOWPLAYER.inc:113
    ctx:getParam(0, "follow_hPlayer") -- FOLLOWPLAYER.inc:114
    ctx:command("follow_bfollowing", "= 1") -- FOLLOWPLAYER.inc:115
    mm9.gosub(script, ctx, "FollowLoop") -- FOLLOWPLAYER.inc:116
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:117
end

script.labels["DoNothing"] = function(ctx)
    -- FOLLOWPLAYER.inc:119
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:120
end

-- ladder stuff
script.labels["follow_CheckLadder"] = function(ctx)
    -- FOLLOWPLAYER.inc:134
    ctx:getParam(0, "follow_hObject") -- FOLLOWPLAYER.inc:135
    ctx:command("getclassname", "follow_hObject, follow_sObjectName") -- FOLLOWPLAYER.inc:136
    if ctx:condition("follow_sObjectName==\"Ladder\"") then -- FOLLOWPLAYER.inc:137
        ctx:command("getdims", "follow_hObject, nTemp,LADDER_HEIGHT,nTemp") -- FOLLOWPLAYER.inc:138
        ctx:command("bpinging", "= 1") -- FOLLOWPLAYER.inc:139
        mm9.gosub(script, ctx, "FollowStop") -- FOLLOWPLAYER.inc:140
        mm9.gosub(script, ctx, "follow_PingLoop") -- FOLLOWPLAYER.inc:141
        ctx:command("ontouchnotify", "DoNothing") -- FOLLOWPLAYER.inc:142
    end -- FOLLOWPLAYER.inc:143
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:145
end

script.labels["follow_PingLoop"] = function(ctx)
    -- FOLLOWPLAYER.inc:147
    ctx:command("getpos", "follow_hPlayer,\tnTemp,follow_y\t,nTemp") -- FOLLOWPLAYER.inc:148
    ctx:command("getpos", "follow_hMe,\t\tnTemp,follow_yMe,nTemp") -- FOLLOWPLAYER.inc:149
    ctx:command("follow_nladderheight", "= 2 * LADDER_HEIGHT + LADDER_GAP") -- FOLLOWPLAYER.inc:151
    ctx:command("ntemp", "= follow_y - follow_yMe") -- FOLLOWPLAYER.inc:152
    if ctx:condition("nTemp<0") then -- FOLLOWPLAYER.inc:153
        ctx:command("ntemp", "= nTemp * -1") -- FOLLOWPLAYER.inc:154
    end -- FOLLOWPLAYER.inc:155
    -- cprint ping...
    -- cprint follow_nLadderHeight
    -- cprint nTemp
    -- cprint ************
    if ctx:condition("nTemp<LADDER_GAP") then -- FOLLOWPLAYER.inc:160
        mm9.gosub(script, ctx, "follow_DescendLadder") -- FOLLOWPLAYER.inc:161
    else -- FOLLOWPLAYER.inc:162
        ctx:command("ntemp", "= follow_y - follow_yMe") -- FOLLOWPLAYER.inc:163
        if ctx:condition("nTemp<0") then -- FOLLOWPLAYER.inc:164
            mm9.gosub(script, ctx, "follow_DescendLadder") -- FOLLOWPLAYER.inc:165
        else -- FOLLOWPLAYER.inc:166
            mm9.gosub(script, ctx, "follow_ClimbLadder") -- FOLLOWPLAYER.inc:167
        end -- FOLLOWPLAYER.inc:168
    end -- FOLLOWPLAYER.inc:169
    if ctx:condition("bPinging==1") then -- FOLLOWPLAYER.inc:171
        ctx:command("wait", "16, 2, follow_PingLoop") -- FOLLOWPLAYER.inc:172
    end -- FOLLOWPLAYER.inc:173
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:175
end

script.labels["follow_DescendLadder"] = function(ctx)
    -- FOLLOWPLAYER.inc:177
    ctx:command("bpinging", "= 0") -- FOLLOWPLAYER.inc:178
    ctx:command("setstat", "follow_hMe, Gravity, TRUE") -- FOLLOWPLAYER.inc:179
    mm9.gosub(script, ctx, "follow_DescendFinish") -- FOLLOWPLAYER.inc:180
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:181
end

script.labels["follow_DescendFinish"] = function(ctx)
    -- FOLLOWPLAYER.inc:183
    ctx:command("ontouchnotify", "follow_CheckLadder") -- FOLLOWPLAYER.inc:184
    mm9.gosub(script, ctx, "FollowStart") -- FOLLOWPLAYER.inc:185
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:186
end

script.labels["follow_ClimbLadder"] = function(ctx)
    -- FOLLOWPLAYER.inc:188
    -- LoopAnim climb, 0
    ctx:command("bpinging", "= 0") -- FOLLOWPLAYER.inc:190
    ctx:command("setstat", "follow_hMe, Gravity, FALSE") -- FOLLOWPLAYER.inc:191
    ctx:command("movedir", "0,1,0, follow_nLadderHeight, follow_nLadderHeight, follow_ClimbFinish") -- FOLLOWPLAYER.inc:192
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:193
end

script.labels["follow_ClimbFinish"] = function(ctx)
    -- FOLLOWPLAYER.inc:195
    ctx:command("stop", "") -- FOLLOWPLAYER.inc:196
    ctx:command("setstat", "follow_hPlayer, Gravity, TRUE") -- FOLLOWPLAYER.inc:197
    ctx:command("bpinging", "= 1") -- FOLLOWPLAYER.inc:198
    ctx:command("getpos", "follow_hObject, follow_x,nTemp,follow_z") -- FOLLOWPLAYER.inc:199
    ctx:command("getpos", "follow_hMe, nTemp,follow_yMe,nTemp") -- FOLLOWPLAYER.inc:200
    ctx:command("walktopos", "follow_x,follow_yMe,follow_z, 25, follow_PingLoop") -- FOLLOWPLAYER.inc:201
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:202
end

return script
