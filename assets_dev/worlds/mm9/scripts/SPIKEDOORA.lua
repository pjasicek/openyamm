-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPIKEDOORA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- SpikeDoorA.scr
-- By Karl
-- When spike are removed the blocks can be
-- opened
script.labels["OnUse"] = function(ctx)
    -- SPIKEDOORA.scr:17
    ctx:command("getmyhandle", "hMyDoor") -- SPIKEDOORA.scr:19
    if ctx:condition("count == 6") then -- SPIKEDOORA.scr:20
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOORA.scr:21
        ctx:trigger("hMyDoor", "toggle") -- SPIKEDOORA.scr:22
    end -- SPIKEDOORA.scr:23
    do return ctx:exit("TRUE") end -- SPIKEDOORA.scr:24
end

script.labels["OnePulled"] = function(ctx)
    -- SPIKEDOORA.scr:26
    ctx:command("count", "= count + 1") -- SPIKEDOORA.scr:28
    if ctx:condition("count == 6") then -- SPIKEDOORA.scr:29
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOORA.scr:30
        ctx:trigger("hMyDoor", "use") -- SPIKEDOORA.scr:31
    end -- SPIKEDOORA.scr:32
    do return ctx:exit(1) end -- SPIKEDOORA.scr:33
end

script.labels["Main2"] = function(ctx)
    -- SPIKEDOORA.scr:35
    ctx:command("getobjecthandle", "sDoor, hMyDoor") -- SPIKEDOORA.scr:37
    ctx:addTrigger("OnePulled", "OnePulled") -- SPIKEDOORA.scr:38
    do return ctx:exit(1) end -- SPIKEDOORA.scr:39
end

script.labels["main"] = function(ctx)
    -- SPIKEDOORA.scr:41
    ctx:getParam(0, "sDoor") -- SPIKEDOORA.scr:43
    ctx:command("wait", "0, 0.4, Main2") -- SPIKEDOORA.scr:44
    do return ctx:exit("") end -- SPIKEDOORA.scr:45
end

return script
