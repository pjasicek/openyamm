-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_PATROL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "DrangheimHostility.inc" }

-- DP_Patrol.scr
-- Brett Yagi
-- Parameters
-- 0 - Marker Root name  (ie for Markers Mrk0, Mrk1, Mrk2  "Mrk" is the root name)
-- 1 - Number of Markers
script.labels["dn"] = function(ctx)
    -- DP_PATROL.scr:25
    do return ctx:exit(1) end -- DP_PATROL.scr:27
end

script.labels["GoToMarker"] = function(ctx)
    -- DP_PATROL.scr:31
    ctx:set("sMarker", "sPatrolMarkerRoot + nMarker") -- DP_PATROL.scr:34
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_PATROL.scr:35
    if ctx:condition("nForward == 0") then -- DP_PATROL.scr:37
        if ctx:condition("nMarker != nNumMarkers") then -- DP_PATROL.scr:38
            ctx:set("nMarker", "nMarker + 1") -- DP_PATROL.scr:39
        else -- DP_PATROL.scr:40
            ctx:state().nForward = 1 -- DP_PATROL.scr:41
            ctx:set("nMarker", "nMarker - 1") -- DP_PATROL.scr:42
        end -- DP_PATROL.scr:43
    else -- DP_PATROL.scr:44
        if ctx:condition("nMarker != 0") then -- DP_PATROL.scr:45
            ctx:set("nMarker", "nMarker - 1") -- DP_PATROL.scr:46
        else -- DP_PATROL.scr:47
            ctx:state().nForward = 0 -- DP_PATROL.scr:48
            ctx:set("nMarker", "nMarker + 1") -- DP_PATROL.scr:49
        end -- DP_PATROL.scr:50
    end -- DP_PATROL.scr:52
    ctx:self():walkTo(ctx:object("hMarker"), 40, "GoToMarker") -- DP_PATROL.scr:53
    do return ctx:exit(1) end -- DP_PATROL.scr:56
end

script.labels["UnStuckMe"] = function(ctx)
    -- DP_PATROL.scr:59
    if ctx:condition("nForward == 0") then -- DP_PATROL.scr:62
        ctx:set("nMarker", "nMarker - 1") -- DP_PATROL.scr:63
    else -- DP_PATROL.scr:64
        ctx:set("nMarker", "nMarker + 1") -- DP_PATROL.scr:65
    end -- DP_PATROL.scr:66
    mm9.gosub(script, ctx, "GoToMarker") -- DP_PATROL.scr:68
    do return ctx:exit(1) end -- DP_PATROL.scr:70
end

script.labels["ClearofDoor"] = function(ctx)
    -- DP_PATROL.scr:73
    ctx:state().nDoor = 0 -- DP_PATROL.scr:76
    do return ctx:exit(1) end -- DP_PATROL.scr:79
end

script.labels["GoThruDoor"] = function(ctx)
    -- DP_PATROL.scr:84
    ctx:getParam(0, "hDoor") -- DP_PATROL.scr:87
    if ctx:condition("nDoor == 0") then -- DP_PATROL.scr:88
        ctx:self():setIdle() -- DP_PATROL.scr:89
        ctx:state().nDoor = 1 -- DP_PATROL.scr:90
        if ctx:condition("nForward == 0") then -- DP_PATROL.scr:91
            ctx:set("nMarker", "nMarker - 1") -- DP_PATROL.scr:92
        else -- DP_PATROL.scr:93
            ctx:set("nMarker", "nMarker + 1") -- DP_PATROL.scr:94
        end -- DP_PATROL.scr:95
        ctx:trigger("hDoor", "use") -- DP_PATROL.scr:97
        ctx:wait(0, 1, "GoToMarker") -- DP_PATROL.scr:98
        ctx:wait(1, 3, "ClearofDoor") -- DP_PATROL.scr:99
    end -- DP_PATROL.scr:100
    do return ctx:exit(1) end -- DP_PATROL.scr:102
end

script.labels["Main2"] = function(ctx)
    -- DP_PATROL.scr:106
    mm9.gosub(script, ctx, "InitDrangheimHostility") -- DP_PATROL.scr:108
    ctx:set("nNumMarkers", "nNumMarkers - 1") -- DP_PATROL.scr:110
    mm9.gosub(script, ctx, "GoToMarker") -- DP_PATROL.scr:112
    do return ctx:exit(1) end -- DP_PATROL.scr:114
end

script.labels["Main"] = function(ctx)
    -- DP_PATROL.scr:117
    ctx:getParam(0, "sPatrolMarkerRoot") -- DP_PATROL.scr:120
    ctx:getParam(1, "nNumMarkers") -- DP_PATROL.scr:121
    ctx:onEvent("OnStuck", "UnStuckMe") -- DP_PATROL.scr:122
    ctx:onEvent("OnDoor", "GoThruDoor") -- DP_PATROL.scr:123
    ctx:wait(0, .1, "main2") -- DP_PATROL.scr:124
    do return ctx:exit(1) end -- DP_PATROL.scr:127
end

return script
