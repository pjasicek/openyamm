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
        ctx:command("rotate", "rotX,rotY,rotZ,180,450,KeepRotating") -- PROPTHROWER.scr:39
    end -- PROPTHROWER.scr:40
    do return ctx:exit("") end -- PROPTHROWER.scr:42
end

script.labels["DoRotation"] = function(ctx)
    -- PROPTHROWER.scr:45
    -- GetRandomFloat 0.5,1,rotX
    -- GetRandomFloat 0.5,1,rotY
    -- GetRandomFloat 0.5,1,rotZ
    ctx:command("rotx", "= 0") -- PROPTHROWER.scr:50
    ctx:command("roty", "= 0") -- PROPTHROWER.scr:51
    ctx:command("rotz", "= 1") -- PROPTHROWER.scr:52
    mm9.gosub(script, ctx, "KeepRotating") -- PROPTHROWER.scr:53
    do return ctx:exit("") end -- PROPTHROWER.scr:54
end

script.labels["ThrowAtPlayer"] = function(ctx)
    -- PROPTHROWER.scr:57
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:59
    if ctx:condition("g_hObject!=hRequester") then -- PROPTHROWER.scr:61
        if ctx:condition("hRequester!=NULL") then -- PROPTHROWER.scr:62
            ctx:command("breakobjectlink", "hRequester") -- PROPTHROWER.scr:63
        end -- PROPTHROWER.scr:64
        ctx:command("hrequester", "= g_hObject") -- PROPTHROWER.scr:65
        ctx:command("createobjectlink", "hRequester") -- PROPTHROWER.scr:66
    end -- PROPTHROWER.scr:67
    ctx:command("getplayerhandle", "hPlayer") -- PROPTHROWER.scr:69
    ctx:command("getpos", "hPlayer, targetX,targetY,targetZ") -- PROPTHROWER.scr:71
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- PROPTHROWER.scr:72
    ctx:command("vecsub", "targetX,targetY,targetZ,g_posX,g_posY,g_posZ") -- PROPTHROWER.scr:74
    ctx:command("vecnorm", "targetX,targetY,targetZ") -- PROPTHROWER.scr:75
    ctx:command("facedir", "targetX,targetY,targetZ") -- PROPTHROWER.scr:76
    ctx:command("vecscale", "targetX,targetY,targetZ,450") -- PROPTHROWER.scr:77
    ctx:command("setvelocity", "g_hMyObject,targetX,targetY,targetZ") -- PROPTHROWER.scr:79
    ctx:command("setflag", "g_hMyObject,FLAG_VISIBLE") -- PROPTHROWER.scr:80
    ctx:command("bthrowing", "= TRUE") -- PROPTHROWER.scr:82
    ctx:command("bdiddamage", "= FALSE") -- PROPTHROWER.scr:83
    mm9.gosub(script, ctx, "DoRotation") -- PROPTHROWER.scr:85
    ctx:command("wait", "5,5,Reset") -- PROPTHROWER.scr:87
    do return ctx:exit("") end -- PROPTHROWER.scr:89
end

script.labels["Reset"] = function(ctx)
    -- PROPTHROWER.scr:92
    if ctx:condition("hRequester!=NULL") then -- PROPTHROWER.scr:95
        ctx:trigger("hRequester", "PropThrowerDone") -- PROPTHROWER.scr:96
    end -- PROPTHROWER.scr:97
    ctx:command("wait", "5,0,DoNothing") -- PROPTHROWER.scr:99
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- PROPTHROWER.scr:100
    ctx:command("setvelocity", "g_hMyObject,0,0,0") -- PROPTHROWER.scr:101
    ctx:command("bthrowing", "= FALSE") -- PROPTHROWER.scr:102
    ctx:command("wait", "7,0.1,ResetPosition") -- PROPTHROWER.scr:103
    ctx:command("bdiddamage", "= FALSE") -- PROPTHROWER.scr:105
    do return ctx:exit("") end -- PROPTHROWER.scr:107
end

script.labels["OnTouchNotify"] = function(ctx)
    -- PROPTHROWER.scr:110
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:112
    if ctx:condition("g_hObject==hRequester") then -- PROPTHROWER.scr:114
        do return ctx:exit("FALSE") end -- PROPTHROWER.scr:115
    end -- PROPTHROWER.scr:116
    if ctx:condition("bDidDamage==FALSE") then -- PROPTHROWER.scr:118
        ctx:command("isclass", "g_hObject,Actor,g_bTemp") -- PROPTHROWER.scr:119
        if ctx:condition("g_bTemp==TRUE") then -- PROPTHROWER.scr:120
            ctx:command("bdiddamage", "= TRUE") -- PROPTHROWER.scr:121
            ctx:command("getrandomint", "1,3,g_nTemp") -- PROPTHROWER.scr:122
            ctx:command("damage", "g_hObject,g_nTemp,0") -- PROPTHROWER.scr:123
        end -- PROPTHROWER.scr:124
    end -- PROPTHROWER.scr:125
    -- TODO:Play sound here...
    mm9.gosub(script, ctx, "Reset") -- PROPTHROWER.scr:130
    do return ctx:exit("") end -- PROPTHROWER.scr:132
end

script.labels["ResetPosition"] = function(ctx)
    -- PROPTHROWER.scr:136
    ctx:command("setpos", "g_hMyObject,homeX,homeY,homeZ") -- PROPTHROWER.scr:139
    do return ctx:exit("") end -- PROPTHROWER.scr:141
end

script.labels["OnLinkBroken"] = function(ctx)
    -- PROPTHROWER.scr:144
    ctx:getParam(0, "g_hObject") -- PROPTHROWER.scr:147
    if ctx:condition("g_hObject==hRequester") then -- PROPTHROWER.scr:148
        ctx:command("hrequester", "= NULL") -- PROPTHROWER.scr:149
    end -- PROPTHROWER.scr:150
    do return ctx:exit("") end -- PROPTHROWER.scr:152
end

script.labels["Main"] = function(ctx)
    -- PROPTHROWER.scr:155
    ctx:command("getmyhandle", "g_hMyObject") -- PROPTHROWER.scr:157
    ctx:command("clearflag", "g_hMyObject,FLAG_VISIBLE") -- PROPTHROWER.scr:158
    ctx:command("clearflag", "g_hMyObject,FLAG_SOLID") -- PROPTHROWER.scr:159
    ctx:command("getpos", "g_hMyObject,homeX,homeY,homeZ") -- PROPTHROWER.scr:161
    ctx:addTrigger("ThrowAtPlayer", "ThrowAtPlayer") -- PROPTHROWER.scr:163
    ctx:addTrigger("GetPlayer", "ThrowAtPlayer") -- PROPTHROWER.scr:164
    ctx:addTrigger("ResetPosition", "ResetPosition") -- PROPTHROWER.scr:165
    ctx:command("ontouchnotify", "OnTouchNotify") -- PROPTHROWER.scr:166
    ctx:command("onobjectlinkbroken", "OnLinkBroken") -- PROPTHROWER.scr:167
    do return ctx:exit("") end -- PROPTHROWER.scr:169
end

return script
