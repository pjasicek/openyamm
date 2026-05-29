-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATTLEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- BattleMan.scr
-- timmy
-- handles the Battle of Frosgard stuff
script.labels["Spawn"] = function(ctx)
    -- BATTLEMAN.scr:33
    ctx:giveKey(377) -- BATTLEMAN.scr:36
    ctx:object("ForadDarre"):trigger("Appear") -- BATTLEMAN.scr:38-39
    ctx:object("TamurLeng0"):trigger("Appear") -- BATTLEMAN.scr:41-42
    ctx:state().SCRIPT = " ScriptName HateNPC.scr" -- BATTLEMAN.scr:44
    -- screenfadeout 1
    ctx:wait(1, 1, "FadeIn") -- BATTLEMAN.scr:46
    ctx:set("sMonsterA", "sMonsterA + Script") -- BATTLEMAN.scr:48
    ctx:set("sMonsterB", "sMonsterB + Script") -- BATTLEMAN.scr:49
    ctx:set("sMonsterC", "sMonsterC + Script") -- BATTLEMAN.scr:50
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("Atlimarker"):pos() -- BATTLEMAN.scr:53-54
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:55
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:56
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- BATTLEMAN.scr:57
    ctx:state().hMonsterC = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- BATTLEMAN.scr:58
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys0"):pos() -- BATTLEMAN.scr:60-61
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:62
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:63
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- BATTLEMAN.scr:64
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys2"):pos() -- BATTLEMAN.scr:66-67
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:68
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:69
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- BATTLEMAN.scr:70
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys3"):pos() -- BATTLEMAN.scr:72-73
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- BATTLEMAN.scr:74
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- BATTLEMAN.scr:75
    do return ctx:exit("") end -- BATTLEMAN.scr:77
end

script.labels["FadeIn"] = function(ctx)
    -- BATTLEMAN.scr:82
    -- letterbox true
    -- getobjecthandle Camera3 g_hobject
    -- trigger g_hobject On
    -- screenfadein 1
    ctx:wait(1, 5, "GoodGuys") -- BATTLEMAN.scr:89
    do return ctx:exit("") end -- BATTLEMAN.scr:90
end

script.labels["GoodGuys"] = function(ctx)
    -- BATTLEMAN.scr:93
    ctx:state().SCRIPT = " ScriptName Hate.scr" -- BATTLEMAN.scr:96
    ctx:set("sGoodGuyA", "sGoodGuyA + Script") -- BATTLEMAN.scr:98
    ctx:set("sGoodGuyB", "sGoodGuyB + Script") -- BATTLEMAN.scr:99
    ctx:set("sGoodGuyC", "sGoodGuyc + Script") -- BATTLEMAN.scr:100
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("GoodGuys"):pos() -- BATTLEMAN.scr:104-105
    -- Spawn hMonsterC Xpos YPos ZPos sKira
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyA") -- BATTLEMAN.scr:108
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- BATTLEMAN.scr:109
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- BATTLEMAN.scr:110
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyC") -- BATTLEMAN.scr:111
    ctx:wait(1, 5, "End") -- BATTLEMAN.scr:113
    do return ctx:exit("") end -- BATTLEMAN.scr:114
end

script.labels["End"] = function(ctx)
    -- BATTLEMAN.scr:117
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys0"):pos() -- BATTLEMAN.scr:120-121
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:122
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:123
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- BATTLEMAN.scr:124
    -- screenfadeout 1
    -- wait 1 1 FadeIn2
    do return ctx:exit("") end -- BATTLEMAN.scr:128
end

script.labels["FadeIn2"] = function(ctx)
    -- BATTLEMAN.scr:131
end

-- letterbox false
-- getobjecthandle Camera3 g_hobject
-- trigger g_hobject Off
-- screenfadein 1
-- exit
script.labels["OnFight2"] = function(ctx)
    -- BATTLEMAN.scr:141
    if not ctx:hasKey(104) then -- BATTLEMAN.scr:144-145
        do return ctx:exit("") end -- BATTLEMAN.scr:146
    end -- BATTLEMAN.scr:147
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("BadGuys1"):pos() -- BATTLEMAN.scr:150-151
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:152
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterA") -- BATTLEMAN.scr:153
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterB") -- BATTLEMAN.scr:154
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sMonsterC") -- BATTLEMAN.scr:155
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:object("GoodGuys0"):pos() -- BATTLEMAN.scr:160-161
    ctx:state().hMonsterA = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyA") -- BATTLEMAN.scr:164
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- BATTLEMAN.scr:165
    ctx:state().hMonsterB = ctx:spawn("Xpos", "YPos", "ZPos", "sGoodGuyB") -- BATTLEMAN.scr:166
    do return ctx:exit("") end -- BATTLEMAN.scr:168
end

script.labels["Init"] = function(ctx)
    -- BATTLEMAN.scr:171
    if ctx:hasKey(377) then -- BATTLEMAN.scr:174-175
        do return ctx:exit("") end -- BATTLEMAN.scr:176
    end -- BATTLEMAN.scr:177
    if ctx:hasKey(104) then -- BATTLEMAN.scr:179-180
        mm9.gosub(script, ctx, "spawn") -- BATTLEMAN.scr:181
        do return ctx:exit("") end -- BATTLEMAN.scr:182
    end -- BATTLEMAN.scr:183
    do return ctx:exit("") end -- BATTLEMAN.scr:185
end

script.labels["Main"] = function(ctx)
    -- BATTLEMAN.scr:189
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Fight2", "OnFight2") -- BATTLEMAN.scr:194
    ctx:onEvent("OnPostStartWorld", "Init") -- BATTLEMAN.scr:195
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- BATTLEMAN.scr:196
    ctx:onEvent("OnPostSaveLoad", "Init") -- BATTLEMAN.scr:197
    ctx:wait(1, .1, "Init") -- BATTLEMAN.scr:198
    do return ctx:exit("") end -- BATTLEMAN.scr:199
end

return script
