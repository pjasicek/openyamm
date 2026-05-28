-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_GUARD0.scr"
script.includes = {}
script.labels = {}


-- DP_Guard0.scr
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
    -- DP_GUARD0.scr:31
    do return ctx:exit(1) end -- DP_GUARD0.scr:33
end

script.labels["CloseCellDoor"] = function(ctx)
    -- DP_GUARD0.scr:36
    ctx:command("playsound", "Sounds\\wahoo.wav dn 0 1000 0 100") -- DP_GUARD0.scr:39
    ctx:command("sswitch", "= sSwitchNameRoot") -- DP_GUARD0.scr:41
    ctx:command("getobjecthandle", "sSwitch hSwitch") -- DP_GUARD0.scr:43
    ctx:trigger("hSwitch", "close") -- DP_GUARD0.scr:44
    ctx:command("ncount", "= nCount + 1") -- DP_GUARD0.scr:45
    do return ctx:exit(1) end -- DP_GUARD0.scr:48
end

script.labels["OpenCellDoor"] = function(ctx)
    -- DP_GUARD0.scr:51
    ctx:command("playsound", "Sounds\\wahoo.wav dn 0 1000 0 100") -- DP_GUARD0.scr:53
    ctx:command("sswitch", "= sSwitchNameRoot + nCount") -- DP_GUARD0.scr:55
    ctx:command("getobjecthandle", "sSwitch hSwitch") -- DP_GUARD0.scr:56
    ctx:trigger("hSwitch", "Use") -- DP_GUARD0.scr:57
    do return ctx:exit(1) end -- DP_GUARD0.scr:60
end

script.labels["Main2"] = function(ctx)
    -- DP_GUARD0.scr:63
    ctx:command("sguard", "= sGuardNameRoot + 1") -- DP_GUARD0.scr:66
    ctx:command("getobjecthandle", "sGuard hGuard") -- DP_GUARD0.scr:67
    ctx:command("target", "hGuard 1") -- DP_GUARD0.scr:68
    do return ctx:exit(1) end -- DP_GUARD0.scr:70
end

script.labels["Main"] = function(ctx)
    -- DP_GUARD0.scr:73
    ctx:getParam(0, "sGuardNameRoot") -- DP_GUARD0.scr:76
    ctx:getParam(1, "sSwitchNameRoot") -- DP_GUARD0.scr:77
    ctx:addTrigger("OpenCellDoor", "OpenCellDoor") -- DP_GUARD0.scr:79
    ctx:addTrigger("CloseCellDoor", "CloseCellDoor") -- DP_GUARD0.scr:80
    ctx:command("wait", "0 .1 main2") -- DP_GUARD0.scr:82
    do return ctx:exit(1) end -- DP_GUARD0.scr:85
end

return script
