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
    ctx:state().follow_hMe = ctx:self() -- FOLLOWPLAYER.inc:31
    ctx:addTrigger("Use", "FollowOnUse") -- FOLLOWPLAYER.inc:33
    ctx:addTrigger("Follow", "FollowStart") -- FOLLOWPLAYER.inc:34
    ctx:addTrigger("Halt", "FollowStop") -- FOLLOWPLAYER.inc:35
    ctx:onEvent("OnTouchNotify", "follow_CheckLadder") -- FOLLOWPLAYER.inc:37
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:39
end

script.labels["FollowStart"] = function(ctx)
    -- FOLLOWPLAYER.inc:42
    -- follow player
    ctx:wait(16, 0, "DoNothing") -- FOLLOWPLAYER.inc:45
    ctx:state().follow_hPlayer = ctx:player() -- FOLLOWPLAYER.inc:46
    ctx:state().follow_hMe = ctx:self() -- FOLLOWPLAYER.inc:47
    ctx:state().follow_bFollowing = 1 -- FOLLOWPLAYER.inc:49
    mm9.gosub(script, ctx, "FollowLoop") -- FOLLOWPLAYER.inc:51
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:53
end

script.labels["FollowStop"] = function(ctx)
    -- FOLLOWPLAYER.inc:56
    -- pause following
    ctx:wait(16, 0, "DoNothing") -- FOLLOWPLAYER.inc:59
    ctx:self():stop() -- FOLLOWPLAYER.inc:60
    ctx:state().follow_bFollowing = 0 -- FOLLOWPLAYER.inc:61
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:63
end

script.labels["FollowResume"] = function(ctx)
    -- FOLLOWPLAYER.inc:66
    -- follow player
    if ctx:condition("follow_hPlayer!=0") then -- FOLLOWPLAYER.inc:69
        ctx:state().follow_bFollowing = 1 -- FOLLOWPLAYER.inc:71
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
    ctx:state().follow_ds = ctx:self():aiDistanceTo(ctx:object("follow_hPlayer")) -- FOLLOWPLAYER.inc:91
    -- run radius
    if ctx:condition("follow_ds>200") then -- FOLLOWPLAYER.inc:93
        ctx:self():runTo(ctx:object("follow_hPlayer"), 32, "FollowDone") -- FOLLOWPLAYER.inc:94
    else -- FOLLOWPLAYER.inc:95
        -- walk radius
        if ctx:condition("follow_ds>100") then -- FOLLOWPLAYER.inc:97
            ctx:self():walkTo(ctx:object("follow_hPlayer"), 32, "FollowDone") -- FOLLOWPLAYER.inc:98
        else -- FOLLOWPLAYER.inc:99
            ctx:self():setIdle() -- FOLLOWPLAYER.inc:100
            mm9.gosub(script, ctx, "OnFollowDone") -- FOLLOWPLAYER.inc:101
        end -- FOLLOWPLAYER.inc:102
    end -- FOLLOWPLAYER.inc:103
    -- refresh action every 3 secs
    ctx:wait(16, 3, "FollowLoop") -- FOLLOWPLAYER.inc:105
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
    ctx:state().follow_bFollowing = 1 -- FOLLOWPLAYER.inc:115
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
    ctx:state().follow_sObjectName = ctx:object("follow_hObject"):className() -- FOLLOWPLAYER.inc:136
    if ctx:condition("follow_sObjectName==\"Ladder\"") then -- FOLLOWPLAYER.inc:137
        ctx:state().nTemp, ctx:state().LADDER_HEIGHT, ctx:state().nTemp = ctx:object("follow_hObject"):dims() -- FOLLOWPLAYER.inc:138
        ctx:state().bPinging = 1 -- FOLLOWPLAYER.inc:139
        mm9.gosub(script, ctx, "FollowStop") -- FOLLOWPLAYER.inc:140
        mm9.gosub(script, ctx, "follow_PingLoop") -- FOLLOWPLAYER.inc:141
        ctx:onEvent("OnTouchNotify", "DoNothing") -- FOLLOWPLAYER.inc:142
    end -- FOLLOWPLAYER.inc:143
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:145
end

