-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LISTTRAVERSE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 28, path = "ListMaker.inc" }

-- ListTraverse.inc
-- by SJR
-- 11-02-01
-- Advantages:
-- Traverses arbitrary list of markers.
-- Performs user callback at each marker.
-- Handles doors easily.
-- Notes: (* default)
-- *	SetTraverseWalk = gosub this for walking
-- SetTraverseRun  = gosub this for running
-- *	SetTraverseOnce = gosub this for one way traversal (ex 0,1,2,3)
-- SetTraverseLoop = gosub this for circular traversal (ex 0,1,2,3,0,1,2,3...)
-- SetTraversePace = gosub this for back and forth (ex 0,1,2,3,2,1,0...)
-- *	SetTraverseDefaults = gosub this to restore defaults
-- LISTNAME = base name of item list (ex "MyMarker" for MyMarker0,1,2...)
-- LISTFIRST= index of first marker of your path (ex 5 for path MyMarker5->MyMarker9)
-- LISTLAST = index of last marker of your path (ex 9 for path MyMarker5->MyMarker9)
-- Script will call "OnTraverseDone" at each marker. Override it.
-- Check the number LISTINDEX in OnTraverseDone to decide what to do.
-- Change 'TRAVERSERADIUS' to a suitable Walk\Run radius (defaults to 40)
-- inputs
-- bool for run
-- bool for looping path
-- bool for back and forth
-- radius of runto, walkto
-- bool for direction
-- bool for active
-- bool for pause state
script.labels["TraverseBegin"] = function(ctx)
    -- LISTTRAVERSE.inc:51
    -- starts walk\running from first object,
    -- sets up door handling
    ctx:command("getmyhandle", "traverse_hMe") -- LISTTRAVERSE.inc:55
    ctx:command("ondoor", "traverse_TraverseDoor") -- LISTTRAVERSE.inc:56
    if ctx:condition("LISTFIRST>LISTLAST") then -- LISTTRAVERSE.inc:57
        -- if user reversed indexes, switch back
        ctx:command("traverse_ntemp", "= LISTFIRST") -- LISTTRAVERSE.inc:59
        ctx:command("listfirst", "= LISTLAST") -- LISTTRAVERSE.inc:60
        ctx:command("listlast", "= traverse_nTemp") -- LISTTRAVERSE.inc:61
    end -- LISTTRAVERSE.inc:62
    ctx:command("bcontinue", "= 1") -- LISTTRAVERSE.inc:63
    ctx:command("listindex", "= LISTLAST") -- LISTTRAVERSE.inc:64
    mm9.gosub(script, ctx, "traverse_GoToNext") -- LISTTRAVERSE.inc:65
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:66
end

script.labels["TraversePause"] = function(ctx)
    -- LISTTRAVERSE.inc:69
    -- pauses path, remembers place
    ctx:command("bpaused", "= 1") -- LISTTRAVERSE.inc:72
    ctx:command("stop", "") -- LISTTRAVERSE.inc:73
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:74
end

script.labels["TraverseResume"] = function(ctx)
    -- LISTTRAVERSE.inc:77
    -- resumes path where left off
    ctx:command("bpaused", "= 0") -- LISTTRAVERSE.inc:80
    mm9.gosub(script, ctx, "traverse_Traverse") -- LISTTRAVERSE.inc:81
    mm9.gosub(script, ctx, "traverse_CheckLocation") -- LISTTRAVERSE.inc:82
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:83
end

script.labels["ReversePath"] = function(ctx)
    -- LISTTRAVERSE.inc:86
    -- reverses direction of path
    ctx:command("bforward", "= 1 - bForward") -- LISTTRAVERSE.inc:89
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:90
end

script.labels["OnTraverseDone"] = function(ctx)
    -- LISTTRAVERSE.inc:93
    -- override this to do things
    -- on the way, called at every marker
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:97
end

