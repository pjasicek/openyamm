-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TRAININGHALLEXIT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- TrainingHallExit.scr
-- timmy
-- gives key for successful completion of training hall
-- edited by Bones 3/27/03
-- TELP Patch 1.3 -- move reward to TRAININGENTER.SCR
script.labels["OnTouch"] = function(ctx)
    -- TRAININGHALLEXIT.scr:15
    if not ctx:hasKey(301) then -- TRAININGHALLEXIT.scr:18-19
        do return ctx:exit("") end -- TRAININGHALLEXIT.scr:20
        ctx:giveKey(301) -- TRAININGHALLEXIT.scr:21
        ctx:command("giveattribute", "0 5 1") -- TRAININGHALLEXIT.scr:22
        ctx:command("giveattribute", "1 5 1") -- TRAININGHALLEXIT.scr:23
        ctx:giveExp(20000) -- TRAININGHALLEXIT.scr:24
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- TRAININGHALLEXIT.scr:25
        do return ctx:exit("") end -- TRAININGHALLEXIT.scr:26
    end -- TRAININGHALLEXIT.scr:27
    do return ctx:exit("") end -- TRAININGHALLEXIT.scr:28
end

script.labels["OnExit"] = function(ctx)
    -- TRAININGHALLEXIT.scr:31
    do return ctx:exit("") end -- TRAININGHALLEXIT.scr:34
end

script.labels["Main"] = function(ctx)
    -- TRAININGHALLEXIT.scr:37
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("ontouchnotify", "Ontouch") -- TRAININGHALLEXIT.scr:42
    do return ctx:exit("") end -- TRAININGHALLEXIT.scr:45
end

return script
