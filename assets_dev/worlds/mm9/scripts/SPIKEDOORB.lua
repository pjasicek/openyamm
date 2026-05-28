-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPIKEDOORB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- SpikeDoorB.scr
-- By Karl
-- When spike are removed the blocks can be
-- opened
script.labels["OnUse"] = function(ctx)
    -- SPIKEDOORB.scr:17
    ctx:command("getmyhandle", "hMyDoor") -- SPIKEDOORB.scr:19
    if ctx:condition("count == 6") then -- SPIKEDOORB.scr:20
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOORB.scr:21
        ctx:trigger("hMyDoor", "toggle") -- SPIKEDOORB.scr:22
    end -- SPIKEDOORB.scr:23
    do return ctx:exit("TRUE") end -- SPIKEDOORB.scr:24
end

script.labels["OnePulled"] = function(ctx)
    -- SPIKEDOORB.scr:26
    ctx:command("count", "= count + 1") -- SPIKEDOORB.scr:28
    if ctx:condition("count == 6") then -- SPIKEDOORB.scr:29
        ctx:trigger("hMyDoor", "unlock") -- SPIKEDOORB.scr:30
        ctx:trigger("hMyDoor", "use") -- SPIKEDOORB.scr:31
    end -- SPIKEDOORB.scr:32
    do return ctx:exit(1) end -- SPIKEDOORB.scr:33
end

script.labels["Main2"] = function(ctx)
    -- SPIKEDOORB.scr:35
    ctx:command("getobjecthandle", "sDoor, hMyDoor") -- SPIKEDOORB.scr:37
    ctx:addTrigger("OnePulled", "OnePulled") -- SPIKEDOORB.scr:38
    do return ctx:exit(1) end -- SPIKEDOORB.scr:39
end

script.labels["main"] = function(ctx)
    -- SPIKEDOORB.scr:41
    ctx:getParam(0, "sDoor") -- SPIKEDOORB.scr:43
    ctx:command("wait", "0, 0.4, Main2") -- SPIKEDOORB.scr:44
    do return ctx:exit("") end -- SPIKEDOORB.scr:45
end

return script
