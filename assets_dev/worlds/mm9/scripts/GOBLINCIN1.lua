-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GOBLINCIN1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "base.inc" }

-- GoblinCin1.scr
-- John Machin
-- This script uses base.inc and extends it
-- so that we can make the goblin do what we
-- want when triggered with BeginScene
script.labels["OnBeginScene"] = function(ctx)
    -- GOBLINCIN1.scr:17
    -- Do Nothing for now.
    do return ctx:exit("") end -- GOBLINCIN1.scr:21
end

script.labels["OnSpeak"] = function(ctx)
    -- GOBLINCIN1.scr:24
    if ctx:condition("speaking = 1") then -- GOBLINCIN1.scr:26
        do return ctx:exit("") end -- GOBLINCIN1.scr:27
    end -- GOBLINCIN1.scr:28
    ctx:command("speak", "cinematic\\blood2.wav, OnSpeakDone") -- GOBLINCIN1.scr:30
    ctx:command("set", "speaking,1") -- GOBLINCIN1.scr:32
    do return ctx:exit("") end -- GOBLINCIN1.scr:34
end

script.labels["OnSpeakDone"] = function(ctx)
    -- GOBLINCIN1.scr:37
    -- Done talking now should exit
    ctx:trigger("hCamera0", "ZoomDone") -- GOBLINCIN1.scr:41
    mm9.gosub(script, ctx, "InitBase") -- GOBLINCIN1.scr:43
    do return ctx:exit("") end -- GOBLINCIN1.scr:45
end

script.labels["OnUse"] = function(ctx)
    -- GOBLINCIN1.scr:48
    ctx:getParam(0, "g_hObject") -- GOBLINCIN1.scr:51
    ctx:command("faceobject", "g_hObject, 180") -- GOBLINCIN1.scr:53
    do return ctx:exit("") end -- GOBLINCIN1.scr:55
end

script.labels["Main"] = function(ctx)
    -- GOBLINCIN1.scr:58
    -- This routine is automatically run
    -- at script startup...
    -- TraceOn
    ctx:command("getobjecthandle", "c0,hCamera0") -- GOBLINCIN1.scr:64
    mm9.gosub(script, ctx, "InitBase") -- GOBLINCIN1.scr:66
    ctx:addTrigger("Use", "OnUse") -- GOBLINCIN1.scr:68
    ctx:addTrigger("BeginScene", "OnBeginScene") -- GOBLINCIN1.scr:69
    ctx:addTrigger("Speak", "OnSpeak") -- GOBLINCIN1.scr:70
    do return ctx:exit("") end -- GOBLINCIN1.scr:72
end

return script
