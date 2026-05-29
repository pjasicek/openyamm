-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDRUDE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "guardsounds.inc" }

-- WorkingMonk.scr
-- timmy
-- Makes Monks play working animations
-- 10/23
-- parameters:
-- p0 - name of Rude to do
script.labels["OnAlarm"] = function(ctx)
    -- GUARDRUDE.scr:22
    -- makes guards hostile
    ctx:self():addEnemy("Player") -- GUARDRUDE.scr:26
    do return mm9.gotoLabel(script, ctx, "BaseInit") end -- GUARDRUDE.scr:27
    do return ctx:exit("") end -- GUARDRUDE.scr:28
end

script.labels["Wakeup"] = function(ctx)
    -- GUARDRUDE.scr:31
    ctx:self():playAnimation("Stand", "DoNothing") -- GUARDRUDE.scr:34
    do return ctx:exit("") end -- GUARDRUDE.scr:35
end

script.labels["OnUse"] = function(ctx)
    -- GUARDRUDE.scr:38
    if ctx:condition("nSleeping==TRUE") then -- GUARDRUDE.scr:41
        mm9.gosub(script, ctx, "Wakeup") -- GUARDRUDE.scr:42
    end -- GUARDRUDE.scr:43
    ctx:getParam(0, "g_hobject") -- GUARDRUDE.scr:45
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- GUARDRUDE.scr:46
    ctx:doRude("NPC_ID") -- GUARDRUDE.scr:47
    do return ctx:exit("") end -- GUARDRUDE.scr:48
end

script.labels["OnDamage"] = function(ctx)
    -- GUARDRUDE.scr:51
    if not ctx:hasKey(5006) then -- GUARDRUDE.scr:53-54
        ctx:giveKey(5006) -- GUARDRUDE.scr:55
    end -- GUARDRUDE.scr:56
    ctx:object("AlarmControl"):trigger("Alarm") -- GUARDRUDE.scr:57-58
    do return ctx:exit("") end -- GUARDRUDE.scr:59
end

script.labels["OnRude"] = function(ctx)
    -- GUARDRUDE.scr:62
    -- TraceOn
    if ctx:hasKey(5006) then -- GUARDRUDE.scr:67-68
        mm9.gosub(script, ctx, "OnDamage") -- GUARDRUDE.scr:69
        do return ctx:exit("") end -- GUARDRUDE.scr:70
    end -- GUARDRUDE.scr:71
    if ctx:hasKey(5007) then -- GUARDRUDE.scr:75-76
        mm9.gosub(script, ctx, "OnMove") -- GUARDRUDE.scr:77
        do return ctx:exit("") end -- GUARDRUDE.scr:78
    end -- GUARDRUDE.scr:79
    do return ctx:exit("") end -- GUARDRUDE.scr:80
end

script.labels["OnMove"] = function(ctx)
    -- GUARDRUDE.scr:83
    if ctx:condition("NPC_ID==426") then -- GUARDRUDE.scr:86
        if ctx:hasItem(446) then -- GUARDRUDE.scr:87-88
            do return ctx:exit("") end -- GUARDRUDE.scr:89
        else -- GUARDRUDE.scr:90
            ctx:giveItem(446) -- GUARDRUDE.scr:91
            ctx:traceOff() -- GUARDRUDE.scr:92
        end -- GUARDRUDE.scr:93
        do return ctx:exit("") end -- GUARDRUDE.scr:94
    else -- GUARDRUDE.scr:95
        -- get out of player's way.
        ctx:state().g_hobject = ctx:objectOrNil("L_Marker") -- GUARDRUDE.scr:98
        if ctx:condition("L_Marker==NULL") then -- GUARDRUDE.scr:99
            do return ctx:exit("") end -- GUARDRUDE.scr:100
        end -- GUARDRUDE.scr:101
        ctx:self():walkTo(ctx:object("g_hobject"), 0, "DoNothing") -- GUARDRUDE.scr:102
        do return ctx:exit("") end -- GUARDRUDE.scr:103
    end -- GUARDRUDE.scr:104
    do return ctx:exit("") end -- GUARDRUDE.scr:105
end

script.labels["OnTarget"] = function(ctx)
    -- GUARDRUDE.scr:108
    if ctx:hasKey(5006) then -- GUARDRUDE.scr:111-112
        mm9.gosub(script, ctx, "OnDamage") -- GUARDRUDE.scr:113
        do return ctx:exit("") end -- GUARDRUDE.scr:114
    end -- GUARDRUDE.scr:115
    do return ctx:exit("") end -- GUARDRUDE.scr:116
end

script.labels["StartWork"] = function(ctx)
    -- GUARDRUDE.scr:119
    ctx:randomInt(1, 20, "G_ntemp") -- GUARDRUDE.scr:122
    if ctx:condition("g_ntemp==1") then -- GUARDRUDE.scr:126
        ctx:self():loopAnimation("sleep", 0, "DoNothing") -- GUARDRUDE.scr:127
        ctx:state().nSleeping = true -- GUARDRUDE.scr:128
        do return ctx:exit("") end -- GUARDRUDE.scr:129
    end -- GUARDRUDE.scr:130
    do return ctx:exit("") end -- GUARDRUDE.scr:131
end

script.labels["Main"] = function(ctx)
    -- GUARDRUDE.scr:134
    -- TraceON
    ctx:getParam(0, "NPC_ID") -- GUARDRUDE.scr:140
    ctx:getParam(1, "L_Marker") -- GUARDRUDE.scr:141
    ctx:addTrigger("Use", "Onuse") -- GUARDRUDE.scr:142
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- GUARDRUDE.scr:143
    ctx:onEvent("OnDamage", "OnDamage") -- GUARDRUDE.scr:144
    ctx:addTrigger("Alarm", "ONAlarm") -- GUARDRUDE.scr:145
    ctx:onEvent("OnFoundTarget", "OnTarget") -- GUARDRUDE.scr:146
    mm9.gosub(script, ctx, "GS_Init") -- GUARDRUDE.scr:147
    mm9.gosub(script, ctx, "Startwork") -- GUARDRUDE.scr:148
    do return ctx:exit("") end -- GUARDRUDE.scr:149
end

return script
