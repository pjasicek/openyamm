-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_PRISONER.scr"
script.includes = {}
script.labels = {}


-- DP_Prisoner.scr
-- Brett Yagi
-- Works in conjunction with IS_fickyflock.scr.
-- Generic function moves object randomly between markers in parameters
-- When given the "scatter" trigger, it will trigger the "birds"
-- specified in parameters.
-- Parameters
-- 0 - Marker Root name  (ie for Markers Mrk0, Mrk1, Mrk2  "Mrk" is the root name)
-- 1 - Number of Markers
-- 2 - Bird Root name  (ie for Birds Bird0, Bird01, Bird02  "Bird0" is the root name)
-- 3 - Number of Birds
script.labels["dn"] = function(ctx)
    -- DP_PRISONER.scr:34
    do return ctx:exit(1) end -- DP_PRISONER.scr:36
end

script.labels["DoNothing"] = function(ctx)
    -- DP_PRISONER.scr:38
    ctx:self():setIdle() -- DP_PRISONER.scr:40
    do return ctx:exit(1) end -- DP_PRISONER.scr:42
end

script.labels["GetInCell"] = function(ctx)
    -- DP_PRISONER.scr:45
    ctx:self():setIdle() -- DP_PRISONER.scr:48
    ctx:self():setTarget(nil) -- DP_PRISONER.scr:49
    ctx:state().hMarker = ctx:objectOrNil("sCellMarker") -- DP_PRISONER.scr:50
    ctx:self():walkTo(ctx:object("hMarker"), 30, "dn") -- DP_PRISONER.scr:51
    do return ctx:exit(1) end -- DP_PRISONER.scr:53
end

script.labels["Follow"] = function(ctx)
    -- DP_PRISONER.scr:57
    ctx:self():walkTo(ctx:object("hGuard"), 50, "dn") -- DP_PRISONER.scr:60
    ctx:onEvent("OnTargetBeyondDist", 50, "Follow") -- DP_PRISONER.scr:61
    do return ctx:exit(1) end -- DP_PRISONER.scr:64
end

script.labels["ExitCell"] = function(ctx)
    -- DP_PRISONER.scr:68
    ctx:set("nMarker", "nPrisonerNum * 3 + 3") -- DP_PRISONER.scr:71
    ctx:set("sMarker", "sMarkerNameRoot + nMarker") -- DP_PRISONER.scr:72
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_PRISONER.scr:73
    ctx:set("sGuard", "sGuardNameRoot + 1") -- DP_PRISONER.scr:74
    ctx:object("sGuard"):trigger("WalkToIR") -- DP_PRISONER.scr:75-76
    ctx:self():setTarget(ctx:object("hGuard")) -- DP_PRISONER.scr:77
    do return ctx:exit(1) end -- DP_PRISONER.scr:79
end

script.labels["Main2"] = function(ctx)
    -- DP_PRISONER.scr:82
    ctx:set("sGuard", "sGuardNameRoot + 1") -- DP_PRISONER.scr:85
    ctx:state().hGuard = ctx:objectOrNil("sGuard") -- DP_PRISONER.scr:86
    ctx:self():setTarget(ctx:object("hGuard")) -- DP_PRISONER.scr:87
    mm9.gosub(script, ctx, "Follow") -- DP_PRISONER.scr:88
    do return ctx:exit(1) end -- DP_PRISONER.scr:90
end

script.labels["Main"] = function(ctx)
    -- DP_PRISONER.scr:93
    ctx:getParam(0, "sGuardNameRoot") -- DP_PRISONER.scr:96
    ctx:getParam(1, "sMarkerNameRoot") -- DP_PRISONER.scr:97
    ctx:getParam(2, "sCellMarker") -- DP_PRISONER.scr:98
    ctx:getParam(3, "nPrisonerNum") -- DP_PRISONER.scr:99
    ctx:addTrigger("ExitCell", "ExitCell") -- DP_PRISONER.scr:103
    ctx:addTrigger("Follow", "Follow") -- DP_PRISONER.scr:104
    ctx:addTrigger("GetInCell", "GetInCell") -- DP_PRISONER.scr:105
    ctx:wait(0, .1, "main2") -- DP_PRISONER.scr:106
    do return ctx:exit(1) end -- DP_PRISONER.scr:109
end

return script
