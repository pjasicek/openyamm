-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTMISSION.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "botGlobals.inc" }

-- BotMission.Scr
-- Bot mission thinking....  Bot AI concerning fullfilling
-- mission objectives goes here...
-- What is the mission of this Map?
-- What are we currently doing?
-- Do we have the princess?
script.labels["BotMissPause"] = function(ctx)
    -- BOTMISSION.inc:35
    -- Pause our mission thinking (we're probably dealing with
    -- an enemy...)
    ctx:command("wait", "MISSION_WAIT, 0, DoNothing") -- BOTMISSION.inc:42
    do return ctx:exit("") end -- BOTMISSION.inc:44
end

script.labels["BotMissResume"] = function(ctx)
    -- BOTMISSION.inc:47
    -- Continue on with our mission objectives...
    ctx:command("wait", "MISSION_WAIT, 0.5, BotMissTick") -- BOTMISSION.inc:53
    do return ctx:exit("") end -- BOTMISSION.inc:55
end

script.labels["RescuePrincess"] = function(ctx)
    -- BOTMISSION.inc:58
    -- See if we currently have the princess.
    -- if not, go to the hostage site...
    ctx:command("getobjecthandle", "Princess0, g_hPrincess") -- BOTMISSION.inc:64
    ctx:command("getobjecthandle", "RescueZone0, g_hRescueZone") -- BOTMISSION.inc:65
    if ctx:condition("g_hPrincess==NULL") then -- BOTMISSION.inc:67
        ctx:command("debugout", "No princess to rescue!!") -- BOTMISSION.inc:68
        do return ctx:exit("") end -- BOTMISSION.inc:69
    end -- BOTMISSION.inc:70
    if ctx:condition("g_hRescueZone==NULL") then -- BOTMISSION.inc:72
        ctx:command("debugout", "No rescue zone for princess!!") -- BOTMISSION.inc:73
        do return ctx:exit("") end -- BOTMISSION.inc:74
    end -- BOTMISSION.inc:75
    ctx:command("set", "g_mission, GT_RESCUE_PRINCESS") -- BOTMISSION.inc:77
    mm9.gosub(script, ctx, "BotMissTick") -- BOTMISSION.inc:79
    do return ctx:exit("") end -- BOTMISSION.inc:81
end

script.labels["CancelTick"] = function(ctx)
    -- BOTMISSION.inc:84
    ctx:command("wait", "MISSION_WAIT, 0, DoNothing") -- BOTMISSION.inc:87
    do return ctx:exit("") end -- BOTMISSION.inc:89
end

script.labels["ReallyAtRescueZone2"] = function(ctx)
    -- BOTMISSION.inc:92
    ctx:command("stop", "") -- BOTMISSION.inc:94
    do return ctx:exit("") end -- BOTMISSION.inc:95
end

script.labels["ReallyAtRescueZone"] = function(ctx)
    -- BOTMISSION.inc:98
    -- We're really there, so time to stop...
    mm9.gosub(script, ctx, "CancelTick") -- BOTMISSION.inc:104
    ctx:command("stop", "") -- BOTMISSION.inc:105
    ctx:command("walk", "") -- BOTMISSION.inc:106
    ctx:command("wait", "MISSION_WAIT, 0.5, ReallyAtRescueZone2") -- BOTMISSION.inc:107
    do return ctx:exit("") end -- BOTMISSION.inc:109
end

script.labels["AtRescueZone"] = function(ctx)
    -- BOTMISSION.inc:112
    -- We are at the bounding box of the rescue zone...
    -- Now go in...
    ctx:command("getpos", "g_hMyObject, g_posX, g_posY, g_posZ") -- BOTMISSION.inc:119
    ctx:command("getpos", "g_hRescueZone, g_posX, g_nTemp, g_posZ") -- BOTMISSION.inc:120
    ctx:command("runtopos", "g_posX, g_posY, g_posZ, 12, ReallyAtRescueZone") -- BOTMISSION.inc:122
    do return ctx:exit("") end -- BOTMISSION.inc:125
