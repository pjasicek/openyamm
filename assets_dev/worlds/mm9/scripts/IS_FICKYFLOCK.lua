-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IS_FICKYFLOCK.scr"
script.includes = {}
script.labels = {}


-- IS_fickyflock.scr
-- Brett Yagi
-- Birds will be inactive till triggered.  When triggered they will
-- fly to the Marker specificed by p0 + p1 (ie p0 = "Mrk" p1="4"
-- then the marker moved to is "Mrk4").  It will then pick a random
-- marker out of markers provide and move there and then die
-- Parameters
-- 0 - Marker Root name  (ie for Markers Mrk0,Mrk1,Mrk2  "Mrk" is the root name)
-- 1 - Number of Markers
script.labels["DN"] = function(ctx)
    -- IS_FICKYFLOCK.scr:31
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:35
end

script.labels["TriggerScatter"] = function(ctx)
    -- IS_FICKYFLOCK.scr:39
    ctx:command("getobjecthandle", "BirdIntheSky0 hBigBird") -- IS_FICKYFLOCK.scr:42
    ctx:trigger("hBigBird", "scatter") -- IS_FICKYFLOCK.scr:43
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:45
end

script.labels["Disappear"] = function(ctx)
    -- IS_FICKYFLOCK.scr:49
    ctx:command("die", "") -- IS_FICKYFLOCK.scr:51
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:53
end

script.labels["GoAway"] = function(ctx)
    -- IS_FICKYFLOCK.scr:57
    ctx:command("getrandomint", "0, nNumMarkers, nMarker") -- IS_FICKYFLOCK.scr:60
    ctx:command("smarker", "= sMarkerRoot") -- IS_FICKYFLOCK.scr:61
    ctx:command("add", "sMarker nMarker") -- IS_FICKYFLOCK.scr:62
    ctx:command("getobjecthandle", "sMarker hMarker") -- IS_FICKYFLOCK.scr:63
    ctx:command("nplaysound", "= 1") -- IS_FICKYFLOCK.scr:64
    ctx:command("walkto", "hMarker 50 Disappear") -- IS_FICKYFLOCK.scr:65
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:67
end

script.labels["Replay"] = function(ctx)
    -- IS_FICKYFLOCK.scr:70
    if ctx:condition("nPlaySound == 0") then -- IS_FICKYFLOCK.scr:74
        ctx:command("playsound", "Sounds\\AnimSounds\\harpyflap.wav Replay 0 1000 0 50") -- IS_FICKYFLOCK.scr:76
    end -- IS_FICKYFLOCK.scr:78
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:81
end

script.labels["Go"] = function(ctx)
    -- IS_FICKYFLOCK.scr:85
    ctx:command("playsound", "Sounds\\AnimSounds\\harpyflap.wav replay 0 1000 0 50") -- IS_FICKYFLOCK.scr:89
    ctx:command("removetrigger", "Go") -- IS_FICKYFLOCK.scr:90
    ctx:command("nmarker", "= nNumMarkers + 1") -- IS_FICKYFLOCK.scr:91
    ctx:command("smarker", "= sMarkerRoot") -- IS_FICKYFLOCK.scr:92
    ctx:command("add", "sMarker nMarker") -- IS_FICKYFLOCK.scr:93
    ctx:command("getobjecthandle", "sMarker hMarker") -- IS_FICKYFLOCK.scr:97
    ctx:command("walkto", "hMarker 30 GoAway") -- IS_FICKYFLOCK.scr:98
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:100
end

script.labels["Main2"] = function(ctx)
    -- IS_FICKYFLOCK.scr:103
    ctx:command("getmyhandle", "hMe") -- IS_FICKYFLOCK.scr:106
    ctx:command("getstat", "hMe flyvel nSpeed") -- IS_FICKYFLOCK.scr:107
    ctx:command("nspeed", "= nSpeed / 4") -- IS_FICKYFLOCK.scr:108
    ctx:command("setstat", "hMe flyvel nSpeed") -- IS_FICKYFLOCK.scr:109
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:111
end

script.labels["Main"] = function(ctx)
    -- IS_FICKYFLOCK.scr:114
    ctx:getParam(0, "sMarkerRoot") -- IS_FICKYFLOCK.scr:117
    ctx:getParam(1, "nNumMarkers") -- IS_FICKYFLOCK.scr:118
    ctx:command("nnummarkers", "= nNumMarkers - 1") -- IS_FICKYFLOCK.scr:119
    ctx:addTrigger("Go", "Go") -- IS_FICKYFLOCK.scr:120
    ctx:command("ondamage", "TriggerScatter TriggerScatter") -- IS_FICKYFLOCK.scr:121
    ctx:command("onstuck", "Go") -- IS_FICKYFLOCK.scr:122
    ctx:command("wait", "0 .1 main2") -- IS_FICKYFLOCK.scr:123
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:126
end

return script
