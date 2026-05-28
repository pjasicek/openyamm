-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YF_EXPLODINGFLOOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "Flags.inc" }

-- YF_FallingFloor.scr
-- kd 11-2-01
-- Parameters
-- CaveIn Trap: Move large floor chunks to marker below.
script.labels["dn"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:19
    do return ctx:exit(1) end -- YF_EXPLODINGFLOOR.scr:21
end

script.labels["StopHere"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:23
    -- playsound Sounds\Door\doorslammetal01.wav DoNothing hDummy 400 FALSE 100
    do return ctx:exit("TRUE") end -- YF_EXPLODINGFLOOR.scr:26
end

script.labels["MoveToMarker"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:28
    -- playsound Sounds\Events\??? DoNothing 50 400 TRUE 100
    ctx:command("cprint", "\"MoveToMarker\"") -- YF_EXPLODINGFLOOR.scr:31
    ctx:trigger("hMe", "Destroy") -- YF_EXPLODINGFLOOR.scr:32
    do return ctx:exit("TRUE") end -- YF_EXPLODINGFLOOR.scr:33
end

script.labels["DelayAction"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:35
    ctx:command("setflag", "hMe,FLAG_GOTHRUWORLD") -- YF_EXPLODINGFLOOR.scr:37
    ctx:command("clearflag", "hMe,FLAG_SOLID") -- YF_EXPLODINGFLOOR.scr:38
    ctx:command("cprint", "\"DelayAction\"") -- YF_EXPLODINGFLOOR.scr:40
    ctx:command("wait", "0, 1.5, MoveToMarker") -- YF_EXPLODINGFLOOR.scr:41
    do return ctx:exit("TRUE") end -- YF_EXPLODINGFLOOR.scr:42
end

script.labels["Main2"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:44
    ctx:command("getmyhandle", "hMe") -- YF_EXPLODINGFLOOR.scr:46
    -- GetObjectHandle YanDstruct0, hDestroy
    ctx:addTrigger("Fall", "DelayAction") -- YF_EXPLODINGFLOOR.scr:48
    do return ctx:exit("TRUE") end -- YF_EXPLODINGFLOOR.scr:49
end

script.labels["Main"] = function(ctx)
    -- YF_EXPLODINGFLOOR.scr:51
    ctx:command("wait", "0 .1 main2") -- YF_EXPLODINGFLOOR.scr:53
    do return ctx:exit("TRUE") end -- YF_EXPLODINGFLOOR.scr:54
end

return script
