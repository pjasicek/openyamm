-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_JOUSTTRELLBORG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "TrainingHostility.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- TH_JoustTrellborg.scr
-- Karl Drown 11-18-01
-- Trellborg that plays animations during jousting
-- pranks.
script.labels["Start"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:26
    ctx:command("bisjousting", "= TRUE") -- TH_JOUSTTRELLBORG.scr:28
    mm9.gosub(script, ctx, "StartAnimations") -- TH_JOUSTTRELLBORG.scr:29
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:30
end

script.labels["TurnOff"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:32
    ctx:command("wait", "1, 1, DoNothing") -- TH_JOUSTTRELLBORG.scr:34
    ctx:command("bisjousting", "= FALSE") -- TH_JOUSTTRELLBORG.scr:35
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:36
end

script.labels["AnimationA"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:39
    ctx:command("playanim", "sAnimA, AnimationB") -- TH_JOUSTTRELLBORG.scr:40
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:41
end

script.labels["AnimationB"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:42
    ctx:command("playanim", "sAnimB, AnimationC") -- TH_JOUSTTRELLBORG.scr:43
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:44
end

script.labels["AnimationC"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:45
    ctx:command("playanim", "sAnimC, AnimationD") -- TH_JOUSTTRELLBORG.scr:46
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:47
end

script.labels["AnimationD"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:48
    ctx:command("playanim", "sAnimD, StartAnimations") -- TH_JOUSTTRELLBORG.scr:49
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:50
end

script.labels["StartAnimations"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:55
    if ctx:condition("bIsJousting==FALSE") then -- TH_JOUSTTRELLBORG.scr:57
        do return ctx:exit("") end -- TH_JOUSTTRELLBORG.scr:58
    end -- TH_JOUSTTRELLBORG.scr:59
    ctx:command("walkto", "hMarker, 3, AnimationA") -- TH_JOUSTTRELLBORG.scr:60
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:61
end

script.labels["Main2"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:64
    ctx:addTrigger("Go", "Start") -- TH_JOUSTTRELLBORG.scr:66
    ctx:addTrigger("Stop", "TurnOff") -- TH_JOUSTTRELLBORG.scr:67
    ctx:addTrigger("BackPos", "StartAnimations") -- TH_JOUSTTRELLBORG.scr:68
    ctx:command("getobjecthandle", "sMarker, hMarker") -- TH_JOUSTTRELLBORG.scr:69
    mm9.gosub(script, ctx, "InitTrainingHostility") -- TH_JOUSTTRELLBORG.scr:70
    do return ctx:exit("TRUE") end -- TH_JOUSTTRELLBORG.scr:71
end

script.labels["Main"] = function(ctx)
    -- TH_JOUSTTRELLBORG.scr:73
    ctx:getParam(0, "sAnimA") -- TH_JOUSTTRELLBORG.scr:75
    ctx:getParam(1, "sAnimB") -- TH_JOUSTTRELLBORG.scr:76
    ctx:getParam(2, "sAnimC") -- TH_JOUSTTRELLBORG.scr:77
    ctx:getParam(3, "sAnimD") -- TH_JOUSTTRELLBORG.scr:78
    ctx:getParam(4, "sMarker") -- TH_JOUSTTRELLBORG.scr:79
    ctx:command("onpoststartworld", "Main2") -- TH_JOUSTTRELLBORG.scr:80
    do return ctx:exit("") end -- TH_JOUSTTRELLBORG.scr:81
end

return script
