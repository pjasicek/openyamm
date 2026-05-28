-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHSORCERER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }

script.labels["Main"] = function(ctx)
    -- LICHSORCERER.scr:22
    ctx:getParam(0, "sDestinationName") -- LICHSORCERER.scr:24
    ctx:getParam(1, "sDoorName") -- LICHSORCERER.scr:25
    ctx:command("getmyhandle", "hMe") -- LICHSORCERER.scr:27
    ctx:addTrigger("walk", "WalkToChamber") -- LICHSORCERER.scr:29
    ctx:addTrigger("transform", "StartTransform") -- LICHSORCERER.scr:30
    ctx:addTrigger("finish", "FinishTransform") -- LICHSORCERER.scr:31
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:33
end

script.labels["WalkToChamber"] = function(ctx)
    -- LICHSORCERER.scr:36
    ctx:command("getobjecthandle", "sDestinationName, hDestination") -- LICHSORCERER.scr:38
    if ctx:condition("hDestination!=0") then -- LICHSORCERER.scr:39
        ctx:command("walkto", "hDestination, 0, OnReachedDestination") -- LICHSORCERER.scr:40
    end -- LICHSORCERER.scr:41
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:43
end

script.labels["OnReachedDestination"] = function(ctx)
    -- LICHSORCERER.scr:46
    ctx:command("stop", "") -- LICHSORCERER.scr:48
    ctx:command("getobjecthandle", "sDoorName, hDoor") -- LICHSORCERER.scr:49
    if ctx:condition("hDoor!=0") then -- LICHSORCERER.scr:50
        ctx:command("rotate", "0,1,0, 180, 180, DoNothing") -- LICHSORCERER.scr:51
        ctx:trigger("hDoor", "open") -- LICHSORCERER.scr:52
        ctx:command("getstat", "hDoor, DoorOpenTime, nTemp") -- LICHSORCERER.scr:53
        ctx:command("ntemp", "= nTemp + 3") -- LICHSORCERER.scr:54
        ctx:command("wait", "0, nTemp, EndScene") -- LICHSORCERER.scr:55
    end -- LICHSORCERER.scr:56
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:58
end

script.labels["StartTransform"] = function(ctx)
    -- LICHSORCERER.scr:61
    ctx:command("doclientfx", "hMe, SPELL_SPARKLIES, FALSE, TRUE") -- LICHSORCERER.scr:63
    ctx:command("playanim", "taunt, ChangeToLich") -- LICHSORCERER.scr:65
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:67
end

script.labels["ChangeToLich"] = function(ctx)
    -- LICHSORCERER.scr:70
    ctx:command("playanim", "die2, EndScene") -- LICHSORCERER.scr:72
    ctx:command("doclientfx", "hMe, SPELL_BLACKSMOKE, TRUE, TRUE") -- LICHSORCERER.scr:74
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:76
end

script.labels["FinishTransform"] = function(ctx)
    -- LICHSORCERER.scr:79
    ctx:command("getpos", "hMe, xMe,yMe,zMe") -- LICHSORCERER.scr:81
    ctx:command("getobjecthandle", "LichSorcererNew, hDummy") -- LICHSORCERER.scr:82
    ctx:command("setpos", "hDummy, xMe,yMe,zMe") -- LICHSORCERER.scr:83
    ctx:command("wait", "0, 1, RemoveMe") -- LICHSORCERER.scr:84
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:86
end

script.labels["RemoveMe"] = function(ctx)
    -- LICHSORCERER.scr:89
    ctx:command("removeobject", "hMe") -- LICHSORCERER.scr:91
    do return ctx:exit("TRUE") end -- LICHSORCERER.scr:93
end

return script
