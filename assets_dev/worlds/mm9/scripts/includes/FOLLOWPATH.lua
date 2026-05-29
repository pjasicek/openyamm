-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FOLLOWPATH.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 25, path = "globals.inc" }

-- FollowPath.inc
-- Jeff Leggett
-- 11/09/1999
-- This include file can be used to have your object
-- (typically a camera) follow a path.  Your object will
-- use both the positional information and rotation information
-- stored in the path you pass to it.
-- Usage:
-- gosub FollowPathInit
-- Set g_sFollowPathName, <Your Path Name Here>
-- Set g_nFollowPathSpeed, < Your speed here>
-- Set g_nFollowPathCallback, < Callback # to use when we reach a marker>
-- Set g_nFollowPathDoneCallback, <callback# to use when path is done>
-- Set g_nFollowPathLoops, 1
-- SetCallback g_nFollowPath
-- gosub FollowPath
-- globals that other scripts can/should use
-- You may check what path # we are currently
-- heading for with this variable
-- local variables that only this script should use
script.labels["FollowPathInit"] = function(ctx)
    -- FOLLOWPATH.inc:50
    -- Default to NOT doing any callbacks
    ctx:state().g_nFollowPathCallback = -1 -- FOLLOWPATH.inc:54
    ctx:state().g_nFollowPathDoneCallback = -1 -- FOLLOWPATH.inc:55
    ctx:state().g_nFollowPathLoops = 1 -- FOLLOWPATH.inc:58
    ctx:onEvent("OnPlayerInterrupt", "FollowPathPlayerInterrupt") -- FOLLOWPATH.inc:60
    do return ctx:exit("") end -- FOLLOWPATH.inc:62
end

script.labels["FollowPath"] = function(ctx)
    -- FOLLOWPATH.inc:65
    -- Prior to calling this routine, you need to setup the following
    -- global variables:
    -- g_sFollowPathName		-> name of path to follow
    -- g_nFollowPathSpeed		-> Speed object should follow path
    ctx:state().g_nFollowPathNbr = 0 -- FOLLOWPATH.inc:75
    ctx:state().nFollowPathCount = 0 -- FOLLOWPATH.inc:76
    mm9.gosub(script, ctx, "FollowPathGetPathCount") -- FOLLOWPATH.inc:78
    if ctx:condition("nFollowPathCount==0") then -- FOLLOWPATH.inc:80
        do return ctx:exit(0) end -- FOLLOWPATH.inc:81
    end -- FOLLOWPATH.inc:82
    mm9.gosub(script, ctx, "FollowPathFirst") -- FOLLOWPATH.inc:84
    do return ctx:exit(1) end -- FOLLOWPATH.inc:86
end

script.labels["FollowPathGetCurrHandle"] = function(ctx)
    -- FOLLOWPATH.inc:89
    -- Gets handle to current path marker...
    ctx:set("sFollowPathTemp", "g_sFollowPathName") -- FOLLOWPATH.inc:93
    ctx:add("sFollowPathTemp", "g_nFollowPathNbr") -- FOLLOWPATH.inc:94
    ctx:state().hFollowPathObject = ctx:objectOrNil("sFollowPathTemp") -- FOLLOWPATH.inc:96
    do return ctx:exit("") end -- FOLLOWPATH.inc:98
end

script.labels["FollowPathFirst"] = function(ctx)
    -- FOLLOWPATH.inc:101
    ctx:state().g_nFollowPathNbr = 0 -- FOLLOWPATH.inc:104
    ctx:state().nFollowPathLoopCount = 0 -- FOLLOWPATH.inc:105
    mm9.gosub(script, ctx, "FollowPathGetCurrHandle") -- FOLLOWPATH.inc:106
    mm9.gosub(script, ctx, "FollowPathMove") -- FOLLOWPATH.inc:107
    do return ctx:exit("") end -- FOLLOWPATH.inc:109
end