script.labels["follow_PingLoop"] = function(ctx)
    -- FOLLOWPLAYER.inc:147
    ctx:state().nTemp, ctx:state().follow_y, ctx:state().nTemp = ctx:object("follow_hPlayer"):pos() -- FOLLOWPLAYER.inc:148
    ctx:state().nTemp, ctx:state().follow_yMe, ctx:state().nTemp = ctx:object("follow_hMe"):pos() -- FOLLOWPLAYER.inc:149
    ctx:set("follow_nLadderHeight", "2 * LADDER_HEIGHT + LADDER_GAP") -- FOLLOWPLAYER.inc:151
    ctx:set("nTemp", "follow_y - follow_yMe") -- FOLLOWPLAYER.inc:152
    if ctx:condition("nTemp<0") then -- FOLLOWPLAYER.inc:153
        ctx:set("nTemp", "nTemp * -1") -- FOLLOWPLAYER.inc:154
    end -- FOLLOWPLAYER.inc:155
    -- cprint ping...
    -- cprint follow_nLadderHeight
    -- cprint nTemp
    -- cprint ************
    if ctx:condition("nTemp<LADDER_GAP") then -- FOLLOWPLAYER.inc:160
        mm9.gosub(script, ctx, "follow_DescendLadder") -- FOLLOWPLAYER.inc:161
    else -- FOLLOWPLAYER.inc:162
        ctx:set("nTemp", "follow_y - follow_yMe") -- FOLLOWPLAYER.inc:163
        if ctx:condition("nTemp<0") then -- FOLLOWPLAYER.inc:164
            mm9.gosub(script, ctx, "follow_DescendLadder") -- FOLLOWPLAYER.inc:165
        else -- FOLLOWPLAYER.inc:166
            mm9.gosub(script, ctx, "follow_ClimbLadder") -- FOLLOWPLAYER.inc:167
        end -- FOLLOWPLAYER.inc:168
    end -- FOLLOWPLAYER.inc:169
    if ctx:condition("bPinging==1") then -- FOLLOWPLAYER.inc:171
        ctx:wait(16, 2, "follow_PingLoop") -- FOLLOWPLAYER.inc:172
    end -- FOLLOWPLAYER.inc:173
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:175
end

script.labels["follow_DescendLadder"] = function(ctx)
    -- FOLLOWPLAYER.inc:177
    ctx:state().bPinging = 0 -- FOLLOWPLAYER.inc:178
    ctx:object("follow_hMe"):setStat("Gravity", "TRUE") -- FOLLOWPLAYER.inc:179
    mm9.gosub(script, ctx, "follow_DescendFinish") -- FOLLOWPLAYER.inc:180
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:181
end

script.labels["follow_DescendFinish"] = function(ctx)
    -- FOLLOWPLAYER.inc:183
    ctx:onEvent("OnTouchNotify", "follow_CheckLadder") -- FOLLOWPLAYER.inc:184
    mm9.gosub(script, ctx, "FollowStart") -- FOLLOWPLAYER.inc:185
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:186
end

script.labels["follow_ClimbLadder"] = function(ctx)
    -- FOLLOWPLAYER.inc:188
    -- LoopAnim climb, 0
    ctx:state().bPinging = 0 -- FOLLOWPLAYER.inc:190
    ctx:object("follow_hMe"):setStat("Gravity", "FALSE") -- FOLLOWPLAYER.inc:191
    ctx:self():moveDir(0, 1, 0, "follow_nLadderHeight", "follow_nLadderHeight", "follow_ClimbFinish") -- FOLLOWPLAYER.inc:192
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:193
end

script.labels["follow_ClimbFinish"] = function(ctx)
    -- FOLLOWPLAYER.inc:195
    ctx:self():stop() -- FOLLOWPLAYER.inc:196
    ctx:object("follow_hPlayer"):setStat("Gravity", "TRUE") -- FOLLOWPLAYER.inc:197
    ctx:state().bPinging = 1 -- FOLLOWPLAYER.inc:198
    ctx:state().follow_x, ctx:state().nTemp, ctx:state().follow_z = ctx:object("follow_hObject"):pos() -- FOLLOWPLAYER.inc:199
    ctx:state().nTemp, ctx:state().follow_yMe, ctx:state().nTemp = ctx:object("follow_hMe"):pos() -- FOLLOWPLAYER.inc:200
    ctx:self():walkToPos("follow_x", "follow_yMe", "follow_z", 25, "follow_PingLoop") -- FOLLOWPLAYER.inc:201
    do return ctx:exit(1) end -- FOLLOWPLAYER.inc:202
end

return script
