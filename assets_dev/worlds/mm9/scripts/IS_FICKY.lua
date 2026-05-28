-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IS_FICKY.scr"
script.includes = {}
script.labels = {}


-- IS_ficky.scr
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
script.labels["PickMarker"] = function(ctx)
    -- IS_FICKY.scr:36
    ctx:command("getrandomint", "0, nNumMarkers, nMarker") -- IS_FICKY.scr:39
    if ctx:condition("nMarker == nPrevMarker") then -- IS_FICKY.scr:40
        mm9.gosub(script, ctx, "PickMarker") -- IS_FICKY.scr:41
    else -- IS_FICKY.scr:42
        ctx:command("nprevmarker", "= nMarker") -- IS_FICKY.scr:43
    end -- IS_FICKY.scr:44
    do return ctx:exit(1) end -- IS_FICKY.scr:46
end

script.labels["Go"] = function(ctx)
    -- IS_FICKY.scr:49
    mm9.gosub(script, ctx, "PickMarker") -- IS_FICKY.scr:52
    ctx:command("smarker", "= sMarkerRoot") -- IS_FICKY.scr:53
    ctx:command("add", "sMarker nMarker") -- IS_FICKY.scr:54
    ctx:command("getobjecthandle", "sMarker hMarker") -- IS_FICKY.scr:55
    ctx:command("walkto", "hMarker 30 Go") -- IS_FICKY.scr:56
    do return ctx:exit(1) end -- IS_FICKY.scr:58
end

script.labels["scatter"] = function(ctx)
    -- IS_FICKY.scr:61
    if ctx:condition("nCount < nNumBirds") then -- IS_FICKY.scr:64
        ctx:command("sbirdname", "= sBirdNameRoot + nCount") -- IS_FICKY.scr:65
        ctx:command("getobjecthandle", "sBirdName hBird") -- IS_FICKY.scr:66
        ctx:trigger("hBird", "go") -- IS_FICKY.scr:67
        ctx:command("ncount", "= nCount + 1") -- IS_FICKY.scr:68
        ctx:command("wait", "0 .2 scatter") -- IS_FICKY.scr:69
    else -- IS_FICKY.scr:70
        -- Gosub go
        ctx:command("removetrigger", "scatter") -- IS_FICKY.scr:72
    end -- IS_FICKY.scr:73
    do return ctx:exit(1) end -- IS_FICKY.scr:76
end

script.labels["Main"] = function(ctx)
    -- IS_FICKY.scr:80
    ctx:getParam(0, "sMarkerRoot") -- IS_FICKY.scr:83
    ctx:getParam(1, "nNumMarkers") -- IS_FICKY.scr:84
    ctx:getParam(2, "sBirdNameRoot") -- IS_FICKY.scr:85
    ctx:getParam(3, "nNumBirds") -- IS_FICKY.scr:86
    ctx:command("nnummarkers", "= nNumMarkers - 1") -- IS_FICKY.scr:88
    ctx:addTrigger("Scatter", "scatter") -- IS_FICKY.scr:89
    mm9.gosub(script, ctx, "Go") -- IS_FICKY.scr:90
    ctx:command("onstuck", "Go") -- IS_FICKY.scr:91
    do return ctx:exit(1) end -- IS_FICKY.scr:93
end

return script
