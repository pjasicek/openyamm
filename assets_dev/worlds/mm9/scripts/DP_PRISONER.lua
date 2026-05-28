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
    ctx:command("setidle", "") -- DP_PRISONER.scr:40
    do return ctx:exit(1) end -- DP_PRISONER.scr:42
end

script.labels["GetInCell"] = function(ctx)
    -- DP_PRISONER.scr:45
    ctx:command("setidle", "") -- DP_PRISONER.scr:48
    ctx:command("target", "NULL 0") -- DP_PRISONER.scr:49
    ctx:command("getobjecthandle", "sCellMarker hMarker") -- DP_PRISONER.scr:50
    ctx:command("walkto", "hMarker 30 dn") -- DP_PRISONER.scr:51
    do return ctx:exit(1) end -- DP_PRISONER.scr:53
end

script.labels["Follow"] = function(ctx)
    -- DP_PRISONER.scr:57
    ctx:command("walkto", "hGuard 50 dn") -- DP_PRISONER.scr:60
    ctx:command("ontargetbeyonddist", "50 Follow") -- DP_PRISONER.scr:61
    do return ctx:exit(1) end -- DP_PRISONER.scr:64
end

script.labels["ExitCell"] = function(ctx)
    -- DP_PRISONER.scr:68
    ctx:command("nmarker", "= nPrisonerNum * 3 + 3") -- DP_PRISONER.scr:71
    ctx:command("smarker", "= sMarkerNameRoot + nMarker") -- DP_PRISONER.scr:72
    ctx:command("getobjecthandle", "sMarker hMarker") -- DP_PRISONER.scr:73
    ctx:command("sguard", "= sGuardNameRoot + 1") -- DP_PRISONER.scr:74
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_PRISONER.scr:75
    ctx:trigger("hGuard", "WalkToIR") -- DP_PRISONER.scr:76
    ctx:command("target", "hGuard 1") -- DP_PRISONER.scr:77
    do return ctx:exit(1) end -- DP_PRISONER.scr:79
end

script.labels["Main2"] = function(ctx)
    -- DP_PRISONER.scr:82
    ctx:command("sguard", "= sGuardNameRoot + 1") -- DP_PRISONER.scr:85
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_PRISONER.scr:86
    ctx:command("target", "hGuard 1") -- DP_PRISONER.scr:87
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
    ctx:command("wait", "0 .1 main2") -- DP_PRISONER.scr:106
    do return ctx:exit(1) end -- DP_PRISONER.scr:109
end

return script
