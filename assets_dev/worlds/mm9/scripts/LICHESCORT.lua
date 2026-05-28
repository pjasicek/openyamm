-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHESCORT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }

script.labels["Main"] = function(ctx)
    -- LICHESCORT.scr:13
    ctx:getParam(0, "sDestinationName") -- LICHESCORT.scr:15
    ctx:command("getmyhandle", "hMe") -- LICHESCORT.scr:17
    ctx:addTrigger("walk", "WalkToEngine") -- LICHESCORT.scr:19
    ctx:addTrigger("play", "PlayAnim") -- LICHESCORT.scr:20
    do return ctx:exit("TRUE") end -- LICHESCORT.scr:22
end

script.labels["WalkToEngine"] = function(ctx)
    -- LICHESCORT.scr:25
    ctx:command("getobjecthandle", "sDestinationName, hDestination") -- LICHESCORT.scr:27
    if ctx:condition("hDestination!=0") then -- LICHESCORT.scr:28
        ctx:command("walkto", "hDestination, 10, StopMoving") -- LICHESCORT.scr:29
        ctx:command("wait", "0, 10, EndScene") -- LICHESCORT.scr:30
    end -- LICHESCORT.scr:31
    do return ctx:exit("TRUE") end -- LICHESCORT.scr:33
end

script.labels["PlayAnim"] = function(ctx)
    -- LICHESCORT.scr:36
    ctx:command("doclientfx", "hMe, SPELL_TRANSFUSION, FALSE, TRUE") -- LICHESCORT.scr:38
    ctx:command("playanim", "resurrectspell, EndScene") -- LICHESCORT.scr:40
    do return ctx:exit("TRUE") end -- LICHESCORT.scr:42
end

return script
