-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPTHROWER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "flags.inc" }

-- PropThrower.scr
-- Jeff Leggett
-- 12/06/2001
-- Script that can turn a prop into a projectile...
script.labels["KeepRotating"] = function(ctx)
    -- PROPTHROWER.scr:36
    if ctx:condition("bThrowing==TRUE") then -- PROPTHROWER.scr:38
        ctx:self():rotate("rotX", "rotY", "rotZ", 180, 450, "KeepRotating") -- PROPTHROWER.scr:39
    end -- PROPTHROWER.scr:40
    do return ctx:exit("") end -- PROPTHROWER.scr:42
end

script.labels["DoRotation"] = function(ctx)
    -- PROPTHROWER.scr:45
    -- GetRandomFloat 0.5,1,rotX
    -- GetRandomFloat 0.5,1,rotY
    -- GetRandomFloat 0.5,1,rotZ
    ctx:state().rotX = 0 -- PROPTHROWER.scr:50
    ctx:state().rotY = 0 -- PROPTHROWER.scr:51
    ctx:state().rotZ = 1 -- PROPTHROWER.scr:52
    mm9.gosub(script, ctx, "KeepRotating") -- PROPTHROWER.scr:53
    do return ctx:exit("") end -- PROPTHROWER.scr:54
end

script.labels["ThrowAtPlayer"] = function(ctx)
    -- PROPTHROWER.scr:57
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:59
    if ctx:condition("g_hObject!=hRequester") then -- PROPTHROWER.scr:61
        if ctx:condition("hRequester!=NULL") then -- PROPTHROWER.scr:62
            ctx:self():unlink(ctx:object("hRequester")) -- PROPTHROWER.scr:63
        end -- PROPTHROWER.scr:64
        ctx:set("hRequester", "g_hObject") -- PROPTHROWER.scr:65
        ctx:self():link(ctx:object("hRequester")) -- PROPTHROWER.scr:66
    end -- PROPTHROWER.scr:67
    ctx:state().targetX, ctx:state().targetY, ctx:state().targetZ = ctx:player():pos() -- PROPTHROWER.scr:71
    ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = ctx:self():pos() -- PROPTHROWER.scr:72
    ctx:state().targetX, ctx:state().targetY, ctx:state().targetZ = ctx:vecSub("targetX", "targetY", "targetZ", "g_posX", "g_posY", "g_posZ") -- PROPTHROWER.scr:74
    ctx:state().targetX, ctx:state().targetY, ctx:state().targetZ = ctx:vecNorm("targetX", "targetY", "targetZ") -- PROPTHROWER.scr:75
    ctx:self():faceDir("targetX", "targetY", "targetZ") -- PROPTHROWER.scr:76
    ctx:state().targetX, ctx:state().targetY, ctx:state().targetZ = ctx:vecScale("targetX", "targetY", "targetZ", 450) -- PROPTHROWER.scr:77
    ctx:self():setVelocity("targetX", "targetY", "targetZ") -- PROPTHROWER.scr:79
    ctx:self():setFlag("FLAG_VISIBLE", true) -- PROPTHROWER.scr:80
    ctx:state().bThrowing = true -- PROPTHROWER.scr:82
    ctx:state().bDidDamage = false -- PROPTHROWER.scr:83
    mm9.gosub(script, ctx, "DoRotation") -- PROPTHROWER.scr:85
    ctx:wait(5, 5, "Reset") -- PROPTHROWER.scr:87
    do return ctx:exit("") end -- PROPTHROWER.scr:89
end

script.labels["Reset"] = function(ctx)
    -- PROPTHROWER.scr:92
    if ctx:condition("hRequester!=NULL") then -- PROPTHROWER.scr:95
        ctx:trigger("hRequester", "PropThrowerDone") -- PROPTHROWER.scr:96
    end -- PROPTHROWER.scr:97
    ctx:wait(5, 0, "DoNothing") -- PROPTHROWER.scr:99
    ctx:self():setFlag("FLAG_VISIBLE", false) -- PROPTHROWER.scr:100
    ctx:self():setVelocity(0, 0, 0) -- PROPTHROWER.scr:101
    ctx:state().bThrowing = false -- PROPTHROWER.scr:102
    ctx:wait(7, 0.1, "ResetPosition") -- PROPTHROWER.scr:103
    ctx:state().bDidDamage = false -- PROPTHROWER.scr:105
    do return ctx:exit("") end -- PROPTHROWER.scr:107
end

script.labels["OnTouchNotify"] = function(ctx)
    -- PROPTHROWER.scr:110
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:112
    if ctx:condition("g_hObject==hRequester") then -- PROPTHROWER.scr:114
        do return ctx:exit("FALSE") end -- PROPTHROWER.scr:115
    end -- PROPTHROWER.scr:116
    if ctx:condition("bDidDamage==FALSE") then -- PROPTHROWER.scr:118
        ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("Actor") -- PROPTHROWER.scr:119
        if ctx:condition("g_bTemp==TRUE") then -- PROPTHROWER.scr:120
            ctx:state().bDidDamage = true -- PROPTHROWER.scr:121
            ctx:randomInt(1, 3, "g_nTemp") -- PROPTHROWER.scr:122
            ctx:object("g_hObject"):damage("g_nTemp", 0) -- PROPTHROWER.scr:123
        end -- PROPTHROWER.scr:124
    end -- PROPTHROWER.scr:125
    -- TODO:Play sound here...
    mm9.gosub(script, ctx, "Reset") -- PROPTHROWER.scr:130
    do return ctx:exit("") end -- PROPTHROWER.scr:132
end

script.labels["ResetPosition"] = function(ctx)
    -- PROPTHROWER.scr:136
    ctx:self():setPos("homeX", "homeY", "homeZ") -- PROPTHROWER.scr:139
    do return ctx:exit("") end -- PROPTHROWER.scr:141
end

script.labels["OnLinkBroken"] = function(ctx)
    -- PROPTHROWER.scr:144
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:147
    if ctx:condition("g_hObject==hRequester") then -- PROPTHROWER.scr:148
        ctx:state().hRequester = nil -- PROPTHROWER.scr:149
    end -- PROPTHROWER.scr:150
    do return ctx:exit("") end -- PROPTHROWER.scr:152
end

script.labels["Main"] = function(ctx)
    -- PROPTHROWER.scr:155
    ctx:self():setFlag("FLAG_VISIBLE", false) -- PROPTHROWER.scr:158
    ctx:self():setFlag("FLAG_SOLID", false) -- PROPTHROWER.scr:159
    ctx:state().homeX, ctx:state().homeY, ctx:state().homeZ = ctx:self():pos() -- PROPTHROWER.scr:161
    ctx:addTrigger("ThrowAtPlayer", "ThrowAtPlayer") -- PROPTHROWER.scr:163
    ctx:addTrigger("GetPlayer", "ThrowAtPlayer") -- PROPTHROWER.scr:164
    ctx:addTrigger("ResetPosition", "ResetPosition") -- PROPTHROWER.scr:165
    ctx:onEvent("OnTouchNotify", "OnTouchNotify") -- PROPTHROWER.scr:166
    ctx:onEvent("OnObjectLinkBroken", "OnLinkBroken") -- PROPTHROWER.scr:167
    do return ctx:exit("") end -- PROPTHROWER.scr:169
end

return script
