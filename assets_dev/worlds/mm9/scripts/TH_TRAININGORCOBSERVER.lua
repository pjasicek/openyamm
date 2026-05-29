-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_TRAININGORCOBSERVER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }

-- TH_TrainingOrcObserver.scr
-- Karl Drown 11-17-01
-- Orc Warrior Observing the Orcs training.
script.labels["Start"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:24
    ctx:state().bIsTraining = true -- TH_TRAININGORCOBSERVER.scr:26
    mm9.gosub(script, ctx, "LookAtTrainees") -- TH_TRAININGORCOBSERVER.scr:27
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:28
end

script.labels["TurnOff"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:30
    ctx:wait(1, 1, "DoNothing") -- TH_TRAININGORCOBSERVER.scr:32
    ctx:state().bIsTraining = false -- TH_TRAININGORCOBSERVER.scr:33
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:34
end

script.labels["LookAround"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:37
    ctx:self():stop() -- TH_TRAININGORCOBSERVER.scr:39
    ctx:self():playAnimation("Fidget1", "LookAtTrainees") -- TH_TRAININGORCOBSERVER.scr:40
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:41
end

script.labels["Relax"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:43
    ctx:self():stop() -- TH_TRAININGORCOBSERVER.scr:45
    ctx:state().hCommander = ctx:objectOrNil("sTarget") -- TH_TRAININGORCOBSERVER.scr:46
    ctx:self():faceObject(ctx:object("hCommander"), 180) -- TH_TRAININGORCOBSERVER.scr:47
    ctx:wait(0, 2, "LookAround") -- TH_TRAININGORCOBSERVER.scr:48
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:49
end

script.labels["LookAtTrainees"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:51
    if ctx:condition("bIsTraining==FALSE") then -- TH_TRAININGORCOBSERVER.scr:53
        do return ctx:exit("") end -- TH_TRAININGORCOBSERVER.scr:54
    end -- TH_TRAININGORCOBSERVER.scr:55
    if ctx:condition("bDirection==0") then -- TH_TRAININGORCOBSERVER.scr:57
        ctx:state().bDirection = 1 -- TH_TRAININGORCOBSERVER.scr:58
        ctx:state().hMarker = ctx:objectOrNil("sMarkerA") -- TH_TRAININGORCOBSERVER.scr:59
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Relax") -- TH_TRAININGORCOBSERVER.scr:60
    else -- TH_TRAININGORCOBSERVER.scr:61
        ctx:state().bDirection = 0 -- TH_TRAININGORCOBSERVER.scr:62
        ctx:state().hMarker = ctx:objectOrNil("sMarkerB") -- TH_TRAININGORCOBSERVER.scr:63
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Relax") -- TH_TRAININGORCOBSERVER.scr:64
    end -- TH_TRAININGORCOBSERVER.scr:65
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:66
end

script.labels["Main2"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:69
    ctx:addTrigger("Train", "Start") -- TH_TRAININGORCOBSERVER.scr:71
    ctx:addTrigger("Stop", "TurnOff") -- TH_TRAININGORCOBSERVER.scr:72
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_TRAININGORCOBSERVER.scr:73
    do return ctx:exit("TRUE") end -- TH_TRAININGORCOBSERVER.scr:74
end

script.labels["Main"] = function(ctx)
    -- TH_TRAININGORCOBSERVER.scr:76
    ctx:getParam(0, "sMarkerA") -- TH_TRAININGORCOBSERVER.scr:78
    ctx:getParam(1, "sMarkerB") -- TH_TRAININGORCOBSERVER.scr:79
    ctx:getParam(2, "sTarget") -- TH_TRAININGORCOBSERVER.scr:80
    ctx:onEvent("OnPostStartWorld", "Main2") -- TH_TRAININGORCOBSERVER.scr:81
    do return ctx:exit("") end -- TH_TRAININGORCOBSERVER.scr:82
end

return script
