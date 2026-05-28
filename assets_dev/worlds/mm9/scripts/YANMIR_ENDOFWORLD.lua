-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIR_ENDOFWORLD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Yanmir_EndOfWorld.Scr
-- Jeff Leggett
-- 01/07/2002
-- - Determines who this is (yanmir, different AI or the player)
-- and does the appropriate action.
script.labels["HandlePlayer"] = function(ctx)
    -- YANMIR_ENDOFWORLD.scr:12
    -- Decide what to do with player here...
    -- For now, goto the frosgardcity
    ctx:command("getobjecthandle", "PlayerExit,g_hObject") -- YANMIR_ENDOFWORLD.scr:20
    ctx:trigger("g_hObject", "On") -- YANMIR_ENDOFWORLD.scr:22
    ctx:trigger("g_hObject", "Trigger") -- YANMIR_ENDOFWORLD.scr:23
    do return ctx:exit("") end -- YANMIR_ENDOFWORLD.scr:25
end

script.labels["HandleYanmir"] = function(ctx)
    -- YANMIR_ENDOFWORLD.scr:28
    -- Just remove him for now...
    ctx:command("removeobject", "g_hObject") -- YANMIR_ENDOFWORLD.scr:33
    do return ctx:exit("") end -- YANMIR_ENDOFWORLD.scr:36
end

script.labels["HandleOther"] = function(ctx)
    -- YANMIR_ENDOFWORLD.scr:39
    ctx:command("isclass", "g_hObject,Actor,g_bTemp") -- YANMIR_ENDOFWORLD.scr:42
    if ctx:condition("g_bTemp==TRUE") then -- YANMIR_ENDOFWORLD.scr:44
        ctx:command("removeobject", "g_hObject") -- YANMIR_ENDOFWORLD.scr:45
    end -- YANMIR_ENDOFWORLD.scr:46
    do return ctx:exit("") end -- YANMIR_ENDOFWORLD.scr:48
end

script.labels["OnOutOfWorld"] = function(ctx)
    -- YANMIR_ENDOFWORLD.scr:51
    ctx:getParam(0, "g_hObject") -- YANMIR_ENDOFWORLD.scr:54
    ctx:command("isplayer", "g_hObject,g_bTemp") -- YANMIR_ENDOFWORLD.scr:56
    if ctx:condition("g_bTemp==TRUE") then -- YANMIR_ENDOFWORLD.scr:58
        do return mm9.gotoLabel(script, ctx, "HandlePlayer") end -- YANMIR_ENDOFWORLD.scr:59
    end -- YANMIR_ENDOFWORLD.scr:60
    ctx:command("getobjectname", "g_hObject,g_sTemp") -- YANMIR_ENDOFWORLD.scr:62
    if ctx:condition("g_sTemp==Yanmir0") then -- YANMIR_ENDOFWORLD.scr:64
        do return mm9.gotoLabel(script, ctx, "HandleYanmir") end -- YANMIR_ENDOFWORLD.scr:65
    end -- YANMIR_ENDOFWORLD.scr:66
    do return mm9.gotoLabel(script, ctx, "HandleOther") end -- YANMIR_ENDOFWORLD.scr:68
    do return ctx:exit("") end -- YANMIR_ENDOFWORLD.scr:70
end

script.labels["Main"] = function(ctx)
    -- YANMIR_ENDOFWORLD.scr:73
    ctx:addTrigger("OutOfWorld", "OnOutOfWorld") -- YANMIR_ENDOFWORLD.scr:76
    do return ctx:exit("") end -- YANMIR_ENDOFWORLD.scr:78
end

return script
