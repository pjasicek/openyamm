-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARG_UNHIDE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- Arg_Unhide.scr
-- timmy
-- Hides or Unhides model based on player key
-- flag variables
-- parameters:
-- p0 The key to check for
-- p1 Hide or Unhide
script.labels["Init"] = function(ctx)
    -- ARG_UNHIDE.scr:26
    ctx:command("set", "g_ncounter, 0") -- ARG_UNHIDE.scr:29
    if ctx:hasKey(94) then -- ARG_UNHIDE.scr:31-32
        mm9.gosub(script, ctx, "hide") -- ARG_UNHIDE.scr:33
        do return ctx:exit("") end -- ARG_UNHIDE.scr:34
    end -- ARG_UNHIDE.scr:35
    if ctx:hasKey(90) then -- ARG_UNHIDE.scr:37-38
        ctx:command("add", "g_ncounter, 1") -- ARG_UNHIDE.scr:39
    end -- ARG_UNHIDE.scr:40
    if ctx:hasKey(91) then -- ARG_UNHIDE.scr:42-43
        ctx:command("add", "g_nCounter, 1") -- ARG_UNHIDE.scr:44
    end -- ARG_UNHIDE.scr:45
    if ctx:condition("g_nCounter==2") then -- ARG_UNHIDE.scr:47
        mm9.gosub(script, ctx, "Unhide") -- ARG_UNHIDE.scr:48
    end -- ARG_UNHIDE.scr:49
    do return ctx:exit("") end -- ARG_UNHIDE.scr:50
end

script.labels["Unhide"] = function(ctx)
    -- ARG_UNHIDE.scr:55
    ctx:command("getobjecthandle", "SvenProp g_hobject") -- ARG_UNHIDE.scr:58
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:59
    ctx:command("getobjecthandle", "TryygvaProp g_hobject") -- ARG_UNHIDE.scr:61
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:62
    ctx:command("getobjecthandle", "MarkeProp g_hobject") -- ARG_UNHIDE.scr:64
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:65
    ctx:command("getobjecthandle", "BookProp g_hobject") -- ARG_UNHIDE.scr:67
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:68
    ctx:command("getobjecthandle", "ForadProp g_hobject") -- ARG_UNHIDE.scr:70
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:71
    ctx:command("getobjecthandle", "SigmundProp g_hobject") -- ARG_UNHIDE.scr:73
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:74
    ctx:command("getobjecthandle", "TreatyProp g_hobject") -- ARG_UNHIDE.scr:76
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:77
    ctx:command("getobjecthandle", "BjarniProp g_hobject") -- ARG_UNHIDE.scr:79
    ctx:command("setflag", "g_hobject, visible") -- ARG_UNHIDE.scr:80
    do return ctx:exit("") end -- ARG_UNHIDE.scr:82
end

script.labels["Hide"] = function(ctx)
    -- ARG_UNHIDE.scr:87
    ctx:command("getobjecthandle", "SvenProp g_hobject") -- ARG_UNHIDE.scr:90
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:91
    ctx:command("getobjecthandle", "TryygvaProp g_hobject") -- ARG_UNHIDE.scr:93
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:94
    ctx:command("getobjecthandle", "MarkeProp g_hobject") -- ARG_UNHIDE.scr:96
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:97
    ctx:command("getobjecthandle", "BookProp g_hobject") -- ARG_UNHIDE.scr:99
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:100
    ctx:command("getobjecthandle", "ForadProp g_hobject") -- ARG_UNHIDE.scr:102
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:103
    ctx:command("getobjecthandle", "SigmundProp g_hobject") -- ARG_UNHIDE.scr:105
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:106
    ctx:command("getobjecthandle", "TreatyProp g_hobject") -- ARG_UNHIDE.scr:108
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:109
    ctx:command("getobjecthandle", "BjarniProp g_hobject") -- ARG_UNHIDE.scr:111
    ctx:command("clearflag", "g_hobject, visible") -- ARG_UNHIDE.scr:112
    do return ctx:exit("") end -- ARG_UNHIDE.scr:114
end

script.labels["Main"] = function(ctx)
    -- ARG_UNHIDE.scr:117
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("onpoststartworld", "Init") -- ARG_UNHIDE.scr:123
    ctx:command("onpostminisaveload", "Init") -- ARG_UNHIDE.scr:124
    ctx:command("onpostsaveload", "Init") -- ARG_UNHIDE.scr:125
    ctx:command("wait", "1 1 Init") -- ARG_UNHIDE.scr:126
    do return ctx:exit("") end -- ARG_UNHIDE.scr:127
end

return script
