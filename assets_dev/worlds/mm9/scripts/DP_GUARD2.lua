-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_GUARD2.scr"
script.includes = {}
script.labels = {}


-- DP_Guard2.scr
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
    -- DP_GUARD2.scr:40
    do return ctx:exit(1) end -- DP_GUARD2.scr:42
end

script.labels["StopMoving"] = function(ctx)
    -- DP_GUARD2.scr:45
    ctx:self():setIdle() -- DP_GUARD2.scr:47
    do return ctx:exit(1) end -- DP_GUARD2.scr:49
end

script.labels["LockDown"] = function(ctx)
    -- DP_GUARD2.scr:52
    ctx:self():setTarget(nil) -- DP_GUARD2.scr:55
    ctx:self():setIdle() -- DP_GUARD2.scr:56
    ctx:set("nMarker", "nCount * 3 + 2") -- DP_GUARD2.scr:58
    ctx:set("sMarker", "sMarkerNameRoot + nMarker") -- DP_GUARD2.scr:59
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_GUARD2.scr:60
    ctx:self():walkTo(ctx:object("hMarker"), 50, "StopMoving") -- DP_GUARD2.scr:61
    ctx:set("nCount", "nCount + 1") -- DP_GUARD2.scr:62
    do return ctx:exit(1) end -- DP_GUARD2.scr:64
end

script.labels["Follow"] = function(ctx)
    -- DP_GUARD2.scr:67
    ctx:self():walkTo(ctx:object("hPrisoner"), 50, "dn") -- DP_GUARD2.scr:70
    ctx:onEvent("OnTargetBeyondDist", 50, "Follow") -- DP_GUARD2.scr:71
    do return ctx:exit(1) end -- DP_GUARD2.scr:73
end

script.labels["GoToCell"] = function(ctx)
    -- DP_GUARD2.scr:76
    ctx:self():setTarget(nil) -- DP_GUARD2.scr:79
    ctx:set("nMarker", "nCount * 3 + 4") -- DP_GUARD2.scr:81
    ctx:set("sMarker", "sMarkerNameRoot + nMarker") -- DP_GUARD2.scr:82
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_GUARD2.scr:83
    ctx:self():walkTo(ctx:object("hMarker"), 30, "dn") -- DP_GUARD2.scr:84
    ctx:set("sPrisoner", "sPrisonerNameRoot + nCount") -- DP_GUARD2.scr:86
    ctx:state().hPrisoner = ctx:objectOrNil("sPrisoner") -- DP_GUARD2.scr:87
    ctx:self():setTarget(ctx:object("hPrisoner")) -- DP_GUARD2.scr:88
    do return ctx:exit(1) end -- DP_GUARD2.scr:91
end

script.labels["Main2"] = function(ctx)
    -- DP_GUARD2.scr:96
    ctx:set("sPrisoner", "sPrisonerNameRoot + nCount") -- DP_GUARD2.scr:99
    ctx:state().hPrisoner = ctx:objectOrNil("sPrisoner") -- DP_GUARD2.scr:100
    ctx:self():setTarget(ctx:object("hPrisoner")) -- DP_GUARD2.scr:101
    mm9.gosub(script, ctx, "follow") -- DP_GUARD2.scr:102
    do return ctx:exit(1) end -- DP_GUARD2.scr:104
end

script.labels["Main"] = function(ctx)
    -- DP_GUARD2.scr:107
    ctx:getParam(0, "sGuardNameRoot") -- DP_GUARD2.scr:110
    ctx:getParam(1, "sPrisonerNameRoot") -- DP_GUARD2.scr:111
    ctx:getParam(2, "nNumPrisoners") -- DP_GUARD2.scr:112
    ctx:getParam(3, "sMarkerNameRoot") -- DP_GUARD2.scr:113
    ctx:addTrigger("GoToCell", "GoToCell") -- DP_GUARD2.scr:115
    ctx:addTrigger("Follow", "Follow") -- DP_GUARD2.scr:116
    ctx:addTrigger("LockDown", "LockDown") -- DP_GUARD2.scr:117
    ctx:wait(0, .1, "main2") -- DP_GUARD2.scr:119
    do return ctx:exit(1) end -- DP_GUARD2.scr:122
end

return script
