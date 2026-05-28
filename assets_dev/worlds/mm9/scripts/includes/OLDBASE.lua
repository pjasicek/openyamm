-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "OLDBASE.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "aiglobals.inc" }

-- base.inc
-- This include file contains base monster
-- handling.  Basically, the monster sees
-- the player.  Runs after him and keeps
-- attacking.  Nothing fancy here.
-- NOTE: Be sure to gosub InitBase in your
-- :main routine.
script.labels["BaseChaseTick"] = function(ctx)
    -- OLDBASE.inc:25
    if ctx:condition("g_bChasing==FALSE") then -- OLDBASE.inc:28
        do return ctx:exit("") end -- OLDBASE.inc:29
    end -- OLDBASE.inc:30
    if ctx:condition("g_hTarget==NULL") then -- OLDBASE.inc:32
        do return ctx:exit("") end -- OLDBASE.inc:33
    end -- OLDBASE.inc:34
    ctx:command("getdistance", "g_hTarget, g_nDist1") -- OLDBASE.inc:36
    if ctx:condition("g_bRunning==TRUE") then -- OLDBASE.inc:38
        if ctx:condition("g_nDist1 < 120.0") then -- OLDBASE.inc:39
            ctx:command("set", "g_sOut, g_nDist1") -- OLDBASE.inc:40
            ctx:command("debugout", "g_sOut") -- OLDBASE.inc:41
            -- Time to Walk!
            ctx:command("set", "g_bRunning, FALSE") -- OLDBASE.inc:43
            ctx:command("walkto", "g_hTarget") -- OLDBASE.inc:44
        end -- OLDBASE.inc:45
    else -- OLDBASE.inc:46
        if ctx:condition("g_nDist1 > 200.0") then -- OLDBASE.inc:47
            ctx:command("set", "g_sOut, g_nDist1") -- OLDBASE.inc:48
            ctx:command("set", "g_bRunning, TRUE") -- OLDBASE.inc:49
            ctx:command("runto", "g_hTarget") -- OLDBASE.inc:50
        end -- OLDBASE.inc:51
    end -- OLDBASE.inc:52
    ctx:command("wait", "0.1, BaseChaseTick") -- OLDBASE.inc:54
    do return ctx:exit("") end -- OLDBASE.inc:56
end

script.labels["BaseGoGetHim"] = function(ctx)
    -- OLDBASE.inc:59
    ctx:command("target", "g_hTarget") -- OLDBASE.inc:61
    -- Run after him. Don't need a callback because
    -- we have OnAttackReady call BaseAttackReady
    -- when we are close enough...
    ctx:command("set", "g_bRunning, TRUE") -- OLDBASE.inc:69
    ctx:command("set", "g_bChasing, TRUE") -- OLDBASE.inc:70
    ctx:command("runto", "g_hTarget") -- OLDBASE.inc:71
    ctx:command("wait", "0.1, BaseChaseTick") -- OLDBASE.inc:73
    do return ctx:exit(1) end -- OLDBASE.inc:75
end

script.labels["BaseRotationDone"] = function(ctx)
    -- OLDBASE.inc:78
    ctx:command("target", "g_hTarget") -- OLDBASE.inc:80
    ctx:command("playanimation", "Threat, FALSE, BaseGoGetHim") -- OLDBASE.inc:81
    do return ctx:exit("") end -- OLDBASE.inc:83
end

script.labels["BaseFoundPlayer"] = function(ctx)
    -- OLDBASE.inc:85
    -- Found a player, set it as our current
    -- target and run after him!
    if ctx:condition("g_hTarget!=0") then -- OLDBASE.inc:91
        do return ctx:exit("") end -- OLDBASE.inc:92
    end -- OLDBASE.inc:93
    ctx:command("getplayerhandle", "g_hTarget") -- OLDBASE.inc:95
    if ctx:condition("g_hTarget == 0") then -- OLDBASE.inc:97
        -- This shouldn't happen, but you can't be too careful!
        do return ctx:exit("") end -- OLDBASE.inc:101
    end -- OLDBASE.inc:102
    ctx:command("set", "g_bInAttackRange, 0") -- OLDBASE.inc:104
    -- Turn and face target before running after him!
    ctx:command("faceobject", "g_hTarget, 360, BaseRotationDone") -- OLDBASE.inc:107
    do return ctx:exit("") end -- OLDBASE.inc:109
end

script.labels["BaseAttackReady"] = function(ctx)
    -- OLDBASE.inc:112
    -- We are now in attack range (for our
    -- currently selected weapon) and ready
    -- to attack.  So let's do it!
    ctx:command("set", "g_bChasing, FALSE") -- OLDBASE.inc:119
    -- No callback is necessary here, AttackReady
    -- will get called when our attack is done
    -- If the player goes out of range while
    -- we were attacking, BaseTargetOutOfRange
    -- will get called...
    ctx:command("set", "g_bInAttackRange, 1") -- OLDBASE.inc:127
    ctx:command("attack", "") -- OLDBASE.inc:129
    do return ctx:exit("") end -- OLDBASE.inc:131
end

