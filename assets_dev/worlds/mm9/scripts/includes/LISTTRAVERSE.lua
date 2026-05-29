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
    ctx:state().traverse_hMe = ctx:self() -- LISTTRAVERSE.inc:55
    ctx:onEvent("OnDoor", "traverse_TraverseDoor") -- LISTTRAVERSE.inc:56
    if ctx:condition("LISTFIRST>LISTLAST") then -- LISTTRAVERSE.inc:57
        -- if user reversed indexes, switch back
        ctx:set("traverse_nTemp", "LISTFIRST") -- LISTTRAVERSE.inc:59
        ctx:set("LISTFIRST", "LISTLAST") -- LISTTRAVERSE.inc:60
        ctx:set("LISTLAST", "traverse_nTemp") -- LISTTRAVERSE.inc:61
    end -- LISTTRAVERSE.inc:62
    ctx:state().bContinue = 1 -- LISTTRAVERSE.inc:63
    ctx:set("LISTINDEX", "LISTLAST") -- LISTTRAVERSE.inc:64
    mm9.gosub(script, ctx, "traverse_GoToNext") -- LISTTRAVERSE.inc:65
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:66
end

script.labels["TraversePause"] = function(ctx)
    -- LISTTRAVERSE.inc:69
    -- pauses path, remembers place
    ctx:state().bPaused = 1 -- LISTTRAVERSE.inc:72
    ctx:self():stop() -- LISTTRAVERSE.inc:73
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:74
end

script.labels["TraverseResume"] = function(ctx)
    -- LISTTRAVERSE.inc:77
    -- resumes path where left off
    ctx:state().bPaused = 0 -- LISTTRAVERSE.inc:80
    mm9.gosub(script, ctx, "traverse_Traverse") -- LISTTRAVERSE.inc:81
    mm9.gosub(script, ctx, "traverse_CheckLocation") -- LISTTRAVERSE.inc:82
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:83
end

script.labels["ReversePath"] = function(ctx)
    -- LISTTRAVERSE.inc:86
    -- reverses direction of path
    ctx:set("bForward", "1 - bForward") -- LISTTRAVERSE.inc:89
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
    ctx:state().TRAVERSERUN = 1 -- LISTTRAVERSE.inc:103
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:104
end

script.labels["SetTraverseWalk"] = function(ctx)
    -- LISTTRAVERSE.inc:107
    -- disable running
    ctx:state().TRAVERSERUN = 0 -- LISTTRAVERSE.inc:110
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:111
end

script.labels["SetTraverseLoop"] = function(ctx)
    -- LISTTRAVERSE.inc:114
    -- loop pathing until user stop
    ctx:state().TRAVERSELOOP = 1 -- LISTTRAVERSE.inc:117
    ctx:state().TRAVERSEPACE = 0 -- LISTTRAVERSE.inc:118
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:119
end

script.labels["SetTraversePace"] = function(ctx)
    -- LISTTRAVERSE.inc:122
    -- back and forth until user stop
    ctx:state().TRAVERSELOOP = 0 -- LISTTRAVERSE.inc:125
    ctx:state().TRAVERSEPACE = 1 -- LISTTRAVERSE.inc:126
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:127
end

script.labels["SetTraverseOnce"] = function(ctx)
    -- LISTTRAVERSE.inc:130
    -- do one trip at a time
    ctx:state().TRAVERSELOOP = 0 -- LISTTRAVERSE.inc:133
    ctx:state().TRAVERSEPACE = 0 -- LISTTRAVERSE.inc:134
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:135
end

