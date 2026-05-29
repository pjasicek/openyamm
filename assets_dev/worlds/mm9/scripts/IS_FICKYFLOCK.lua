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
    ctx:object("BirdIntheSky0"):trigger("scatter") -- IS_FICKYFLOCK.scr:42-43
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:45
end

script.labels["Disappear"] = function(ctx)
    -- IS_FICKYFLOCK.scr:49
    ctx:self():die() -- IS_FICKYFLOCK.scr:51
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:53
end

script.labels["GoAway"] = function(ctx)
    -- IS_FICKYFLOCK.scr:57
    ctx:randomInt(0, "nNumMarkers", "nMarker") -- IS_FICKYFLOCK.scr:60
    ctx:set("sMarker", "sMarkerRoot") -- IS_FICKYFLOCK.scr:61
    ctx:add("sMarker", "nMarker") -- IS_FICKYFLOCK.scr:62
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- IS_FICKYFLOCK.scr:63
    ctx:state().nPlaySound = 1 -- IS_FICKYFLOCK.scr:64
    ctx:self():walkTo(ctx:object("hMarker"), 50, "Disappear") -- IS_FICKYFLOCK.scr:65
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:67
end

script.labels["Replay"] = function(ctx)
    -- IS_FICKYFLOCK.scr:70
    if ctx:condition("nPlaySound == 0") then -- IS_FICKYFLOCK.scr:74
        ctx:playSound("Sounds\\AnimSounds\\harpyflap.wav", "Replay", 0, 1000, 0, 50) -- IS_FICKYFLOCK.scr:76
    end -- IS_FICKYFLOCK.scr:78
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:81
end

script.labels["Go"] = function(ctx)
    -- IS_FICKYFLOCK.scr:85
    ctx:playSound("Sounds\\AnimSounds\\harpyflap.wav", "replay", 0, 1000, 0, 50) -- IS_FICKYFLOCK.scr:89
    ctx:removeTrigger("Go") -- IS_FICKYFLOCK.scr:90
    ctx:set("nMarker", "nNumMarkers + 1") -- IS_FICKYFLOCK.scr:91
    ctx:set("sMarker", "sMarkerRoot") -- IS_FICKYFLOCK.scr:92
    ctx:add("sMarker", "nMarker") -- IS_FICKYFLOCK.scr:93
    ctx:state().hMarker = ctx:objectOrNil("sMarker") -- IS_FICKYFLOCK.scr:97
    ctx:self():walkTo(ctx:object("hMarker"), 30, "GoAway") -- IS_FICKYFLOCK.scr:98
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:100
end

script.labels["Main2"] = function(ctx)
    -- IS_FICKYFLOCK.scr:103
    ctx:state().nSpeed = ctx:self():getStat("flyvel") -- IS_FICKYFLOCK.scr:107
    ctx:set("nSpeed", "nSpeed / 4") -- IS_FICKYFLOCK.scr:108
    ctx:self():setStat("flyvel", "nSpeed") -- IS_FICKYFLOCK.scr:109
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:111
end

script.labels["Main"] = function(ctx)
    -- IS_FICKYFLOCK.scr:114
    ctx:getParam(0, "sMarkerRoot") -- IS_FICKYFLOCK.scr:117
    ctx:getParam(1, "nNumMarkers") -- IS_FICKYFLOCK.scr:118
    ctx:set("nNumMarkers", "nNumMarkers - 1") -- IS_FICKYFLOCK.scr:119
    ctx:addTrigger("Go", "Go") -- IS_FICKYFLOCK.scr:120
    ctx:onEvent("OnDamage", "TriggerScatter") -- IS_FICKYFLOCK.scr:121
    ctx:onEvent("OnStuck", "Go") -- IS_FICKYFLOCK.scr:122
    ctx:wait(0, .1, "main2") -- IS_FICKYFLOCK.scr:123
    do return ctx:exit(1) end -- IS_FICKYFLOCK.scr:126
end

return script
