-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHINSTRUCTIONS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- LichInstructions.scr
-- By Timmy
-- gives the player the Lich Instructions.
-- and the related key
-- Lich Instructions is item 245 and 447
-- Lich Item keys are 296, 371
script.labels["OnUse"] = function(ctx)
    -- LICHINSTRUCTIONS.scr:16
    if not ctx:hasKey(296) then -- LICHINSTRUCTIONS.scr:19-20
        ctx:giveKey(296) -- LICHINSTRUCTIONS.scr:21
        ctx:giveItem(447) -- LICHINSTRUCTIONS.scr:22
        ctx:command("getmyhandle", "g_hmyobject") -- LICHINSTRUCTIONS.scr:23
        ctx:command("removeobject", "g_hmyobject") -- LICHINSTRUCTIONS.scr:24
        do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:25
    end -- LICHINSTRUCTIONS.scr:26
    do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:27
end

script.labels["Init"] = function(ctx)
    -- LICHINSTRUCTIONS.scr:29
    if ctx:hasKey(296) then -- LICHINSTRUCTIONS.scr:32-33
        ctx:command("getmyhandle", "g_hmyobject") -- LICHINSTRUCTIONS.scr:34
        ctx:command("removeobject", "g_hmyobject") -- LICHINSTRUCTIONS.scr:35
        do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:36
    end -- LICHINSTRUCTIONS.scr:37
    do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:38
    do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:40
end

script.labels["Main"] = function(ctx)
    -- LICHINSTRUCTIONS.scr:42
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- LICHINSTRUCTIONS.scr:46
    ctx:command("wait", "1 .1 Init") -- LICHINSTRUCTIONS.scr:47
    ctx:command("onpoststartworld", "Init") -- LICHINSTRUCTIONS.scr:48
    ctx:command("onpostminisaveload", "Init") -- LICHINSTRUCTIONS.scr:49
    ctx:command("onpostsaveload", "Init") -- LICHINSTRUCTIONS.scr:50
    do return ctx:exit("") end -- LICHINSTRUCTIONS.scr:51
end

return script
