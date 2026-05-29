-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AUTORESURRECT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "flags.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "AICommon.inc" }

-- AutoResurrect.scr
-- Jeff Leggett
-- 12/12/2001
-- Used for AI that start out under the ground
-- When we receive the Resurrect trigger, we
-- play our resurrect animation and then Run our normal
-- script...
script.labels["ResurrectDone"] = function(ctx)
    -- AUTORESURRECT.scr:25
    mm9.gosub(script, ctx, "ResurrectDone") -- AUTORESURRECT.scr:27
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- AUTORESURRECT.scr:28
    ctx:runScript("g_sTemp") -- AUTORESURRECT.scr:29
    do return ctx:exit("") end -- AUTORESURRECT.scr:30
end

script.labels["OnResurrect"] = function(ctx)
    -- AUTORESURRECT.scr:34
    mm9.gosub(script, ctx, "OnResurrect") -- AUTORESURRECT.scr:36
    if ctx:condition("g_bCanResurrectNow==FALSE") then -- AUTORESURRECT.scr:38
        do return ctx:exit("") end -- AUTORESURRECT.scr:39
    end -- AUTORESURRECT.scr:40
    ctx:self():setFlag("FLAG_SOLID", true) -- AUTORESURRECT.scr:42
    ctx:self():setFlag("FLAG_GRAVITY", true) -- AUTORESURRECT.scr:43
    ctx:self():setFlag("FLAG_VISIBLE", true) -- AUTORESURRECT.scr:44
    do return ctx:exit("") end -- AUTORESURRECT.scr:46
end

script.labels["Init"] = function(ctx)
    -- AUTORESURRECT.scr:49
    -- Just loop a custom anim so that we don't do anything
    -- else...
    ctx:self():loopAnimation(0, 0) -- AUTORESURRECT.scr:54
    do return ctx:exit("") end -- AUTORESURRECT.scr:55
end

script.labels["CacheFiles"] = function(ctx)
    -- AUTORESURRECT.scr:58
    ctx:state().g_sTemp = ctx:self():stringProperty("ScriptName") -- AUTORESURRECT.scr:60
    ctx:cacheScript("g_sTemp") -- AUTORESURRECT.scr:61
    do return ctx:exit("") end -- AUTORESURRECT.scr:63
end

script.labels["Main"] = function(ctx)
    -- AUTORESURRECT.scr:66
    -- #number x
    -- #number y
    -- #number z
    -- GetPos g_hMyObject, x,y,z
    -- g_sTemp = x + _ + y + _ + z
    -- cprint g_sTemp
    ctx:self():setFlag("FLAG_SOLID", false) -- AUTORESURRECT.scr:77
    ctx:self():setFlag("FLAG_GRAVITY", false) -- AUTORESURRECT.scr:78
    ctx:self():setFlag("FLAG_VISIBLE", false) -- AUTORESURRECT.scr:79
    ctx:wait(0, 0.01, "Init") -- AUTORESURRECT.scr:81
    ctx:addTrigger("TMSG_RESURRECT", "OnResurrect") -- AUTORESURRECT.scr:83
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- AUTORESURRECT.scr:84
    do return ctx:exit("") end -- AUTORESURRECT.scr:87
end

return script
