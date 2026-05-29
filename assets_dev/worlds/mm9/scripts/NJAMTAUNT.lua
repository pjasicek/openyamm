-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NJAMTAUNT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- NjamTaunt.scr
-- By Timmy
-- Handle's Njam's Taunting Stuff for Taunt Cutscene
-- flag variables
script.labels["OnStart"] = function(ctx)
    -- NJAMTAUNT.scr:17
    ctx:state().g_hobject = ctx:objectOrNil("TauntMarker") -- NJAMTAUNT.scr:20
    ctx:self():walkTo(ctx:object("g_hobject"), 2, "OnArrive") -- NJAMTAUNT.scr:21
    do return ctx:exit("") end -- NJAMTAUNT.scr:22
end

script.labels["OnArrive"] = function(ctx)
    -- NJAMTAUNT.scr:25
    ctx:state().g_hobject = ctx:objectOrNil("TauntCamB") -- NJAMTAUNT.scr:28
    ctx:self():faceObject(ctx:object("g_hobject"), 10, "DoNothing") -- NJAMTAUNT.scr:29
    ctx:object("TauntMan"):trigger("Arrive") -- NJAMTAUNT.scr:31-32
    ctx:wait(1, 1, "OnText1") -- NJAMTAUNT.scr:33
    do return ctx:exit("") end -- NJAMTAUNT.scr:34
end

script.labels["OnText1"] = function(ctx)
    -- NJAMTAUNT.scr:38
    ctx:rolloverText(15, 0) -- NJAMTAUNT.scr:41
    ctx:wait(1, 4, "OnText2") -- NJAMTAUNT.scr:42
    do return ctx:exit("") end -- NJAMTAUNT.scr:45
end

script.labels["OnText2"] = function(ctx)
    -- NJAMTAUNT.scr:49
    ctx:rolloverText(16, 0) -- NJAMTAUNT.scr:52
    ctx:wait(1, 4, "OnVanish") -- NJAMTAUNT.scr:53
    do return ctx:exit("") end -- NJAMTAUNT.scr:54
end

script.labels["OnVanish"] = function(ctx)
    -- NJAMTAUNT.scr:58
    ctx:object("TauntMan"):trigger("VanishStart") -- NJAMTAUNT.scr:62-63
    -- play vanish effect here
    ctx:self():doClientFx("GreaterDemon") -- NJAMTAUNT.scr:68
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMTAUNT.scr:69
    ctx:wait(1, 1, "Vanish2b") -- NJAMTAUNT.scr:70
    do return ctx:exit("") end -- NJAMTAUNT.scr:71
end

script.labels["Vanish2b"] = function(ctx)
    -- NJAMTAUNT.scr:74
    ctx:self():setFlag("visible", false) -- NJAMTAUNT.scr:77
    ctx:playSound("\\Sounds\\magic\\teleport.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NJAMTAUNT.scr:78
    ctx:wait(1, 1, "Vanish2c") -- NJAMTAUNT.scr:79
    do return ctx:exit("") end -- NJAMTAUNT.scr:80
end

script.labels["Vanish2c"] = function(ctx)
    -- NJAMTAUNT.scr:84
    ctx:object("TauntMan"):trigger("VanishDone") -- NJAMTAUNT.scr:86-87
    ctx:self():remove() -- NJAMTAUNT.scr:89
    do return ctx:exit("") end -- NJAMTAUNT.scr:90
end

script.labels["Init"] = function(ctx)
    -- NJAMTAUNT.scr:94
    if ctx:hasKey(497) then -- NJAMTAUNT.scr:97-98
        ctx:self():remove() -- NJAMTAUNT.scr:100
    end -- NJAMTAUNT.scr:101
    do return ctx:exit("") end -- NJAMTAUNT.scr:103
end

script.labels["Main"] = function(ctx)
    -- NJAMTAUNT.scr:107
    -- TraceOn ;delete me!!
    ctx:addTrigger("Start", "OnStart") -- NJAMTAUNT.scr:111
    ctx:onEvent("OnPostStartWorld", "Init") -- NJAMTAUNT.scr:112
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NJAMTAUNT.scr:113
    ctx:onEvent("OnPostSaveLoad", "Init") -- NJAMTAUNT.scr:114
    ctx:wait(1, .1, "Init") -- NJAMTAUNT.scr:115
    do return ctx:exit("") end -- NJAMTAUNT.scr:116
end

return script
