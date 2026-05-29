-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GREATERDEMON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "range.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "Flags.inc" }

-- GreaterDemon.scr
-- Jeff Leggett
-- p0 - pass a 1 if you want to spawn in from
-- the ground...
script.labels["AwareDone"] = function(ctx)
    -- GREATERDEMON.scr:14
    mm9.gosub(script, ctx, "Begin") -- GREATERDEMON.scr:16
    do return ctx:exit("") end -- GREATERDEMON.scr:18
end

script.labels["SpawnDone"] = function(ctx)
    -- GREATERDEMON.scr:21
    ctx:self():aware("AwareDone") -- GREATERDEMON.scr:23
    do return ctx:exit("") end -- GREATERDEMON.scr:25
end

script.labels["DoSpawnAnim"] = function(ctx)
    -- GREATERDEMON.scr:28
    ctx:state().g_hObject = ctx:player() -- GREATERDEMON.scr:31
    ctx:self():faceObject(ctx:player()) -- GREATERDEMON.scr:32
    ctx:self():playAnimation("Spawn", "SpawnDone") -- GREATERDEMON.scr:34
    ctx:self():setFlag("FLAG_VISIBLE", true) -- GREATERDEMON.scr:35
    do return ctx:exit("") end -- GREATERDEMON.scr:37
end

script.labels["SpawnIn"] = function(ctx)
    -- GREATERDEMON.scr:40
    -- Play our animation and do our special FX
    ctx:self():doClientFx("GreaterDemon") -- GREATERDEMON.scr:46
    ctx:wait(29, 1, "DoSpawnAnim") -- GREATERDEMON.scr:48
    do return ctx:exit("") end -- GREATERDEMON.scr:51
end

script.labels["Begin"] = function(ctx)
    -- GREATERDEMON.scr:55
    mm9.gosub(script, ctx, "BaseInit") -- GREATERDEMON.scr:58
    mm9.gosub(script, ctx, "RangeInit") -- GREATERDEMON.scr:59
    do return ctx:exit("") end -- GREATERDEMON.scr:60
end

script.labels["Main"] = function(ctx)
    -- GREATERDEMON.scr:63
    ctx:getParam(0, "g_bTemp") -- GREATERDEMON.scr:66
    if ctx:condition("g_bTemp==TRUE") then -- GREATERDEMON.scr:68
        ctx:self():setFlag("FLAG_VISIBLE", false) -- GREATERDEMON.scr:70
        ctx:wait(0, 0.1, "SpawnIn") -- GREATERDEMON.scr:71
    else -- GREATERDEMON.scr:72
        mm9.gosub(script, ctx, "Begin") -- GREATERDEMON.scr:73
    end -- GREATERDEMON.scr:74
    do return ctx:exit("") end -- GREATERDEMON.scr:77
end

return script