script.labels["FollowPathNext"] = function(ctx)
    -- FOLLOWPATH.inc:112
    -- Finds next path name and follows it
    -- Let the path object know were here
    ctx:trigger("hFollowPathObject", "Trigger") -- FOLLOWPATH.inc:117
    ctx:state().g_nFollowPathNbr = (tonumber(ctx:state().g_nFollowPathNbr) or 0) + 1 -- FOLLOWPATH.inc:119
    -- DebugOut ---Follow Path Number----
    -- DebugOut g_nFollowPathNbr
    -- DebugOut ---Follow Path Count---
    -- DebugOut nFollowPathCount
    if ctx:condition("g_nFollowPathNbr >= nFollowPathCount") then -- FOLLOWPATH.inc:127
        ctx:state().nFollowPathLoopCount = (tonumber(ctx:state().nFollowPathLoopCount) or 0) + 1 -- FOLLOWPATH.inc:128
        if ctx:condition("nFollowPathLoopCount >= g_nFollowPathLoops") then -- FOLLOWPATH.inc:130
            -- we're done!
            -- DebugOut ---Follow Path Number----
            -- DebugOut g_nFollowPathNbr
            -- DebugOut ---Follow Path Count---
            -- DebugOut nFollowPathCount
            -- DebugOut calling done callback...
            ctx:doCallback("g_nFollowPathDoneCallback") -- FOLLOWPATH.inc:140
            do return ctx:exit("") end -- FOLLOWPATH.inc:141
        end -- FOLLOWPATH.inc:142
        -- Loop back to First one...
        ctx:state().g_nFollowPathNbr = 0 -- FOLLOWPATH.inc:145
    else -- FOLLOWPATH.inc:146
        -- Call our callback (with g_nFollowPathNbr set to the marker we're currently at!)
        ctx:state().g_nFollowPathNbr = (tonumber(ctx:state().g_nFollowPathNbr) or 0) - 1 -- FOLLOWPATH.inc:148
        ctx:doCallback("g_nFollowPathCallback") -- FOLLOWPATH.inc:149
        ctx:state().g_nFollowPathNbr = (tonumber(ctx:state().g_nFollowPathNbr) or 0) + 1 -- FOLLOWPATH.inc:150
    end -- FOLLOWPATH.inc:151
    -- Go to next marker...
    mm9.gosub(script, ctx, "FollowPathGetCurrHandle") -- FOLLOWPATH.inc:155
    -- DebugOut calling followPath Move
    mm9.gosub(script, ctx, "FollowPathMove") -- FOLLOWPATH.inc:158
    do return ctx:exit("") end -- FOLLOWPATH.inc:160
end

script.labels["FollowPathMove"] = function(ctx)
    -- FOLLOWPATH.inc:163
    -- Do the calculations and get us moving...
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:object("hFollowPathObject"):pos() -- FOLLOWPATH.inc:168
    ctx:getRotation(ctx:object("hFollowPathObject"), "g_rotX", "g_rotY", "g_rotZ", "g_rotSpin") -- FOLLOWPATH.inc:169
    ctx:calcRotationRate(ctx:object("hFollowPathObject"), "g_nFollowPathSpeed", "nFollowPathRate") -- FOLLOWPATH.inc:171
    ctx:setRotation("g_rotX", "g_rotY", "g_rotZ", "g_rotSpin", "nFollowPathRate") -- FOLLOWPATH.inc:173
    ctx:self():moveToPos("g_posX", "g_posY", "g_posZ", "g_nFollowPathSpeed", "FollowPathNext") -- FOLLOWPATH.inc:174
    do return ctx:exit("") end -- FOLLOWPATH.inc:176
end

script.labels["FollowPathGetPathCount"] = function(ctx)
    -- FOLLOWPATH.inc:179
    ctx:state().nFollowPathCount = 0 -- FOLLOWPATH.inc:182
    ctx:state().g_bTemp = true -- FOLLOWPATH.inc:183
    while ctx:condition("g_bTemp==TRUE") do -- FOLLOWPATH.inc:185
        ctx:set("sFollowPathTemp", "g_sFollowPathName") -- FOLLOWPATH.inc:186
        ctx:add("sFollowPathTemp", "nFollowPathCount") -- FOLLOWPATH.inc:187
        ctx:state().hFollowPathObject = ctx:objectOrNil("sFollowPathTemp") -- FOLLOWPATH.inc:189
        if ctx:condition("hFollowPathObject==0") then -- FOLLOWPATH.inc:191
            -- we've counted them all!
            ctx:state().g_bTemp = false -- FOLLOWPATH.inc:193
        else -- FOLLOWPATH.inc:194
            ctx:state().nFollowPathCount = (tonumber(ctx:state().nFollowPathCount) or 0) + 1 -- FOLLOWPATH.inc:195
        end -- FOLLOWPATH.inc:196
    end -- FOLLOWPATH.inc:197
    do return ctx:exit("") end -- FOLLOWPATH.inc:199
end

script.labels["FollowPathStop"] = function(ctx)
    -- FOLLOWPATH.inc:203
    ctx:self():stop() -- FOLLOWPATH.inc:205
    do return ctx:exit("") end -- FOLLOWPATH.inc:207
end

script.labels["FollowPathPlayerInterrupt"] = function(ctx)
    -- FOLLOWPATH.inc:210
    -- Player pressed the USE key during camera playback.
    -- By default, we'll abort the script and turn off the camera...
    mm9.gosub(script, ctx, "FollowPathStop") -- FOLLOWPATH.inc:219
    ctx:trigger("g_hMyObject", "OFF") -- FOLLOWPATH.inc:220
    do return ctx:exit("TRUE") end -- FOLLOWPATH.inc:222
end

return script
