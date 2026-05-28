-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMDOORMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseMelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "DrangheimHostility.inc" }

-- DrangheimDoorman.scr
-- SJR
-- Feltup by kd 10-21-01
-- Guard that Unlocks/opens and closes/Locks
-- the InterrogationRoom Doors
script.labels["Main"] = function(ctx)
    -- DRANGHEIMDOORMAN.scr:17
    ctx:getParam(0, "sDoorName") -- DRANGHEIMDOORMAN.scr:19
    ctx:command("onpoststartworld", "InitDoorman") -- DRANGHEIMDOORMAN.scr:21
    ctx:command("onpostminisaveload", "InitDoorman") -- DRANGHEIMDOORMAN.scr:22
    do return ctx:exit("TRUE") end -- DRANGHEIMDOORMAN.scr:24
end

script.labels["InitDoorman"] = function(ctx)
    -- DRANGHEIMDOORMAN.scr:27
    mm9.gosub(script, ctx, "InitDrangheimHostility") -- DRANGHEIMDOORMAN.scr:29
    ctx:addTrigger("open", "OpenRoom") -- DRANGHEIMDOORMAN.scr:31
    ctx:addTrigger("close", "CloseRoom") -- DRANGHEIMDOORMAN.scr:32
    ctx:command("getobjecthandle", "sDoorName, hDoor") -- DRANGHEIMDOORMAN.scr:34
    mm9.gosub(script, ctx, "CloseRoom") -- DRANGHEIMDOORMAN.scr:36
    do return ctx:exit("TRUE") end -- DRANGHEIMDOORMAN.scr:38
end

script.labels["OpenRoom"] = function(ctx)
    -- DRANGHEIMDOORMAN.scr:41
    if ctx:condition("hDoor!=0") then -- DRANGHEIMDOORMAN.scr:43
        ctx:trigger("hDoor", "unlock") -- DRANGHEIMDOORMAN.scr:44
        ctx:trigger("hDoor", "use") -- DRANGHEIMDOORMAN.scr:45
    end -- DRANGHEIMDOORMAN.scr:46
    do return ctx:exit("TRUE") end -- DRANGHEIMDOORMAN.scr:48
end

script.labels["CloseRoom"] = function(ctx)
    -- DRANGHEIMDOORMAN.scr:51
    if ctx:condition("hDoor!=0") then -- DRANGHEIMDOORMAN.scr:53
        ctx:trigger("hDoor", "close") -- DRANGHEIMDOORMAN.scr:54
        ctx:trigger("hDoor", "lock") -- DRANGHEIMDOORMAN.scr:55
    end -- DRANGHEIMDOORMAN.scr:56
    do return ctx:exit("TRUE") end -- DRANGHEIMDOORMAN.scr:58
end

return script
