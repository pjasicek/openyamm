-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LESSERDEMON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "range.inc" }

-- LesserDemon.scr
-- Jeff Leggett
-- p0 - pass a 1 if you want to spawn a
-- greater demon out when we die...
script.labels["OnDeathDone"] = function(ctx)
    -- LESSERDEMON.scr:18
    if ctx:condition("bSpawnGreaterDemon==TRUE") then -- LESSERDEMON.scr:21
        ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- LESSERDEMON.scr:22
        ctx:command("spawn", "g_hMyObject, g_posX, g_posY, g_posZ, sSpawnCmd") -- LESSERDEMON.scr:23
    end -- LESSERDEMON.scr:24
    do return ctx:exit("FALSE") end -- LESSERDEMON.scr:26
end

script.labels["CacheFiles"] = function(ctx)
    -- LESSERDEMON.scr:30
    ctx:command("cacheclientfx", "GreaterDemon") -- LESSERDEMON.scr:33
    do return ctx:exit("") end -- LESSERDEMON.scr:34
end

script.labels["Main"] = function(ctx)
    -- LESSERDEMON.scr:38
    ctx:getParam(0, "bSpawnGreaterDemon") -- LESSERDEMON.scr:41
    mm9.gosub(script, ctx, "BaseInit") -- LESSERDEMON.scr:43
    mm9.gosub(script, ctx, "RangeInit") -- LESSERDEMON.scr:44
    ctx:command("ondeathdone", "OnDeathDone") -- LESSERDEMON.scr:46
    if ctx:condition("bSpawnGreatherDemon==TRUE") then -- LESSERDEMON.scr:48
        ctx:command("oncachefiles", "CacheFiles") -- LESSERDEMON.scr:49
        mm9.gosub(script, ctx, "CacheFiles") -- LESSERDEMON.scr:50
    end -- LESSERDEMON.scr:51
    do return ctx:exit("") end -- LESSERDEMON.scr:53
end

return script
