-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC378.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basedoor.inc" }

-- NPC378.scr
-- timmy
-- handles Thorolf Ratatoskssen voice and quest stuff
-- edited by Bones 5/28/03
-- TELP Patch 1.3 -- Makes dialog with messenger unavoidable.
-- Vanishes after ThronheimCity message given.
-- Moves TC's Thorolf1 to a better position.
-- flag variables
-- parameters
-- p0 My object name
script.labels["OnRude"] = function(ctx)
    -- NPC378.scr:39
    ctx:self():setTarget(nil) -- NPC378.scr:42
    ctx:state().bTalking = false -- NPC378.scr:43
    if ctx:hasKey(107) then -- NPC378.scr:44-45
        ctx:wait(1, 2, "Vanish") -- NPC378.scr:46
        do return ctx:exit("") end -- NPC378.scr:47
    end -- NPC378.scr:48
    if ctx:hasKey(106) then -- NPC378.scr:49-50
        ctx:doRude(378) -- NPC378.scr:51
        do return ctx:exit("") end -- NPC378.scr:52
    end -- NPC378.scr:53
    if ctx:hasKey(84) then -- NPC378.scr:54-55
        ctx:wait(1, 2, "Vanish") -- NPC378.scr:56
        do return ctx:exit("") end -- NPC378.scr:57
    end -- NPC378.scr:58
    if ctx:hasKey(83) then -- NPC378.scr:59-60
        ctx:doRude(378) -- NPC378.scr:61
    end -- NPC378.scr:62
    do return ctx:exit("") end -- NPC378.scr:63
end

script.labels["OnUse"] = function(ctx)
    -- NPC378.scr:67
    ctx:self():stop() -- NPC378.scr:69
    ctx:self():setTarget(nil) -- NPC378.scr:70
    if ctx:condition("sWhoAmI==Thorolf0") then -- NPC378.scr:72
        ctx:state().g_hobject = ctx:objectOrNil("thorolf1") -- NPC378.scr:73
        ctx:object("g_hobject"):remove() -- NPC378.scr:74
    else -- NPC378.scr:75
        ctx:state().g_hobject = ctx:objectOrNil("thorolf0") -- NPC378.scr:76
        ctx:object("g_hobject"):remove() -- NPC378.scr:77
    end -- NPC378.scr:78
    do return ctx:exit("") end -- NPC378.scr:79
end

script.labels["Init"] = function(ctx)
    -- NPC378.scr:82
    ctx:state().g_hobject = ctx:self() -- NPC378.scr:88
    ctx:self():setFlag("visible", false) -- NPC378.scr:89
    ctx:self():setFlag("solid", false) -- NPC378.scr:90
    ctx:self():setFlag("gravity", false) -- NPC378.scr:91
    ctx:cprint("DELETED", "ME", "FIRST...") -- NPC378.scr:92
    if ctx:condition("sWhoamI==Frosgard") then -- NPC378.scr:94
        do return ctx:exit("") end -- NPC378.scr:95
    end -- NPC378.scr:96
    if ctx:hasKey(83) then -- NPC378.scr:98-99
        ctx:state().g_hobject = ctx:self() -- NPC378.scr:100
        ctx:self():setFlag("visible", true) -- NPC378.scr:101
        ctx:self():setFlag("solid", true) -- NPC378.scr:102
        ctx:self():setFlag("gravity", true) -- NPC378.scr:103
        ctx:cprint("MADE", "ME", "VISIBLE", "TO", "GIVE", "STURM", "AND", "DRANG", "MESSAGE") -- NPC378.scr:104
        ctx:state().g_nPad2, ctx:state().g_nPad3, ctx:state().g_nPad4 = ctx:self():pos() -- NPC378.scr:106
        if ctx:condition("g_nPad4 == 3712") then -- NPC378.scr:107
            ctx:self():setPos(-2806, 1240, 5040) -- NPC378.scr:108
        end -- NPC378.scr:109
    end -- NPC378.scr:111
    if ctx:hasKey(84) then -- NPC378.scr:113-114
        ctx:state().g_hobject = ctx:self() -- NPC378.scr:115
        ctx:self():setFlag("visible", false) -- NPC378.scr:116
        ctx:self():setFlag("solid", false) -- NPC378.scr:117
        ctx:self():setFlag("gravity", false) -- NPC378.scr:118
        ctx:cprint("DELETED", "ME", "BECAUSE", "WAR", "IS", "FIXED.") -- NPC378.scr:119
    end -- NPC378.scr:120
    ctx:state().g_hPlayer = ctx:player() -- NPC378.scr:122
    ctx:self():faceObject(ctx:player()) -- NPC378.scr:123
    ctx:onEvent("OnFoundPlayer", "OnFound") -- NPC378.scr:124
    do return ctx:exit("") end -- NPC378.scr:125
end

script.labels["OnAppear2"] = function(ctx)
    -- NPC378.scr:130
    ctx:state().g_hPlayer = ctx:player() -- NPC378.scr:134
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:player():pos() -- NPC378.scr:136
    ctx:set("MyX", "XPos + 256") -- NPC378.scr:137
    ctx:set("MyY", "YPos + 20") -- NPC378.scr:138
    ctx:set("MyZ", "ZPos + 256") -- NPC378.scr:139
    ctx:self():setFlag("Solid", false) -- NPC378.scr:142
    ctx:self():setFlag("gravity", false) -- NPC378.scr:143
    ctx:self():setPos("MyX", "MyY", "MyZ") -- NPC378.scr:144
    ctx:wait(1, 2, "OnTeleport") -- NPC378.scr:145
    do return ctx:exit("") end -- NPC378.scr:146
