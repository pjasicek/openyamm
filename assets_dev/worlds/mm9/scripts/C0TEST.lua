-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "C0TEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "followpath.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "globals.inc" }

script.labels["OnZoom"] = function(ctx)
    -- C0TEST.scr:8
    ctx:setCallback(0, "OnZoomWait") -- C0TEST.scr:11
    ctx:trigger("g_hMyObject", "ON") -- C0TEST.scr:13
    ctx:set("g_sFollowPathName", "Marker") -- C0TEST.scr:15
    ctx:state().g_nFollowPathSpeed = 96 -- C0TEST.scr:16
    ctx:state().g_nFollowPathDoneCallback = 0 -- C0TEST.scr:17
    ctx:state().g_nFollowPathLoops = 1 -- C0TEST.scr:18
    mm9.gosub(script, ctx, "FollowPath") -- C0TEST.scr:19
    ctx:addTrigger("Zoom", "DoNothing") -- C0TEST.scr:21
    do return ctx:exit("") end -- C0TEST.scr:23
end

script.labels["OnZoomDone"] = function(ctx)
    -- C0TEST.scr:27
    ctx:trigger("g_hMyObject", "OFF") -- C0TEST.scr:29
    do return ctx:exit("") end -- C0TEST.scr:31
end

script.labels["DoNothing"] = function(ctx)
    -- C0TEST.scr:35
    do return ctx:exit("") end -- C0TEST.scr:37
end

script.labels["OnZoomWait"] = function(ctx)
    -- C0TEST.scr:41
    -- Wait 10,OnZoomDone
    ctx:state().hGoblin0 = ctx:objectOrNil("Goblin0") -- C0TEST.scr:44
    ctx:trigger("hGoblin0", "Speak") -- C0TEST.scr:46
    do return ctx:exit("") end -- C0TEST.scr:48
end

script.labels["Main"] = function(ctx)
    -- C0TEST.scr:51
    -- This routine is automatically run
    -- at script startup...
    -- TraceOn
    ctx:addTrigger("Zoom", "OnZoom") -- C0TEST.scr:60
    ctx:addTrigger("ZoomDone", "OnZoomDone") -- C0TEST.scr:61
    do return ctx:exit("") end -- C0TEST.scr:63
end

return script
