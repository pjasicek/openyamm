-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRAGONAZURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "base.inc" }

script.labels["DragonAzure.scr"] = function(ctx)
    -- DRAGONAZURE.scr:2
end

-- Specifically handles the Azure dragon
script.labels["GetWaterDims"] = function(ctx)
    -- DRAGONAZURE.scr:31
    ctx:command("getliquidcontainer", "g_hMyObject, hWater") -- DRAGONAZURE.scr:33
    if ctx:condition("hWater!=NULL") then -- DRAGONAZURE.scr:35
        ctx:command("getobjectminmax", "hWater, minWaterX, minWaterY, minWaterZ, maxWaterX, maxWaterY, maxWaterZ") -- DRAGONAZURE.scr:36
    end -- DRAGONAZURE.scr:37
    do return ctx:exit("") end -- DRAGONAZURE.scr:39
end

script.labels["JumpDone"] = function(ctx)
    -- DRAGONAZURE.scr:42
    mm9.gosub(script, ctx, "BaseGoGetHim") -- DRAGONAZURE.scr:44
    do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:45
end

script.labels["JumpAtTarget"] = function(ctx)
    -- DRAGONAZURE.scr:48
    ctx:command("jump", "JumpDone") -- DRAGONAZURE.scr:51
    do return ctx:exit("") end -- DRAGONAZURE.scr:53
end

script.labels["CheckForJump"] = function(ctx)
    -- DRAGONAZURE.scr:56
    -- See if we should attempt to jump out of the water
    -- get obstacle handle
    ctx:getParam(0, "g_hObject") -- DRAGONAZURE.scr:62
    -- See if obstacle handle is world geometry
    if ctx:condition("g_hObject==NULL") then -- DRAGONAZURE.scr:65
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:66
    end -- DRAGONAZURE.scr:67
    ctx:command("getclassname", "g_hObject, g_sTemp") -- DRAGONAZURE.scr:69
    if ctx:condition("g_sTemp!=World") then -- DRAGONAZURE.scr:71
        -- only jump over world obstacles
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:73
    end -- DRAGONAZURE.scr:74
    mm9.gosub(script, ctx, "GetWaterDims") -- DRAGONAZURE.scr:76
    if ctx:condition("hWater==NULL") then -- DRAGONAZURE.scr:78
        -- we're not in water, so don't jump....
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:80
    end -- DRAGONAZURE.scr:81
    -- Okay, we're in water....
    if ctx:condition("g_hTarget==NULL") then -- DRAGONAZURE.scr:85
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:86
    end -- DRAGONAZURE.scr:87
    ctx:command("getpos", "g_hTarget, g_posX, g_posY, g_posZ") -- DRAGONAZURE.scr:89
    ctx:getParam(1, "normalX") -- DRAGONAZURE.scr:91
    ctx:getParam(2, "normalY") -- DRAGONAZURE.scr:92
    ctx:getParam(3, "normalZ") -- DRAGONAZURE.scr:93
    ctx:command("mul", "normalX, -1") -- DRAGONAZURE.scr:95
    ctx:command("mul", "normalY, -1") -- DRAGONAZURE.scr:96
    ctx:command("mul", "normalZ, -1") -- DRAGONAZURE.scr:97
    if ctx:condition("g_posY <= maxWaterY") then -- DRAGONAZURE.scr:99
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:100
    end -- DRAGONAZURE.scr:101
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- DRAGONAZURE.scr:103
    ctx:command("getdims", "g_hMyObject, dimsX, dimsY, dimsZ") -- DRAGONAZURE.scr:104
    ctx:command("add", "g_posY, dimsY") -- DRAGONAZURE.scr:106
    ctx:command("add", "g_posY, dimsY") -- DRAGONAZURE.scr:107
    ctx:command("add", "g_posY, dimsY") -- DRAGONAZURE.scr:108
    ctx:command("set", "g_nTemp, dimsZ") -- DRAGONAZURE.scr:110
    ctx:command("mul", "g_nTemp, 3") -- DRAGONAZURE.scr:112
    -- Now see if there's a wall in the way...
    ctx:command("checkworldcollision", "g_posX, g_posY, g_posZ, normalX, normalY, normalZ, g_nTemp, g_hObject") -- DRAGONAZURE.scr:115
    if ctx:condition("g_hObject!=NULL") then -- DRAGONAZURE.scr:117
        -- There's a wall in our way...
        do return ctx:exit("FALSE") end -- DRAGONAZURE.scr:119
        ctx:command("debugout", "Can't Jump... There's a wall in the way!") -- DRAGONAZURE.scr:120
    end -- DRAGONAZURE.scr:121
    -- if we're here, it's time to do the jump!
    ctx:command("facedir", "normalX, normalY, normalZ, 180") -- DRAGONAZURE.scr:125
    mm9.gosub(script, ctx, "JumpAtTarget") -- DRAGONAZURE.scr:126
    do return ctx:exit("TRUE") end -- DRAGONAZURE.scr:128
end

script.labels["DamageDone"] = function(ctx)
    -- DRAGONAZURE.scr:131
    -- Don't ever go after one of our own...
    mm9.gosub(script, ctx, "BaseDamageDone") -- DRAGONAZURE.scr:137
    do return ctx:exit("") end -- DRAGONAZURE.scr:139
end

script.labels["Main"] = function(ctx)
    -- DRAGONAZURE.scr:142
    mm9.gosub(script, ctx, "InitBase") -- DRAGONAZURE.scr:145
    -- OnStuck CheckForJump
    ctx:command("onobstacle", "CheckForJump") -- DRAGONAZURE.scr:148
    ctx:command("ondamagedone", "DamageDone") -- DRAGONAZURE.scr:149
    do return ctx:exit("") end -- DRAGONAZURE.scr:151
end

return script
