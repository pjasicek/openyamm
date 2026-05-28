-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_TRAININGORCS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_TrainingOrcs.scr
-- Karl Drown 11-17-01
-- Orcs practicing their attacks - KungFu style.
script.labels["Start"] = function(ctx)
    -- TH_TRAININGORCS.scr:17
    ctx:command("bistraining", "= TRUE") -- TH_TRAININGORCS.scr:19
    mm9.gosub(script, ctx, "ParadiddleStart") -- TH_TRAININGORCS.scr:20
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:21
end

script.labels["TurnOff"] = function(ctx)
    -- TH_TRAININGORCS.scr:23
    ctx:command("wait", "1, 1, DoNothing") -- TH_TRAININGORCS.scr:25
    ctx:command("bistraining", "= FALSE") -- TH_TRAININGORCS.scr:26
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:27
end

script.labels["ParadiddleStart"] = function(ctx)
    -- TH_TRAININGORCS.scr:30
    if ctx:condition("bIsTraining==FALSE") then -- TH_TRAININGORCS.scr:32
        do return ctx:exit("") end -- TH_TRAININGORCS.scr:33
    end -- TH_TRAININGORCS.scr:34
    ctx:command("playanim", "Taunt, RightA") -- TH_TRAININGORCS.scr:35
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:36
end

script.labels["RightA"] = function(ctx)
    -- TH_TRAININGORCS.scr:38
    ctx:command("playanim", "HAttack1, LeftA") -- TH_TRAININGORCS.scr:39
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:40
end

script.labels["LeftA"] = function(ctx)
    -- TH_TRAININGORCS.scr:41
    ctx:command("playanim", "HAttack2, Right1") -- TH_TRAININGORCS.scr:42
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:43
end

script.labels["Right1"] = function(ctx)
    -- TH_TRAININGORCS.scr:44
    ctx:command("playanim", "HAttack1, Right2") -- TH_TRAININGORCS.scr:45
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:46
end

script.labels["Right2"] = function(ctx)
    -- TH_TRAININGORCS.scr:47
    ctx:command("playanim", "HAttack1, LeftB") -- TH_TRAININGORCS.scr:48
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:49
end

script.labels["LeftB"] = function(ctx)
    -- TH_TRAININGORCS.scr:51
    ctx:command("playanim", "HAttack2, RightB") -- TH_TRAININGORCS.scr:52
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:53
end

script.labels["RightB"] = function(ctx)
    -- TH_TRAININGORCS.scr:54
    ctx:command("playanim", "HAttack1, Left1") -- TH_TRAININGORCS.scr:55
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:56
end

script.labels["Left1"] = function(ctx)
    -- TH_TRAININGORCS.scr:57
    ctx:command("playanim", "HAttack2, Left2") -- TH_TRAININGORCS.scr:58
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:59
end

script.labels["Left2"] = function(ctx)
    -- TH_TRAININGORCS.scr:60
    ctx:command("playanim", "HAttack2, ParadiddleStart") -- TH_TRAININGORCS.scr:61
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:62
end

script.labels["Main2"] = function(ctx)
    -- TH_TRAININGORCS.scr:65
    ctx:addTrigger("Train", "Start") -- TH_TRAININGORCS.scr:67
    ctx:addTrigger("Stop", "TurnOff") -- TH_TRAININGORCS.scr:68
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_TRAININGORCS.scr:69
    do return ctx:exit("TRUE") end -- TH_TRAININGORCS.scr:70
end

script.labels["Main"] = function(ctx)
    -- TH_TRAININGORCS.scr:72
    ctx:command("onpoststartworld", "Main2") -- TH_TRAININGORCS.scr:74
    do return ctx:exit("") end -- TH_TRAININGORCS.scr:75
end

return script
