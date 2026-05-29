-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_TRAININGORCCOMMANDER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_TrainingOrcCommander.scr
-- Karl Drown 11-17-01
-- Orc Warrior trainer and motivator.
script.labels["Start"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:16
    ctx:state().bIsTraining = true -- TH_TRAININGORCCOMMANDER.scr:18
    mm9.gosub(script, ctx, "StartTraining") -- TH_TRAININGORCCOMMANDER.scr:19
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:20
end

script.labels["TurnOff"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:22
    ctx:wait(1, 1, "DoNothing") -- TH_TRAININGORCCOMMANDER.scr:24
    ctx:state().bIsTraining = false -- TH_TRAININGORCCOMMANDER.scr:25
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:26
end

script.labels["CommandTwo"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:28
    ctx:playSound("Sounds\\AnimSounds\\LizardOrcwince1.wav", "DoNothing", 1000, 1500, "FALSE", 100) -- TH_TRAININGORCCOMMANDER.scr:30
    ctx:self():playAnimation("Taunt", "StartTraining") -- TH_TRAININGORCCOMMANDER.scr:31
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:32
end

script.labels["Relax"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:34
    ctx:self():playAnimation("Stand", "CommandTwo") -- TH_TRAININGORCCOMMANDER.scr:36
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:37
end

script.labels["CommandOne"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:39
    ctx:playSound("Sounds\\AnimSounds\\LizardOrcfidget3.wav", "DoNothing", 1000, 1500, "FALSE", 100) -- TH_TRAININGORCCOMMANDER.scr:41
    ctx:self():playAnimation("Fidget2", "Relax") -- TH_TRAININGORCCOMMANDER.scr:42
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:43
end

script.labels["StartTraining"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:45
    if ctx:condition("bIsTraining==FALSE") then -- TH_TRAININGORCCOMMANDER.scr:47
        do return ctx:exit("") end -- TH_TRAININGORCCOMMANDER.scr:48
    end -- TH_TRAININGORCCOMMANDER.scr:49
    ctx:self():playAnimation("Stand", "CommandOne") -- TH_TRAININGORCCOMMANDER.scr:50
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:51
end

script.labels["Main2"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:53
    ctx:addTrigger("Train", "Start") -- TH_TRAININGORCCOMMANDER.scr:55
    ctx:addTrigger("Stop", "TurnOff") -- TH_TRAININGORCCOMMANDER.scr:56
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_TRAININGORCCOMMANDER.scr:57
    do return ctx:exit("TRUE") end -- TH_TRAININGORCCOMMANDER.scr:58
end

script.labels["Main"] = function(ctx)
    -- TH_TRAININGORCCOMMANDER.scr:60
    ctx:onEvent("OnPostStartWorld", "Main2") -- TH_TRAININGORCCOMMANDER.scr:62
    do return ctx:exit("") end -- TH_TRAININGORCCOMMANDER.scr:63
end

return script
