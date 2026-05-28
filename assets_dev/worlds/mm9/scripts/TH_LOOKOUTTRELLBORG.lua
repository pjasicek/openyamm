-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_LOOKOUTTRELLBORG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_LookOutTrellborg.scr
-- Karl Drown 11-18-01
-- Trellborg that is being the lookout for his
-- buddies in the Joust room.
script.labels["Start"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:25
    ctx:command("bisjousting", "= TRUE") -- TH_LOOKOUTTRELLBORG.scr:27
    mm9.gosub(script, ctx, "WalkToMarker") -- TH_LOOKOUTTRELLBORG.scr:28
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:29
end

script.labels["TurnOff"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:31
    ctx:command("wait", "1, 1, DoNothing") -- TH_LOOKOUTTRELLBORG.scr:33
    ctx:command("bisjousting", "= FALSE") -- TH_LOOKOUTTRELLBORG.scr:34
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:35
end

script.labels["LookAround"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:38
    ctx:command("stop", "") -- TH_LOOKOUTTRELLBORG.scr:39
    ctx:command("playanim", "Stand, AnimationA") -- TH_LOOKOUTTRELLBORG.scr:40
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:41
end

script.labels["AnimationA"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:42
    ctx:command("playanim", "Fidget1, AnimationB") -- TH_LOOKOUTTRELLBORG.scr:43
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:44
end

script.labels["AnimationB"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:45
    ctx:command("playanim", "Stand, WalkToMarker") -- TH_LOOKOUTTRELLBORG.scr:46
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:47
end

script.labels["WatchVictim"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:52
    ctx:command("stop", "") -- TH_LOOKOUTTRELLBORG.scr:54
    ctx:command("getobjecthandle", "sTargetB, hTarget") -- TH_LOOKOUTTRELLBORG.scr:55
    ctx:command("faceobject", "hTarget, 180") -- TH_LOOKOUTTRELLBORG.scr:56
    ctx:command("wait", "0, 2, LookAround") -- TH_LOOKOUTTRELLBORG.scr:57
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:58
end

script.labels["WatchBully"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:60
    ctx:command("stop", "") -- TH_LOOKOUTTRELLBORG.scr:62
    ctx:command("getobjecthandle", "sTargetA, hTarget") -- TH_LOOKOUTTRELLBORG.scr:63
    ctx:command("faceobject", "hTarget, 180") -- TH_LOOKOUTTRELLBORG.scr:64
    ctx:command("wait", "0, 2, LookAround") -- TH_LOOKOUTTRELLBORG.scr:65
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:66
end

script.labels["WalkToMarker"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:68
    if ctx:condition("bIsJousting==FALSE") then -- TH_LOOKOUTTRELLBORG.scr:70
        do return ctx:exit("") end -- TH_LOOKOUTTRELLBORG.scr:71
    end -- TH_LOOKOUTTRELLBORG.scr:72
    if ctx:condition("bDirection==0") then -- TH_LOOKOUTTRELLBORG.scr:74
        ctx:command("bdirection", "= 1") -- TH_LOOKOUTTRELLBORG.scr:75
        ctx:command("getobjecthandle", "sMarkerA, hMarker") -- TH_LOOKOUTTRELLBORG.scr:76
        ctx:command("walkto", "hMarker, 5, WatchVictim") -- TH_LOOKOUTTRELLBORG.scr:77
    else -- TH_LOOKOUTTRELLBORG.scr:78
        ctx:command("bdirection", "= 0") -- TH_LOOKOUTTRELLBORG.scr:79
        ctx:command("getobjecthandle", "sMarkerB, hMarker") -- TH_LOOKOUTTRELLBORG.scr:80
        ctx:command("walkto", "hMarker, 5, WatchBully") -- TH_LOOKOUTTRELLBORG.scr:81
    end -- TH_LOOKOUTTRELLBORG.scr:82
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:83
end

script.labels["Main2"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:86
    ctx:addTrigger("Go", "Start") -- TH_LOOKOUTTRELLBORG.scr:88
    ctx:addTrigger("Stop", "TurnOff") -- TH_LOOKOUTTRELLBORG.scr:89
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_LOOKOUTTRELLBORG.scr:90
    do return ctx:exit("TRUE") end -- TH_LOOKOUTTRELLBORG.scr:91
end

script.labels["Main"] = function(ctx)
    -- TH_LOOKOUTTRELLBORG.scr:93
    ctx:getParam(0, "sMarkerA") -- TH_LOOKOUTTRELLBORG.scr:95
    ctx:getParam(1, "sMarkerB") -- TH_LOOKOUTTRELLBORG.scr:96
    ctx:getParam(2, "sTargetA") -- TH_LOOKOUTTRELLBORG.scr:97
    ctx:getParam(3, "sTargetB") -- TH_LOOKOUTTRELLBORG.scr:98
    ctx:command("onpoststartworld", "Main2") -- TH_LOOKOUTTRELLBORG.scr:99
    do return ctx:exit("") end -- TH_LOOKOUTTRELLBORG.scr:100
end

return script