script.labels["BaseTargetOutOfRange"] = function(ctx)
    -- OLDBASE.inc:134
    -- Target moved out of our weapon range.
    -- Go after him!
    ctx:command("debugout", "Base Target Out Of Range") -- OLDBASE.inc:141
    ctx:command("set", "g_bInAttackRange, 0") -- OLDBASE.inc:143
    mm9.gosub(script, ctx, "BaseGoGetHim") -- OLDBASE.inc:145
    do return ctx:exit("") end -- OLDBASE.inc:147
end

script.labels["BaseLostTarget"] = function(ctx)
    -- OLDBASE.inc:150
    -- We've lost the target, so let's go idle.
    ctx:command("set", "g_hTarget, 0") -- OLDBASE.inc:155
    ctx:command("setidle", "") -- OLDBASE.inc:156
    do return ctx:exit("") end -- OLDBASE.inc:158
end

script.labels["BaseStuckDone"] = function(ctx)
    -- OLDBASE.inc:161
    -- This is called when a stuck animation
    -- has finished... We'll just re-attempt
    -- to run after our target...
    if ctx:condition("g_hTarget!=0") then -- OLDBASE.inc:168
        mm9.gosub(script, ctx, "BaseGoGetHim") -- OLDBASE.inc:169
    end -- OLDBASE.inc:170
    do return ctx:exit("") end -- OLDBASE.inc:172
end

script.labels["BaseDamageDone"] = function(ctx)
    -- OLDBASE.inc:175
    -- We were attacked, now we want to run
    -- after whoever attacked us!
    if ctx:condition("g_hTarget==0") then -- OLDBASE.inc:182
        ctx:command("set", "g_hTarget, g_hAttacker") -- OLDBASE.inc:183
    else -- OLDBASE.inc:184
        if ctx:condition("g_hAttacker!=0") then -- OLDBASE.inc:185
            if ctx:condition("g_hAttacker!=g_hTarget") then -- OLDBASE.inc:186
                -- 70% chance we'll switch to the damager
                ctx:command("set", "g_nTemp, 70") -- OLDBASE.inc:188
                if ctx:condition("g_bInAttackRange==1") then -- OLDBASE.inc:189
                    -- we're already in attack range of our current target
                    -- so lower chances of switching
                    ctx:command("set", "g_nTemp, 10") -- OLDBASE.inc:192
                end -- OLDBASE.inc:193
                ctx:command("getdistance", "g_hTarget, g_nDist1") -- OLDBASE.inc:195
                ctx:command("getdistance", "g_hAttacker, g_nDist2") -- OLDBASE.inc:196
                if ctx:condition("g_nDist2 > g_nDist1") then -- OLDBASE.inc:198
                    -- reduce odds even further...
                    ctx:command("divide", "g_nTemp, 2") -- OLDBASE.inc:200
                end -- OLDBASE.inc:201
                ctx:command("getrandomint", "0, 100, g_nRandom") -- OLDBASE.inc:203
                if ctx:condition("g_nRandom < g_nTemp") then -- OLDBASE.inc:204
                    -- Okay, we decided to switch our current target to the
                    -- attacker!
                    ctx:command("set", "g_hTarget, g_hAttacker") -- OLDBASE.inc:209
                end -- OLDBASE.inc:210
            end -- OLDBASE.inc:211
        end -- OLDBASE.inc:212
    end -- OLDBASE.inc:213
    if ctx:condition("g_hTarget==0") then -- OLDBASE.inc:215
        -- 0 means have the AI do it's default handling of this event.
        do return ctx:exit(0) end -- OLDBASE.inc:216
    end -- OLDBASE.inc:217
    -- Go after the Target...
    mm9.gosub(script, ctx, "BaseGoGetHim") -- OLDBASE.inc:221
    do return ctx:exit("") end -- OLDBASE.inc:223
end

script.labels["BaseDamage"] = function(ctx)
    -- OLDBASE.inc:226
    -- p1 = hAttacker
    -- p2 = HitPoints
    ctx:getParam(0, "g_hAttacker") -- OLDBASE.inc:233
    do return ctx:exit("FALSE") end -- OLDBASE.inc:235
end

script.labels["InitBase"] = function(ctx)
    -- OLDBASE.inc:238
    -- Main intialization code.
    -- This should be called by the actual
    -- script file..
    -- TraceOn
    ctx:command("getmyhandle", "g_hMyObject") -- OLDBASE.inc:247
    -- Setup our event handlers...
    ctx:command("onfoundplayer", "BaseFoundPlayer") -- OLDBASE.inc:252
    ctx:command("onlosttarget", "BaseLostTarget") -- OLDBASE.inc:253
    ctx:command("ontargetoutofrange", "BaseTargetOutOfRange") -- OLDBASE.inc:254
    ctx:command("onattackready", "BaseAttackReady") -- OLDBASE.inc:255
    ctx:command("onstuckdone", "BaseStuckDone") -- OLDBASE.inc:256
    ctx:command("ondamagedone", "BaseDamageDone") -- OLDBASE.inc:257
    ctx:command("ondamage", "BaseDamage") -- OLDBASE.inc:258
    do return ctx:exit("") end -- OLDBASE.inc:260
end

return script
