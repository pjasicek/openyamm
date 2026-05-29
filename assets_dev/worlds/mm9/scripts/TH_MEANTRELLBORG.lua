-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_MEANTRELLBORG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_MeanTrellborg.scr
-- Karl Drown 11-18-01
-- Trellborg that launches the practice horse for
-- his buddies in the Joust room.
script.labels["CheckStart"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:23
    if ctx:condition("bIsJousting==FALSE") then -- TH_MEANTRELLBORG.scr:25
        do return ctx:exit("") end -- TH_MEANTRELLBORG.scr:26
    end -- TH_MEANTRELLBORG.scr:27
    mm9.gosub(script, ctx, "Start") -- TH_MEANTRELLBORG.scr:28
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:29
end

script.labels["Start"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:31
    ctx:state().bIsJousting = true -- TH_MEANTRELLBORG.scr:33
    mm9.gosub(script, ctx, "StartAnimations") -- TH_MEANTRELLBORG.scr:34
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:35
end

script.labels["TurnOff"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:37
    ctx:wait(1, 1, "DoNothing") -- TH_MEANTRELLBORG.scr:39
    ctx:state().bIsJousting = false -- TH_MEANTRELLBORG.scr:40
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:41
end

script.labels["AnimationA"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:44
    ctx:self():stop() -- TH_MEANTRELLBORG.scr:45
    ctx:self():playAnimation("Stand", "AnimationB") -- TH_MEANTRELLBORG.scr:46
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:47
end

script.labels["AnimationB"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:48
    ctx:self():playAnimation("Fidget3", "AnimationC") -- TH_MEANTRELLBORG.scr:49
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:50
end

script.labels["AnimationC"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:51
    ctx:self():playAnimation("Fidget1", "AnimationD") -- TH_MEANTRELLBORG.scr:52
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:53
end

script.labels["AnimationD"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:54
    ctx:self():playAnimation("Taunt", "LaunchHorse") -- TH_MEANTRELLBORG.scr:55
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:56
end

script.labels["LaunchHorse"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:57
    ctx:trigger("hSwitch", "Use") -- TH_MEANTRELLBORG.scr:58
    ctx:self():faceObject(ctx:object("hTrellborg"), 180) -- TH_MEANTRELLBORG.scr:59
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:60
end

script.labels["ResetSwitch"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:65
    ctx:self():faceObject(ctx:object("hSwitch"), 180) -- TH_MEANTRELLBORG.scr:67
    ctx:trigger("hSwitch", "Use") -- TH_MEANTRELLBORG.scr:68
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:69
end

script.labels["StartAnimations"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:72
    if ctx:condition("bIsJousting==FALSE") then -- TH_MEANTRELLBORG.scr:74
        do return ctx:exit("") end -- TH_MEANTRELLBORG.scr:75
    end -- TH_MEANTRELLBORG.scr:76
    mm9.gosub(script, ctx, "AnimationA") -- TH_MEANTRELLBORG.scr:77
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:79
end

script.labels["Main2"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:82
    ctx:state().hSwitch = ctx:objectOrNil("sSwitch") -- TH_MEANTRELLBORG.scr:84
    ctx:state().hTrellborg = ctx:objectOrNil("sTrellborg") -- TH_MEANTRELLBORG.scr:85
    ctx:addTrigger("Go", "Start") -- TH_MEANTRELLBORG.scr:86
    ctx:addTrigger("Stop", "TurnOff") -- TH_MEANTRELLBORG.scr:87
    ctx:addTrigger("Switch", "ResetSwitch") -- TH_MEANTRELLBORG.scr:88
    ctx:addTrigger("Throw", "CheckStart") -- TH_MEANTRELLBORG.scr:89
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_MEANTRELLBORG.scr:90
    do return ctx:exit("TRUE") end -- TH_MEANTRELLBORG.scr:91
end

script.labels["Main"] = function(ctx)
    -- TH_MEANTRELLBORG.scr:93
    ctx:getParam(0, "sSwitch") -- TH_MEANTRELLBORG.scr:95
    ctx:getParam(1, "sTrellborg") -- TH_MEANTRELLBORG.scr:96
    ctx:onEvent("OnPostStartWorld", "Main2") -- TH_MEANTRELLBORG.scr:97
    do return ctx:exit("") end -- TH_MEANTRELLBORG.scr:98
end

return script
