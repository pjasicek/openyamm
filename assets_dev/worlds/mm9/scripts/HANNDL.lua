-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HANNDL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- LoseMan.scr
-- By Timmy
-- 12/20
-- handles losegame cutscene
script.labels["Speak1"] = function(ctx)
    -- HANNDL.scr:16
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:19
    ctx:self():playAnimation("Sc3_hanndl07", "Speak2") -- HANNDL.scr:21
    do return ctx:exit("") end -- HANNDL.scr:23
end

script.labels["Voice1"] = function(ctx)
    -- HANNDL.scr:27
    ctx:playSound("voices\\cinema\\Losegame\\Hanndl07.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:30
    do return ctx:exit("") end -- HANNDL.scr:31
end

script.labels["Speak2"] = function(ctx)
    -- HANNDL.scr:34
    ctx:self():playAnimation("Sc3_hanndl08", "Close") -- HANNDL.scr:37
    do return ctx:exit("") end -- HANNDL.scr:38
end

script.labels["OnSpeak9"] = function(ctx)
    -- HANNDL.scr:41
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:44
    -- ..You again!  Why must you keep bothering me?!
    ctx:self():playAnimation("Sc4_hanndl09", "Done") -- HANNDL.scr:46
    -- wait 1 4.5 Done
    do return ctx:exit("") end -- HANNDL.scr:48
end

script.labels["OnSpeak10"] = function(ctx)
    -- HANNDL.scr:52
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:55
    -- I've told you before...
    ctx:self():playAnimation("Sc4_hanndl10", "Done") -- HANNDL.scr:57
    -- wait 1 4.5 Done
    do return ctx:exit("") end -- HANNDL.scr:59
end

script.labels["OnSpeak11"] = function(ctx)
    -- HANNDL.scr:63
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:66
    -- why?  What's so important...dead soldiers
    ctx:self():playAnimation("Sc4_hanndl11", "Done") -- HANNDL.scr:68
    -- wait 1 5.5 Done
    do return ctx:exit("") end -- HANNDL.scr:70
end

script.labels["OnSpeak12"] = function(ctx)
    -- HANNDL.scr:74
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:77
    -- Destiny?  What destiny...
    ctx:self():playAnimation("Sc4_hanndl12", "Done") -- HANNDL.scr:79
    -- wait 1 11 Done
    do return ctx:exit("") end -- HANNDL.scr:81
end

script.labels["OnSpeak13"] = function(ctx)
    -- HANNDL.scr:85
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:88
    -- You seem to believe it.
    ctx:self():playAnimation("Sc4_hanndl13", "OnSpeak14") -- HANNDL.scr:90
    -- wait 1 4.5 OnSpeak14
    do return ctx:exit("") end -- HANNDL.scr:92
end

script.labels["OnSpeak14"] = function(ctx)
    -- HANNDL.scr:96
    -- If I am to let you in...Writ of fate...Wyrdes.
    ctx:self():playAnimation("Sc4_hanndl14", "DoNothing") -- HANNDL.scr:101
    do return ctx:exit("") end -- HANNDL.scr:102
end

script.labels["OnSpeak15"] = function(ctx)
    -- HANNDL.scr:106
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:109
    -- ...Dark passageway...Transport you to the entrance
    ctx:self():playAnimation("Sc4_hanndl15", "close") -- HANNDL.scr:112
    do return ctx:exit("") end -- HANNDL.scr:113
end

script.labels["OnSpeak16"] = function(ctx)
    -- HANNDL.scr:117
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:120
    -- ...Well?
    ctx:self():playAnimation("sc5_Hanndl16", "DoNothing") -- HANNDL.scr:122
    do return ctx:exit("") end -- HANNDL.scr:123
end

script.labels["OnSpeak17"] = function(ctx)
    -- HANNDL.scr:127
    ctx:getParam(0, "hTriggeredMe") -- HANNDL.scr:130
    -- ...Harrumph!
    ctx:self():playAnimation("sc5_Hanndl17", "DoNothing") -- HANNDL.scr:132
    do return ctx:exit("") end -- HANNDL.scr:133
end

script.labels["Voice2"] = function(ctx)
    -- HANNDL.scr:137
    ctx:playSound("voices\\cinema\\Losegame\\Hanndl08.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:140
    do return ctx:exit("") end -- HANNDL.scr:141
end

script.labels["OnVoice9"] = function(ctx)
    -- HANNDL.scr:144
    -- ..You again!  Why must you keep bothering me?!
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl09.wav", "DoNothing", 100, 240000, "FALSE", 100) -- HANNDL.scr:148
    do return ctx:exit("") end -- HANNDL.scr:149
end

script.labels["OnVoice10"] = function(ctx)
    -- HANNDL.scr:152
    -- I've told you before...not letting you in.
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:156
    do return ctx:exit("") end -- HANNDL.scr:157
end

script.labels["OnVoice11"] = function(ctx)
    -- HANNDL.scr:160
    -- Why?  ...important...Dead soldiers.
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl11.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:164
    do return ctx:exit("") end -- HANNDL.scr:165
end

script.labels["OnVoice12"] = function(ctx)
    -- HANNDL.scr:168
    -- Destiny?  What destiny?.,.position to know.
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl12.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:172
    do return ctx:exit("") end -- HANNDL.scr:173
end

script.labels["OnVoice13"] = function(ctx)
    -- HANNDL.scr:176
    -- You seem to believe it.
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl13.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:180
    do return ctx:exit("") end -- HANNDL.scr:181
end

script.labels["OnVoice14"] = function(ctx)
    -- HANNDL.scr:184
    -- If if am to let you in...Writ of Fate.
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl14.wav", "Done", 100, 24000, "FALSE", 100) -- HANNDL.scr:188
    do return ctx:exit("") end -- HANNDL.scr:189
end

script.labels["OnVoice15"] = function(ctx)
    -- HANNDL.scr:192
    -- ...Travel through the Dark Passageway...Teleport you to the entrance
    ctx:playSound("voices\\cinema\\writoffate\\Hanndl15.wav", "DoNothing", 100, 24000, "FALSE", 100) -- HANNDL.scr:196
    do return ctx:exit("") end -- HANNDL.scr:197
end

script.labels["OnVoice16"] = function(ctx)
    -- HANNDL.scr:200
    -- Well?
    ctx:playSound("voices\\cinema\\presenthanndlwithwrit\\Hanndl16.wav", "Done", 100, 24000, "FALSE", 100) -- HANNDL.scr:204
    do return ctx:exit("") end -- HANNDL.scr:205
end

script.labels["OnVoice17"] = function(ctx)
    -- HANNDL.scr:208
    -- Harrumph
    ctx:playSound("voices\\cinema\\presenthanndlwithwrit\\Hanndl17b.wav", "Close", 100, 24000, "FALSE", 100) -- HANNDL.scr:212
    do return ctx:exit("") end -- HANNDL.scr:213
end

script.labels["Close"] = function(ctx)
    -- HANNDL.scr:216
    ctx:trigger("hTriggeredMe", "FadeOut") -- HANNDL.scr:220
    do return ctx:exit("") end -- HANNDL.scr:221
end

script.labels["Done"] = function(ctx)
    -- HANNDL.scr:224
    ctx:trigger("hTriggeredMe", "Done") -- HANNDL.scr:228
    do return ctx:exit("") end -- HANNDL.scr:229
end

script.labels["Main"] = function(ctx)
    -- HANNDL.scr:233
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Speak", "Speak1") -- HANNDL.scr:238
    ctx:addTrigger("Speak9", "OnSpeak9") -- HANNDL.scr:239
    ctx:addTrigger("Speak10", "OnSpeak10") -- HANNDL.scr:240
    ctx:addTrigger("Speak11", "OnSpeak11") -- HANNDL.scr:241
    ctx:addTrigger("Speak12", "OnSpeak12") -- HANNDL.scr:242
    ctx:addTrigger("Speak13", "OnSpeak13") -- HANNDL.scr:243
    ctx:addTrigger("Speak14", "OnSpeak14") -- HANNDL.scr:244
    ctx:addTrigger("Speak15", "OnSpeak15") -- HANNDL.scr:245
    ctx:addTrigger("Speak16", "OnSpeak16") -- HANNDL.scr:246
    ctx:addTrigger("Speak17", "OnSpeak17") -- HANNDL.scr:247
    ctx:addModelKey("Speak1", "Voice1") -- HANNDL.scr:248
    ctx:addModelKey("Speak2", "Voice2") -- HANNDL.scr:249
    ctx:addModelKey("Speak9", "OnVoice9") -- HANNDL.scr:250
    ctx:addModelKey("speak10", "OnVoice10") -- HANNDL.scr:251
    ctx:addModelKey("speak11", "OnVoice11") -- HANNDL.scr:252
    ctx:addModelKey("speak12", "OnVoice12") -- HANNDL.scr:253
    ctx:addModelKey("Speak13", "OnVoice13") -- HANNDL.scr:254
    ctx:addModelKey("Speak14", "OnVoice14") -- HANNDL.scr:255
    ctx:addModelKey("Speak15", "OnVoice15") -- HANNDL.scr:256
    ctx:addModelKey("Speak16", "OnVoice16") -- HANNDL.scr:257
    ctx:addModelKey("Speak17", "OnVoice17") -- HANNDL.scr:258
    ctx:addModelKey("Done", "Done") -- HANNDL.scr:259
    ctx:addModelKey("Close", "Close") -- HANNDL.scr:260
    do return ctx:exit("") end -- HANNDL.scr:261
end

return script