script.labels["SetTraverseDefaults"] = function(ctx)
    -- LISTTRAVERSE.inc:138
    -- restore all the defaults
    ctx:state().TRAVERSELOOP = 0 -- LISTTRAVERSE.inc:141
    ctx:state().TRAVERSEPACE = 0 -- LISTTRAVERSE.inc:142
    ctx:state().TRAVERSERADIUS = 40 -- LISTTRAVERSE.inc:143
    ctx:state().TRAVERSERUN = 0 -- LISTTRAVERSE.inc:144
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
        ctx:self():runTo(ctx:object("LISTOBJECT"), "TRAVERSERADIUS", "traverse_TraverseTick") -- LISTTRAVERSE.inc:172
    else -- LISTTRAVERSE.inc:173
        ctx:self():walkTo(ctx:object("LISTOBJECT"), "TRAVERSERADIUS", "traverse_TraverseTick") -- LISTTRAVERSE.inc:174
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
    ctx:state().bContinue = 1 -- LISTTRAVERSE.inc:184
    if ctx:condition("TRAVERSELOOP==1") then -- LISTTRAVERSE.inc:185
        do return ctx:exit(1) end -- LISTTRAVERSE.inc:186
    end -- LISTTRAVERSE.inc:187
    if ctx:condition("ARRIVEDLAST==1") then -- LISTTRAVERSE.inc:188
        if ctx:condition("bForward==1") then -- LISTTRAVERSE.inc:189
            ctx:set("bContinue", "TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSE.inc:190
        end -- LISTTRAVERSE.inc:191
        ctx:state().bForward = 0 -- LISTTRAVERSE.inc:192
    end -- LISTTRAVERSE.inc:193
    if ctx:condition("ARRIVEDFIRST==1") then -- LISTTRAVERSE.inc:194
        if ctx:condition("bForward==0") then -- LISTTRAVERSE.inc:195
            ctx:set("bContinue", "TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSE.inc:196
        end -- LISTTRAVERSE.inc:197
        ctx:state().bForward = 1 -- LISTTRAVERSE.inc:198
    end -- LISTTRAVERSE.inc:199
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:200
end

-- Modified baseDoor.inc routine to cooperate(!) with this script
script.labels["traverse_TraverseDoor"] = function(ctx)
    -- LISTTRAVERSE.inc:214
    mm9.gosub(script, ctx, "TraversePause") -- LISTTRAVERSE.inc:216
    ctx:getParam(0, "traverse_hDoor") -- LISTTRAVERSE.inc:218
    ctx:state().traverse_nTemp = ctx:object("traverse_hDoor"):getStat("IsClosed") -- LISTTRAVERSE.inc:219
    if ctx:condition("traverse_nTemp==0") then -- LISTTRAVERSE.inc:221
        mm9.gosub(script, ctx, "TraverseResume") -- LISTTRAVERSE.inc:222
        do return ctx:exit(0) end -- LISTTRAVERSE.inc:223
    end -- LISTTRAVERSE.inc:224
    ctx:getParam(1, "traverse_normalX") -- LISTTRAVERSE.inc:226
    ctx:getParam(2, "traverse_normalY") -- LISTTRAVERSE.inc:227
    ctx:getParam(3, "traverse_normalZ") -- LISTTRAVERSE.inc:228
    ctx:state().traverse_normalX, ctx:state().traverse_normalY, ctx:state().traverse_normalZ = ctx:rotateDir("traverse_normalX", "traverse_normalY", "traverse_normalZ", 180) -- LISTTRAVERSE.inc:229
    ctx:state().traverse_velX, ctx:state().traverse_velY, ctx:state().traverse_velZ = ctx:object("traverse_hMe"):rotation() -- LISTTRAVERSE.inc:231
    ctx:state().traverse_nTemp = ctx:vecAngle("traverse_normalX", 0, "traverse_normalZ", "traverse_velX", 0, "traverse_velZ") -- LISTTRAVERSE.inc:233
    if ctx:condition("traverse_nTemp > 45") then -- LISTTRAVERSE.inc:234
        do return ctx:exit(0) end -- LISTTRAVERSE.inc:235
    end -- LISTTRAVERSE.inc:236
    ctx:self():stop() -- LISTTRAVERSE.inc:237
    ctx:self():faceDir("traverse_normalX", 0, "traverse_normalZ", 360) -- LISTTRAVERSE.inc:238
    ctx:trigger("traverse_hDoor", "Use") -- LISTTRAVERSE.inc:239
    ctx:state().traverse_nTemp = ctx:object("traverse_hDoor"):getStat("DoorOpenTime") -- LISTTRAVERSE.inc:240
    ctx:wait(0, "traverse_nTemp", "TraverseResume") -- LISTTRAVERSE.inc:241
    do return ctx:exit(1) end -- LISTTRAVERSE.inc:243
end

return script
