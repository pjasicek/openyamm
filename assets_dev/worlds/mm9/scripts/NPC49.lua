-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC49.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- NPC49.scr
-- By Timmy
-- handles It'lor's getting a job
script.labels["Onblabber"] = function(ctx)
    -- NPC49.scr:15
    -- erccs blabber
    ctx:command("playsound", "voices\\NPC\\NPC_049.wav, DoNothing, 100, 240, FALSE, 100") -- NPC49.scr:22
    do return ctx:exit("") end -- NPC49.scr:27
end

script.labels["Init"] = function(ctx)
    -- NPC49.scr:33
    if ctx:hasKey(157) then -- NPC49.scr:35-36
        ctx:command("getobjecthandle", "ItlorWork g_hobject") -- NPC49.scr:37
        ctx:command("getmyhandle", "g_hmyobject") -- NPC49.scr:38
        ctx:command("getpos", "g_hobject xPos yPos zPos") -- NPC49.scr:39
        ctx:command("setpos", "g_hmyobject xPos yPos zPos") -- NPC49.scr:40
        do return ctx:exit("") end -- NPC49.scr:41
    end -- NPC49.scr:42
    do return ctx:exit("") end -- NPC49.scr:44
end

script.labels["Main"] = function(ctx)
    -- NPC49.scr:47
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- NPC49.scr:51
    ctx:command("wait", "1 1 Init") -- NPC49.scr:52
    do return ctx:exit("") end -- NPC49.scr:53
end

return script
