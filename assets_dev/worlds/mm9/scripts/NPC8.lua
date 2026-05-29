-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC8.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- NPC8.scr
-- timmy
-- handles Ketil Strongpick's voice and quest stuff.
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC8.scr:26
    if ctx:hasKey(9510) then -- NPC8.scr:29-30
        ctx:state().Walking = true -- NPC8.scr:31
        ctx:self():setTarget(ctx:object("L_htarget")) -- NPC8.scr:32
        ctx:set("L_Marker", "Marker3") -- NPC8.scr:33
        ctx:wait(1, .5, "OnWalkTo") -- NPC8.scr:34
        do return ctx:exit("") end -- NPC8.scr:35
    end -- NPC8.scr:36
    do return ctx:exit("") end -- NPC8.scr:38
end

script.labels["OnWalkTo"] = function(ctx)
    -- NPC8.scr:41
    if ctx:condition("Walking==TRUE") then -- NPC8.scr:46
        ctx:onEvent("OnTargetBeyondDist", 256, "OnStop") -- NPC8.scr:47
        ctx:state().g_hobject = ctx:objectOrNil("L_Marker") -- NPC8.scr:48
        ctx:self():walkTo(ctx:object("g_hobject"), 8, "OnExit") -- NPC8.scr:49
        ctx:onEvent("OnLostTarget", "OnLost") -- NPC8.scr:50
        mm9.gosub(script, ctx, "WalkCheck") -- NPC8.scr:51
        do return ctx:exit("") end -- NPC8.scr:52
    end -- NPC8.scr:53
    do return ctx:exit("") end -- NPC8.scr:54
end

script.labels["WalkCheck"] = function(ctx)
    -- NPC8.scr:57
    if ctx:condition("walking==TRUE") then -- NPC8.scr:59
        ctx:state().g_ntemp = ctx:self():isMoving() -- NPC8.scr:60
        if ctx:condition("g_ntemp==FALSE") then -- NPC8.scr:61
            mm9.gosub(script, ctx, "OnWalkto") -- NPC8.scr:62
        end -- NPC8.scr:63
        ctx:wait(2, 1, "WalkCheck") -- NPC8.scr:64
    end -- NPC8.scr:65
    do return ctx:exit("") end -- NPC8.scr:66
end

script.labels["OnUse"] = function(ctx)
    -- NPC8.scr:70
    ctx:getParam(0, "L_hTarget") -- NPC8.scr:75
    ctx:playSound("sound", "Onexit", 100, 240, "FALSE", 100) -- NPC8.scr:76
    do return ctx:exit("") end -- NPC8.scr:77
end

script.labels["OnStop"] = function(ctx)
    -- NPC8.scr:80
    if ctx:condition("panic==TRUE") then -- NPC8.scr:82
        do return ctx:exit("") end -- NPC8.scr:83
    end -- NPC8.scr:84
    ctx:self():stop() -- NPC8.scr:86
    ctx:self():setTarget(ctx:object("L_HTarget")) -- NPC8.scr:87
    ctx:self():faceObject(ctx:object("L_HTarget"), 200, "DoNothing") -- NPC8.scr:88
    ctx:onEvent("OnTargetWithinDist", 256, "OnWalkTo") -- NPC8.scr:89
    do return ctx:exit("") end -- NPC8.scr:90
end

script.labels["OnExit"] = function(ctx)
    -- NPC8.scr:93
    ctx:giveKey(9511) -- NPC8.scr:96
    ctx:state().panic = false -- NPC8.scr:97
    ctx:state().walking = false -- NPC8.scr:98
    do return ctx:exit("") end -- NPC8.scr:99
end

script.labels["OnRunAway"] = function(ctx)
    -- NPC8.scr:103
    -- finds the closest safe marker
    -- and runs to it
    ctx:self():stop() -- NPC8.scr:108
    ctx:state().Panic = true -- NPC8.scr:109
    ctx:state().g_hobject = ctx:objectOrNil("Marker0") -- NPC8.scr:110
    ctx:state().Marker_Dist1 = ctx:self():aiDistanceTo(ctx:object("g_hobject")) -- NPC8.scr:111
    ctx:state().g_hobject = ctx:objectOrNil("Marker1") -- NPC8.scr:112
    ctx:state().Marker_Dist2 = ctx:self():aiDistanceTo(ctx:object("g_hobject")) -- NPC8.scr:113
    if ctx:condition("Marker_Dist1<Marker_Dist2") then -- NPC8.scr:115
        ctx:state().g_hobject = ctx:objectOrNil("Marker0") -- NPC8.scr:116
        ctx:self():runTo(ctx:object("g_hobject"), 8, "OnExit") -- NPC8.scr:117
        do return ctx:exit("") end -- NPC8.scr:118
    else -- NPC8.scr:119
        ctx:state().g_hobject = ctx:objectOrNil("Marker1") -- NPC8.scr:120
        ctx:self():runTo(ctx:object("g_hobject"), 8, "OnExit") -- NPC8.scr:121
        do return ctx:exit("") end -- NPC8.scr:122
    end -- NPC8.scr:123
    do return ctx:exit("") end -- NPC8.scr:124
end

script.labels["OnLost"] = function(ctx)
    -- NPC8.scr:127
    do return ctx:exit("TRUE") end -- NPC8.scr:130
end

script.labels["Main"] = function(ctx)
    -- NPC8.scr:133
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- NPC8.scr:139
    ctx:getParam(1, "Params") -- NPC8.scr:140
    ctx:getParam(2, "g_ntemp") -- NPC8.scr:141
    ctx:self():loopAnimation("Params", "g_ntemp", "ONExit") -- NPC8.scr:142
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC8.scr:143
    ctx:addTrigger("Use", "OnUse") -- NPC8.scr:144
    ctx:self():attachProp("MonkHammer.ABC", "MonkHammer.dtx", "RHand1", ctx:object("g_hobject2")) -- NPC8.scr:145
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPC8.scr:146
    ctx:onEvent("OnDamage", "OnRunAway") -- NPC8.scr:147
    do return ctx:exit("") end -- NPC8.scr:149
end

return script
