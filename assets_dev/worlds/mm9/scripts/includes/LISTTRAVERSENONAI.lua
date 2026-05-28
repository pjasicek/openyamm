-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LISTTRAVERSENONAI.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 22, path = "Flags.inc" }
script.includes[#script.includes + 1] = { line = 23, path = "ListMaker.inc" }

-- ListTraverseNONAI.inc
-- by SJR
-- 11-02-01
-- Advantages:
-- Traverses arbitrary list of markers.
-- Performs user callback at each marker.
-- Notes: (* default)
-- *	SetTraverseOnce = gosub this for one way traversal (ex 0,1,2,3)
-- SetTraverseLoop = gosub this for circular traversal (ex 0,1,2,3,0,1,2,3...)
-- SetTraversePace = gosub this for back and forth (ex 0,1,2,3,2,1,0...)
-- LISTNAME = base name of item list (ex "MyMarker" for MyMarker0,1,2...)
-- LISTFIRST= index of first marker of your path (ex 5 for path MyMarker5->MyMarker9)
-- LISTLAST = index of last marker of your path (ex 9 for path MyMarker5->MyMarker9)
-- Script will call "OnTraverseDone" at each marker. Override it.
-- Check the number LISTINDEX in OnTraverseDone to decide what to do.
-- inputs
-- bool for looping path
-- bool for back and forth
-- bool for back and forth
-- bool for direction
-- bool for active
-- bool for pause state
script.labels["TraverseBegin"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:44
    -- starts moving to first object,
    -- sets up collision handling
    ctx:command("getmyhandle", "traverse_hMe") -- LISTTRAVERSENONAI.inc:48
    if ctx:condition("LISTFIRST>LISTLAST") then -- LISTTRAVERSENONAI.inc:50
        -- if user reversed indexes, switch back
        ctx:command("traverse_ntemp", "= LISTFIRST") -- LISTTRAVERSENONAI.inc:52
        ctx:command("listfirst", "= LISTLAST") -- LISTTRAVERSENONAI.inc:53
        ctx:command("listlast", "= traverse_nTemp") -- LISTTRAVERSENONAI.inc:54
    end -- LISTTRAVERSENONAI.inc:55
    ctx:command("bcontinue", "= 1") -- LISTTRAVERSENONAI.inc:56
    ctx:command("listindex", "= LISTLAST") -- LISTTRAVERSENONAI.inc:57
    mm9.gosub(script, ctx, "traverse_GoToNext") -- LISTTRAVERSENONAI.inc:58
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:59
end

script.labels["TraversePause"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:62
    -- pauses path, remembers place
    ctx:command("bpaused", "= 1") -- LISTTRAVERSENONAI.inc:65
    ctx:command("stop", "") -- LISTTRAVERSENONAI.inc:66
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:67
end

script.labels["TraverseResume"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:70
    -- resumes path where left off
    ctx:command("bpaused", "= 0") -- LISTTRAVERSENONAI.inc:73
    mm9.gosub(script, ctx, "traverse_Traverse") -- LISTTRAVERSENONAI.inc:74
    mm9.gosub(script, ctx, "traverse_CheckLocation") -- LISTTRAVERSENONAI.inc:75
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:76
end

script.labels["ReversePath"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:79
    -- reverses direction of path
    ctx:command("bforward", "= 1 - bForward") -- LISTTRAVERSENONAI.inc:82
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:83
end

script.labels["OnTraverseDone"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:86
    -- override this to do things
    -- on the way, called at every marker
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:90
end

script.labels["SetTraverseLoop"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:93
    -- loop pathing until user stop
    ctx:command("traverseloop", "= 1") -- LISTTRAVERSENONAI.inc:96
    ctx:command("traversepace", "= 0") -- LISTTRAVERSENONAI.inc:97
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:98
end

script.labels["SetTraversePace"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:101
    -- back and forth until user stop
    ctx:command("traverseloop", "= 0") -- LISTTRAVERSENONAI.inc:104
    ctx:command("traversepace", "= 1") -- LISTTRAVERSENONAI.inc:105
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:106
end

script.labels["SetTraverseOnce"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:109
    -- do one trip at a time
    ctx:command("traverseloop", "= 0") -- LISTTRAVERSENONAI.inc:112
    ctx:command("traversepace", "= 0") -- LISTTRAVERSENONAI.inc:113
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:114
end

-- private
script.labels["traverse_GoToNext"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:123
    if ctx:condition("bContinue==0") then -- LISTTRAVERSENONAI.inc:124
        do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:125
    end -- LISTTRAVERSENONAI.inc:126
    if ctx:condition("bForward==1") then -- LISTTRAVERSENONAI.inc:127
        mm9.gosub(script, ctx, "GetNextObject") -- LISTTRAVERSENONAI.inc:128
    else -- LISTTRAVERSENONAI.inc:129
        mm9.gosub(script, ctx, "GetPreviousObject") -- LISTTRAVERSENONAI.inc:130
    end -- LISTTRAVERSENONAI.inc:131
    if ctx:condition("bPaused==0") then -- LISTTRAVERSENONAI.inc:132
        mm9.gosub(script, ctx, "traverse_Traverse") -- LISTTRAVERSENONAI.inc:133
        mm9.gosub(script, ctx, "traverse_CheckLocation") -- LISTTRAVERSENONAI.inc:134
    end -- LISTTRAVERSENONAI.inc:135
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:136
end

script.labels["traverse_Traverse"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:138
    ctx:command("getpos", "LISTOBJECT, traverse_x,traverse_y,traverse_z") -- LISTTRAVERSENONAI.inc:139
    ctx:command("movetopos", "traverse_x,traverse_y,traverse_z, TRAVERSE_SPEED, traverse_TraverseTick") -- LISTTRAVERSENONAI.inc:140
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:141
end

script.labels["traverse_TraverseTick"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:143
    mm9.gosub(script, ctx, "OnTraverseDone") -- LISTTRAVERSENONAI.inc:144
    mm9.gosub(script, ctx, "traverse_GoToNext") -- LISTTRAVERSENONAI.inc:145
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:146
end

script.labels["traverse_CheckLocation"] = function(ctx)
    -- LISTTRAVERSENONAI.inc:148
    ctx:command("bcontinue", "= 1") -- LISTTRAVERSENONAI.inc:149
    if ctx:condition("TRAVERSELOOP==1") then -- LISTTRAVERSENONAI.inc:150
        do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:151
    end -- LISTTRAVERSENONAI.inc:152
    if ctx:condition("ARRIVEDLAST==1") then -- LISTTRAVERSENONAI.inc:153
        if ctx:condition("bForward==1") then -- LISTTRAVERSENONAI.inc:154
            ctx:command("bcontinue", "= TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSENONAI.inc:155
        end -- LISTTRAVERSENONAI.inc:156
        ctx:command("bforward", "= 0") -- LISTTRAVERSENONAI.inc:157
    end -- LISTTRAVERSENONAI.inc:158
    if ctx:condition("ARRIVEDFIRST==1") then -- LISTTRAVERSENONAI.inc:159
        if ctx:condition("bForward==0") then -- LISTTRAVERSENONAI.inc:160
            ctx:command("bcontinue", "= TRAVERSELOOP + TRAVERSEPACE") -- LISTTRAVERSENONAI.inc:161
        end -- LISTTRAVERSENONAI.inc:162
        ctx:command("bforward", "= 1") -- LISTTRAVERSENONAI.inc:163
    end -- LISTTRAVERSENONAI.inc:164
    do return ctx:exit(1) end -- LISTTRAVERSENONAI.inc:165
end

return script