end

script.labels["HavePrincessTick"] = function(ctx)
    -- BOTMISSION.inc:128
    -- Keep heading towards the Princess Rescue Zone
    ctx:command("runto", "g_hRescueZone, 0, AtRescueZone") -- BOTMISSION.inc:134
    do return ctx:exit("") end -- BOTMISSION.inc:136
end

script.labels["FoundPrincess"] = function(ctx)
    -- BOTMISSION.inc:139
    -- We've found her, now "use" her...
    ctx:command("set", "g_bHavePrincess, TRUE") -- BOTMISSION.inc:144
    ctx:trigger("g_hPrincess", "Use") -- BOTMISSION.inc:145
    do return ctx:exit("") end -- BOTMISSION.inc:147
end

script.labels["FindPrincessTick"] = function(ctx)
    -- BOTMISSION.inc:150
    -- Keep searching for princess.....
    ctx:command("runto", "g_hPrincess, 36, FoundPrincess") -- BOTMISSION.inc:156
    do return ctx:exit("") end -- BOTMISSION.inc:158
end

script.labels["BotMissTick"] = function(ctx)
    -- BOTMISSION.inc:161
    -- Do our thinking....
    if ctx:condition("g_bHavePrincess==TRUE") then -- BOTMISSION.inc:167
        mm9.gosub(script, ctx, "HavePrincessTick") -- BOTMISSION.inc:168
    else -- BOTMISSION.inc:169
        mm9.gosub(script, ctx, "FindPrincessTick") -- BOTMISSION.inc:170
    end -- BOTMISSION.inc:171
    ctx:command("wait", "MISSION_WAIT, 0.5, BotMissTick") -- BOTMISSION.inc:173
    do return ctx:exit("") end -- BOTMISSION.inc:175
end

script.labels["PrincessLost"] = function(ctx)
    -- BOTMISSION.inc:178
    -- The princess will trigger us if somebody else
    ctx:command("set", "g_bHavePrincess, FALSE") -- BOTMISSION.inc:183
    do return ctx:exit("") end -- BOTMISSION.inc:185
end

script.labels["Celebrate"] = function(ctx)
    -- BOTMISSION.inc:188
    -- We won!!
    if ctx:condition("g_nTemp==0") then -- BOTMISSION.inc:193
        ctx:command("set", "g_nTemp, 1") -- BOTMISSION.inc:194
    else -- BOTMISSION.inc:195
        ctx:command("set", "g_nTemp, 0") -- BOTMISSION.inc:196
    end -- BOTMISSION.inc:197
    ctx:command("setcrouch", "g_nTemp") -- BOTMISSION.inc:199
    ctx:command("wait", "8, 0.5, Celebrate") -- BOTMISSION.inc:201
    do return ctx:exit("") end -- BOTMISSION.inc:203
end

script.labels["PrincessRescued"] = function(ctx)
    -- BOTMISSION.inc:206
    -- We rescued the princess!!!  Yahoo!
    ctx:command("stop", "") -- BOTMISSION.inc:213
    ctx:command("wait", "MISSION_WAIT, 0, DoNothing") -- BOTMISSION.inc:214
    mm9.gosub(script, ctx, "Celebrate") -- BOTMISSION.inc:216
    do return ctx:exit("") end -- BOTMISSION.inc:218
end

script.labels["BotMissInit"] = function(ctx)
    -- BOTMISSION.inc:221
    -- Initialization stuff...
    ctx:addTrigger("RescuePrincess", "RescuePrincess") -- BOTMISSION.inc:227
    ctx:addTrigger("RP", "RescuePrincess") -- BOTMISSION.inc:228
    ctx:addTrigger("PrincessLost", "PrincessLost") -- BOTMISSION.inc:229
    ctx:addTrigger("PrincessRescued", "PrincessRescued") -- BOTMISSION.inc:230
    do return ctx:exit("") end -- BOTMISSION.inc:232
end

return script