script.labels["SetTraverseRun"] = function(ctx)
    -- LISTTRAVERSE.inc:100
    -- enable running
    ctx:command("traverserun", "= 1") -- LISTTRAVERSE.inc:103
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:104
end

script.labels["SetTraverseWalk"] = function(ctx)
    -- LISTTRAVERSE.inc:107
    -- disable running
    ctx:command("traverserun", "= 0") -- LISTTRAVERSE.inc:110
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:111
end

script.labels["SetTraverseLoop"] = function(ctx)
    -- LISTTRAVERSE.inc:114
    -- loop pathing until user stop
    ctx:command("traverseloop", "= 1") -- LISTTRAVERSE.inc:117
    ctx:command("traversepace", "= 0") -- LISTTRAVERSE.inc:118
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:119
end

script.labels["SetTraversePace"] = function(ctx)
    -- LISTTRAVERSE.inc:122
    -- back and forth until user stop
    ctx:command("traverseloop", "= 0") -- LISTTRAVERSE.inc:125
    ctx:command("traversepace", "= 1") -- LISTTRAVERSE.inc:126
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:127
end

script.labels["SetTraverseOnce"] = function(ctx)
    -- LISTTRAVERSE.inc:130
    -- do one trip at a time
    ctx:command("traverseloop", "= 0") -- LISTTRAVERSE.inc:133
    ctx:command("traversepace", "= 0") -- LISTTRAVERSE.inc:134
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:135
end

script.labels["SetTraverseDefaults"] = function(ctx)
    -- LISTTRAVERSE.inc:138
    -- restore all the defaults
    ctx:command("traverseloop", "= 0") -- LISTTRAVERSE.inc:141
    ctx:command("traversepace", "= 0") -- LISTTRAVERSE.inc:142
    ctx:command("traverseradius", "= 40") -- LISTTRAVERSE.inc:143
    ctx:command("traverserun", "= 0") -- LISTTRAVERSE.inc:144
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:145
end

-- private
-- keep out! do not screw with these.
script.labels["traverse_GoToNext"] = function(ctx)
    -- LISTTRAVERSE.inc:155
    if ctx:condition("bContinue==0") then -- LISTTRAVERSE.inc:156
        do return ctx:exit(1) end -- LISTTRAVERSE.inc:157
    end -- LISTTRAVERSE.inc:158
    if ctx:condition("bForward==1") then -- LISTTRAVERSE.inc:159
        mm9.gosub(script, ctx, "GetNextObject") -- LISTTRAVERSE.inc:160
    else -- LISTTRAVERSE.inc:161
        mm9.gosub(script, ctx, "GetPreviousObject") -- LISTTRAVERSE.inc:162
    end -- LISTTRAVERSE.inc:163
    if ctx:condition("bPaused==0") then -- LISTTRAVERSE.inc:164
        mm9.gosub(script, ctx, "traverse_Traverse") -- LISTTRAVERSE.inc:165
        mm9.gosub(script, ctx, "traverse_CheckLocation") -- LISTTRAVERSE.inc:166
    end -- LISTTRAVERSE.inc:167
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:168
end

script.labels["traverse_Traverse"] = function(ctx)
    -- LISTTRAVERSE.inc:170
    if ctx:condition("TRAVERSERUN==1") then -- LISTTRAVERSE.inc:171
        ctx:command("runto", "LISTOBJECT, TRAVERSERADIUS, traverse_TraverseTick") -- LISTTRAVERSE.inc:172
    else -- LISTTRAVERSE.inc:173
        ctx:command("walkto", "LISTOBJECT, TRAVERSERADIUS, traverse_TraverseTick") -- LISTTRAVERSE.inc:174
    end -- LISTTRAVERSE.inc:175
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:176
end

script.labels["traverse_TraverseTick"] = function(ctx)
    -- LISTTRAVERSE.inc:178
    mm9.gosub(script, ctx, "OnTraverseDone") -- LISTTRAVERSE.inc:179
    mm9.gosub(script, ctx, "traverse_GoToNext") -- LISTTRAVERSE.inc:180
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:181
end

