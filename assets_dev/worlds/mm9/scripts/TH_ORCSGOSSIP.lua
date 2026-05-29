-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_ORCSGOSSIP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_OrcsGossip.scr
-- Karl Drown 11-17-01
-- Orc's script in RightHall.
script.labels["Start"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:25
    ctx:cprint("TurnOn") -- TH_ORCSGOSSIP.scr:27
    ctx:state().bIsGossiping = true -- TH_ORCSGOSSIP.scr:28
    mm9.gosub(script, ctx, "DoTheTalk") -- TH_ORCSGOSSIP.scr:29
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:30
end

script.labels["TurnOff"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:32
    ctx:cprint("TurnOff") -- TH_ORCSGOSSIP.scr:34
    ctx:wait(1, 1, "DoNothing") -- TH_ORCSGOSSIP.scr:35
    ctx:state().bIsGossiping = false -- TH_ORCSGOSSIP.scr:36
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:37
end

script.labels["DoTheTalk"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:39
    if ctx:condition("bIsGossiping==FALSE") then -- TH_ORCSGOSSIP.scr:41
        do return ctx:exit("") end -- TH_ORCSGOSSIP.scr:42
    end -- TH_ORCSGOSSIP.scr:43
    ctx:self():playAnimation("sAnimA", "AnimationB") -- TH_ORCSGOSSIP.scr:44
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:45
end

script.labels["AnimationB"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:47
    ctx:playSound("Sounds\\AnimSounds\\LizardOrcfidget3.wav", "DoNothing", 1000, 1500, "FALSE", 100) -- TH_ORCSGOSSIP.scr:48
    ctx:self():playAnimation("sAnimB", "AnimationC") -- TH_ORCSGOSSIP.scr:49
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:50
end

script.labels["AnimationC"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:51
    ctx:self():playAnimation("sAnimC", "AnimationD") -- TH_ORCSGOSSIP.scr:52
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:53
end

script.labels["AnimationD"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:54
    -- playsound Sounds\AnimSounds\LizardOrcwince1.wav DoNothing 1000 1500 FALSE 100
    ctx:self():playAnimation("sAnimD", "AnimationE") -- TH_ORCSGOSSIP.scr:56
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:57
end

script.labels["AnimationE"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:58
    ctx:self():playAnimation("sAnimE", "AnimationF") -- TH_ORCSGOSSIP.scr:59
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:60
end

script.labels["AnimationF"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:61
    ctx:self():playAnimation("sAnimF", "DoTheTalk") -- TH_ORCSGOSSIP.scr:62
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:63
end

script.labels["Main2"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:65
    ctx:addTrigger("Go", "Start") -- TH_ORCSGOSSIP.scr:67
    ctx:addTrigger("Stop", "TurnOff") -- TH_ORCSGOSSIP.scr:68
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_ORCSGOSSIP.scr:69
    do return ctx:exit("TRUE") end -- TH_ORCSGOSSIP.scr:70
end

script.labels["Main"] = function(ctx)
    -- TH_ORCSGOSSIP.scr:72
    ctx:getParam(0, "sAnimA") -- TH_ORCSGOSSIP.scr:74
    ctx:getParam(1, "sAnimB") -- TH_ORCSGOSSIP.scr:75
    ctx:getParam(2, "sAnimC") -- TH_ORCSGOSSIP.scr:76
    ctx:getParam(3, "sAnimD") -- TH_ORCSGOSSIP.scr:77
    ctx:getParam(4, "sAnimE") -- TH_ORCSGOSSIP.scr:78
    ctx:getParam(5, "sAnimF") -- TH_ORCSGOSSIP.scr:79
    ctx:onEvent("OnPostStartWorld", "Main2") -- TH_ORCSGOSSIP.scr:80
    do return ctx:exit("") end -- TH_ORCSGOSSIP.scr:81
end

return script
