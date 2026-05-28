-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHSACRIFICE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }

script.labels["Main"] = function(ctx)
    -- LICHSACRIFICE.scr:15
    ctx:getParam(0, "sDestinationName") -- LICHSACRIFICE.scr:17
    ctx:command("getmyhandle", "hMe") -- LICHSACRIFICE.scr:19
    ctx:addTrigger("walk", "WalkToEngine") -- LICHSACRIFICE.scr:21
    ctx:addTrigger("port", "PortToLocation") -- LICHSACRIFICE.scr:22
    ctx:addTrigger("burn", "PlayEffects") -- LICHSACRIFICE.scr:23
    do return ctx:exit("TRUE") end -- LICHSACRIFICE.scr:25
end

script.labels["WalkToEngine"] = function(ctx)
    -- LICHSACRIFICE.scr:28
    ctx:command("getobjecthandle", "sDestinationName, hDestination") -- LICHSACRIFICE.scr:30
    if ctx:condition("hDestination!=0") then -- LICHSACRIFICE.scr:31
        ctx:command("walkto", "hDestination, 1, StopMoving") -- LICHSACRIFICE.scr:32
    end -- LICHSACRIFICE.scr:33
    do return ctx:exit("TRUE") end -- LICHSACRIFICE.scr:35
end

script.labels["PortToLocation"] = function(ctx)
    -- LICHSACRIFICE.scr:38
    ctx:command("getobjecthandle", "sDestinationName, hDestination") -- LICHSACRIFICE.scr:40
    ctx:command("getpos", "hDestination, x,y,z") -- LICHSACRIFICE.scr:41
    ctx:command("setpos", "hMe, x,y,z") -- LICHSACRIFICE.scr:42
    do return ctx:exit("TRUE") end -- LICHSACRIFICE.scr:44
end

script.labels["PlayEffects"] = function(ctx)
    -- LICHSACRIFICE.scr:47
    ctx:command("loopanim", "girl1, 0") -- LICHSACRIFICE.scr:49
    ctx:command("doclientfx", "hMe, SPELL_BLUEFIRE, TRUE, TRUE") -- LICHSACRIFICE.scr:51
    do return ctx:exit("TRUE") end -- LICHSACRIFICE.scr:53
end

return script