script.labels["traverse_CheckLocation"] = function(ctx)
    -- LISTTRAVERSE.inc:183
    ctx:command("bcontinue", "= 1") -- LISTTRAVERSE.inc:184
    if ctx:condition("TRAVERSELOOP==1") then -- LISTTRAVERSE.inc:185
        do return ctx:exit(1) end -- LISTTRAVERSE.inc:186
    end -- LISTTRAVERSE.inc:187
    if ctx:condition("ARRIVEDLAST==1") then -- LISTTRAVERSE.inc:188
        if ctx:condition("bForward==1") then -- LISTTRAVERSE.inc:189
            ctx:command("bcontinue", "= TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSE.inc:190
        end -- LISTTRAVERSE.inc:191
        ctx:command("bforward", "= 0") -- LISTTRAVERSE.inc:192
    end -- LISTTRAVERSE.inc:193
    if ctx:condition("ARRIVEDFIRST==1") then -- LISTTRAVERSE.inc:194
        if ctx:condition("bForward==0") then -- LISTTRAVERSE.inc:195
            ctx:command("bcontinue", "= TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSE.inc:196
        end -- LISTTRAVERSE.inc:197
        ctx:command("bforward", "= 1") -- LISTTRAVERSE.inc:198
    end -- LISTTRAVERSE.inc:199
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:200
end

-- Modified baseDoor.inc routine to cooperate(!) with this script
script.labels["traverse_TraverseDoor"] = function(ctx)
    -- LISTTRAVERSE.inc:214
    mm9.gosub(script, ctx, "TraversePause") -- LISTTRAVERSE.inc:216
    ctx:getParam(0, "traverse_hDoor") -- LISTTRAVERSE.inc:218
    ctx:command("getstat", "traverse_hDoor,IsClosed,traverse_nTemp") -- LISTTRAVERSE.inc:219
    if ctx:condition("traverse_nTemp==0") then -- LISTTRAVERSE.inc:221
        mm9.gosub(script, ctx, "TraverseResume") -- LISTTRAVERSE.inc:222
        do return ctx:exit(0) end -- LISTTRAVERSE.inc:223
    end -- LISTTRAVERSE.inc:224
    ctx:getParam(1, "traverse_normalX") -- LISTTRAVERSE.inc:226
    ctx:getParam(2, "traverse_normalY") -- LISTTRAVERSE.inc:227
    ctx:getParam(3, "traverse_normalZ") -- LISTTRAVERSE.inc:228
    ctx:command("rotatedir", "traverse_normalX, traverse_normalY, traverse_normalZ, 180") -- LISTTRAVERSE.inc:229
    ctx:command("getfacedir", "traverse_hMe, traverse_velX, traverse_velY, traverse_velZ") -- LISTTRAVERSE.inc:231
    ctx:command("vecangle", "traverse_normalX,0,traverse_normalZ,traverse_velX,0,traverse_velZ, traverse_nTemp") -- LISTTRAVERSE.inc:233
    if ctx:condition("traverse_nTemp > 45") then -- LISTTRAVERSE.inc:234
        do return ctx:exit(0) end -- LISTTRAVERSE.inc:235
    end -- LISTTRAVERSE.inc:236
    ctx:command("stop", "") -- LISTTRAVERSE.inc:237
    ctx:command("facedir", "traverse_normalX, 0, traverse_normalZ, 360") -- LISTTRAVERSE.inc:238
    ctx:trigger("traverse_hDoor", "Use") -- LISTTRAVERSE.inc:239
    ctx:command("getstat", "traverse_hDoor,DoorOpenTime,traverse_nTemp") -- LISTTRAVERSE.inc:240
    ctx:command("wait", "0, traverse_nTemp, TraverseResume") -- LISTTRAVERSE.inc:241
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:243
end

return script
