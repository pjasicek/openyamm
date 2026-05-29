-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC420.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "MonkHostility.inc" }

-- NPC420.scr
-- timmy
-- handles organ player voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC420.scr:13
    mm9.gosub(script, ctx, "PlaySong") -- NPC420.scr:16
    do return ctx:exit("") end -- NPC420.scr:19
end

script.labels["TurnHostilityOn"] = function(ctx)
    -- NPC420.scr:22
    mm9.gosub(script, ctx, "CancelSound") -- NPC420.scr:24
    mm9.gosub(script, ctx, "TurnHostilityOn") -- NPC420.scr:25
    do return ctx:exit("TRUE") end -- NPC420.scr:27
end

script.labels["PlaySong"] = function(ctx)
    -- NPC420.scr:30
    if ctx:hasKey(9506) then -- NPC420.scr:33-34
        ctx:state().g_hobject = ctx:objectOrNil("E2") -- NPC420.scr:35
        ctx:self():faceObject(ctx:object("g_hobject"), 180, "Play") -- NPC420.scr:36
        ctx:state().bIsPlaying = true -- NPC420.scr:37
        do return ctx:exit("") end -- NPC420.scr:38
    end -- NPC420.scr:39
    do return ctx:exit("") end -- NPC420.scr:41
end

script.labels["PlayAnim"] = function(ctx)
    -- NPC420.scr:44
    ctx:self():loopAnimation("play", 0, "DoNothing") -- NPC420.scr:46
    ctx:wait(2, 24, "Onexit") -- NPC420.scr:47
    do return ctx:exit("") end -- NPC420.scr:48
end

-- SJR
script.labels["Play"] = function(ctx)
    -- NPC420.scr:54
    ctx:object("Organ"):trigger("off") -- NPC420.scr:57-58
    ctx:self():loopAnimation("play", 0, "DoNothing") -- NPC420.scr:61
    -- SJR
    ctx:playSoundHandle("sounds\\Events\\HeroesPipe441.wav", "hSound", 1000, "FALSE", 100) -- NPC420.scr:63
    ctx:takeKey(9506) -- NPC420.scr:65
    ctx:wait(1, 24, "Onexit") -- NPC420.scr:66
    do return ctx:exit("") end -- NPC420.scr:67
end

-- SJR
script.labels["CancelSound"] = function(ctx)
    -- NPC420.scr:71
    ctx:object("Organ"):trigger("off") -- NPC420.scr:74-75
    ctx:isSoundDone("hSound", "bIsPlaying") -- NPC420.scr:77
    if ctx:condition("bIsPlaying==FALSE") then -- NPC420.scr:78
        ctx:killSound("hSound") -- NPC420.scr:79
    end -- NPC420.scr:80
    do return ctx:exit(1) end -- NPC420.scr:81
end

script.labels["OnUse"] = function(ctx)
    -- NPC420.scr:84
    if ctx:condition("bIsPlaying==TRUE") then -- NPC420.scr:87
        do return ctx:exit("") end -- NPC420.scr:88
    end -- NPC420.scr:89
    ctx:getParam(0, "g_hobject") -- NPC420.scr:92
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- NPC420.scr:93
    ctx:doRude(420) -- NPC420.scr:94
    ctx:playSound("voices\\NPC\\NPC_177.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC420.scr:95
    do return ctx:exit("") end -- NPC420.scr:96
end

script.labels["OnExit"] = function(ctx)
    -- NPC420.scr:99
    mm9.gosub(script, ctx, "CancelSound") -- NPC420.scr:101
    ctx:state().bIsPlaying = false -- NPC420.scr:102
    ctx:self():playAnimation("stand", "DoNothing") -- NPC420.scr:103
    do return ctx:exit("") end -- NPC420.scr:104
end

script.labels["Init"] = function(ctx)
    -- NPC420.scr:107
    mm9.gosub(script, ctx, "InitMonkHostility") -- NPC420.scr:110
    do return ctx:exit("") end -- NPC420.scr:111
end

script.labels["Main"] = function(ctx)
    -- NPC420.scr:113
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC420.scr:120
    ctx:addTrigger("Play", "PlayAnim") -- NPC420.scr:121
    ctx:addTrigger("Use", "OnUse") -- NPC420.scr:122
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC420.scr:123
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC420.scr:124
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC420.scr:125
    ctx:wait(1, .1, "Init") -- NPC420.scr:126
    do return ctx:exit("") end -- NPC420.scr:127
end

return script
