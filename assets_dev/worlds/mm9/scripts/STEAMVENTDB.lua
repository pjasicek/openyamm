-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STEAMVENTDB.scr"
script.includes = {}
script.labels = {}


-- Steamventdb.scr
-- Brett Yagi
-- This script is controls the damage brush for a steam vent
-- Parameters
-- 0 - Marker that damagebrush will move to and from
script.labels["dn"] = function(ctx)
    -- STEAMVENTDB.scr:28
    do return ctx:exit(1) end -- STEAMVENTDB.scr:31
end

script.labels["turnoff"] = function(ctx)
    -- STEAMVENTDB.scr:34
    ctx:command("movetopos", "ax ay az 1000 dn") -- STEAMVENTDB.scr:37
    do return ctx:exit(1) end -- STEAMVENTDB.scr:39
end

script.labels["turnon"] = function(ctx)
    -- STEAMVENTDB.scr:42
    ctx:command("movetopos", "bx by bz 1000 dn") -- STEAMVENTDB.scr:45
    do return ctx:exit(1) end -- STEAMVENTDB.scr:47
end

script.labels["main2"] = function(ctx)
    -- STEAMVENTDB.scr:50
    ctx:command("getmyhandle", "myH") -- STEAMVENTDB.scr:53
    ctx:command("getobjecthandle", "sMarker ma") -- STEAMVENTDB.scr:54
    ctx:command("getpos", "ma ax ay az") -- STEAMVENTDB.scr:55
    ctx:command("getpos", "myH bx by bz") -- STEAMVENTDB.scr:56
    do return ctx:exit(1) end -- STEAMVENTDB.scr:58
end

script.labels["main"] = function(ctx)
    -- STEAMVENTDB.scr:62
    ctx:getParam(0, "sMarker") -- STEAMVENTDB.scr:65
    ctx:addTrigger("turnon", "turnon") -- STEAMVENTDB.scr:66
    ctx:addTrigger("turnoff", "turnoff") -- STEAMVENTDB.scr:67
    ctx:command("wait", "0 .1 main2") -- STEAMVENTDB.scr:68
    do return ctx:exit(1) end -- STEAMVENTDB.scr:70
end

return script