end

script.labels["OnAppear"] = function(ctx)
    -- NPC378.scr:149
    ctx:getParam(0, "g_hplayer") -- NPC378.scr:152
    if not ctx:hasKey(106) then -- NPC378.scr:154-155
        do return ctx:exit("") end -- NPC378.scr:156
    end -- NPC378.scr:157
    -- set my pos near the player...
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:player():pos() -- NPC378.scr:162
    ctx:self():setPos("XPos", "YPos", "ZPos") -- NPC378.scr:165
    ctx:wait(1, 2, "OnTeleport") -- NPC378.scr:166
    do return ctx:exit("") end -- NPC378.scr:167
end

script.labels["OnTeleport"] = function(ctx)
    -- NPC378.scr:170
    -- teleport in...
    -- play vanish effect here
    ctx:self():doClientFx("Ceffect") -- NPC378.scr:177
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC378.scr:178
    ctx:wait(1, 1, "Appear2b") -- NPC378.scr:179
    do return ctx:exit("") end -- NPC378.scr:180
end

script.labels["Appear2b"] = function(ctx)
    -- NPC378.scr:183
    ctx:self():setFlag("visible", true) -- NPC378.scr:186
    ctx:playSound("\\Sounds\\spells\\townportal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC378.scr:187
end

-- no exit here on purpose...
script.labels["OnFound"] = function(ctx)
    -- NPC378.scr:192
    if ctx:condition("bTalking==TRUE") then -- NPC378.scr:195
        do return ctx:exit("") end -- NPC378.scr:196
    end -- NPC378.scr:197
    if ctx:hasKey(107) then -- NPC378.scr:199-200
        do return ctx:exit("") end -- NPC378.scr:201
    end -- NPC378.scr:202
    if ctx:hasKey(84) then -- NPC378.scr:204-205
        if not ctx:hasKey(106) then -- NPC378.scr:206-207
            do return ctx:exit("") end -- NPC378.scr:208
        end -- NPC378.scr:209
    end -- NPC378.scr:210
    ctx:state().g_htarget = ctx:player() -- NPC378.scr:212
    ctx:self():runTo(ctx:player(), 16, "Talk") -- NPC378.scr:213
    -- target g_hobject
    -- OnTargetWithinDist 8 Talk
    -- OnLostTarget OnLost
    do return ctx:exit("") end -- NPC378.scr:217
end

script.labels["Talk"] = function(ctx)
    -- NPC378.scr:220
    ctx:self():stop() -- NPC378.scr:223
    ctx:state().bTalking = true -- NPC378.scr:224
    ctx:doRude(378) -- NPC378.scr:225
    ctx:playSound("voices\\NPC\\NPC_378.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC378.scr:226
    if ctx:condition("sWhoAmI==Thorolf0") then -- NPC378.scr:227
        ctx:state().g_hobject = ctx:objectOrNil("thorolf1") -- NPC378.scr:228
        ctx:object("g_hobject"):remove() -- NPC378.scr:229
    else -- NPC378.scr:230
        ctx:state().g_hobject = ctx:objectOrNil("Thorolf0") -- NPC378.scr:231
        ctx:object("g_hobject"):remove() -- NPC378.scr:232
    end -- NPC378.scr:233
    do return ctx:exit("") end -- NPC378.scr:234
end

script.labels["OnLost"] = function(ctx)
    -- NPC378.scr:238
    mm9.gosub(script, ctx, "OnFound") -- NPC378.scr:241
    do return ctx:exit("") end -- NPC378.scr:242
end

script.labels["Vanish"] = function(ctx)
    -- NPC378.scr:245
    -- play vanish effect here
    ctx:self():doClientFx("Ceffect") -- NPC378.scr:250
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC378.scr:251
    ctx:wait(1, 1, "Vanish2b") -- NPC378.scr:252
    do return ctx:exit("") end -- NPC378.scr:253
end

script.labels["Vanish2b"] = function(ctx)
    -- NPC378.scr:256
    ctx:self():setFlag("visible", false) -- NPC378.scr:259
    ctx:playSound("\\Sounds\\spells\\townportal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- NPC378.scr:260
    ctx:wait(1, 1, "Vanish2c") -- NPC378.scr:261
    do return ctx:exit("") end -- NPC378.scr:262
end

script.labels["Vanish2c"] = function(ctx)
    -- NPC378.scr:266
    ctx:self():remove() -- NPC378.scr:268
    do return ctx:exit("") end -- NPC378.scr:269
end

script.labels["Main"] = function(ctx)
    -- NPC378.scr:272
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC378.scr:279
    ctx:getParam(0, "sWhoAmI") -- NPC378.scr:280
    ctx:addTrigger("Use", "OnUse") -- NPC378.scr:281
    ctx:addTrigger("Appear", "OnAppear") -- NPC378.scr:282
    ctx:addTrigger("Appear2", "OnAppear2") -- NPC378.scr:283
    mm9.gosub(script, ctx, "basedoorinit") -- NPC378.scr:284
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC378.scr:285
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC378.scr:286
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC378.scr:287
    ctx:wait(1, .1, "Init") -- NPC378.scr:288
    do return ctx:exit("") end -- NPC378.scr:289
end

return script
