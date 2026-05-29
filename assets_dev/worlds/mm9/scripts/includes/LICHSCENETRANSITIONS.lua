-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHSCENETRANSITIONS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "flags.inc" }

-- LichSceneTransition.inc
-- by SJR
-- Purpose:remove the creatures
-- already there and
-- restore them later.
script.labels["RemoveCreatures"] = function(ctx)
    -- LICHSCENETRANSITIONS.inc:14
    ctx:object("LichKing1"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:16-17
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:18
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:19
    ctx:object("LichKing2"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:21-22
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:23
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:24
    ctx:object("LichKing3"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:26-27
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:28
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:29
    ctx:object("Oculus0"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:31-32
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:33
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:34
    ctx:object("Oculus1"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:36-37
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:38
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:39
    ctx:object("Oculus2"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:41-42
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:43
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:44
    ctx:object("Oculus3"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:46-47
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:48
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:49
    ctx:object("Oculus4"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:51-52
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:53
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:54
    ctx:object("SkeletonMaster0"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:56-57
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:58
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:59
    ctx:object("SkeletonMaster1"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:61-62
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:63
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:64
    ctx:object("SkeletonMaster4"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:66-67
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:68
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:69
    ctx:object("SkeletonMaster5"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:71-72
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:73
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:74
    ctx:object("SkeletonMaster6"):setStat("gravity", false) -- LICHSCENETRANSITIONS.inc:76-77
    ctx:object("hCreature"):setFlag("FLAG_SOLID", false) -- LICHSCENETRANSITIONS.inc:78
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", false) -- LICHSCENETRANSITIONS.inc:79
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:81
end

script.labels["ReplaceCreatures"] = function(ctx)
    -- LICHSCENETRANSITIONS.inc:84
    ctx:object("LichKing1"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:86-87
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:88
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:89
    ctx:object("LichKing2"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:91-92
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:93
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:94
    ctx:object("LichKing3"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:96-97
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:98
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:99
    ctx:object("Oculus0"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:101-102
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:103
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:104
    ctx:object("Oculus1"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:106-107
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:108
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:109
    ctx:object("Oculus2"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:111-112
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:113
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:114
    ctx:object("Oculus3"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:116-117
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:118
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:119
    ctx:object("Oculus4"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:121-122
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:123
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:124
    ctx:object("SkeletonMaster0"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:126-127
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:128
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:129
    ctx:object("SkeletonMaster1"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:131-132
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:133
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:134
    ctx:object("SkeletonMaster4"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:136-137
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:138
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:139
    ctx:object("SkeletonMaster5"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:141-142
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:143
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:144
    ctx:object("SkeletonMaster6"):setStat("gravity", true) -- LICHSCENETRANSITIONS.inc:146-147
    ctx:object("hCreature"):setFlag("FLAG_SOLID", true) -- LICHSCENETRANSITIONS.inc:148
    ctx:object("hCreature"):setFlag("FLAG_VISIBLE", true) -- LICHSCENETRANSITIONS.inc:149
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:151
end

script.labels["RemoveActors"] = function(ctx)
    -- LICHSCENETRANSITIONS.inc:154
    ctx:state().hCreature = ctx:objectOrNil("LichSorcerer") -- LICHSCENETRANSITIONS.inc:156
    if ctx:condition("hCreature!=0") then -- LICHSCENETRANSITIONS.inc:157
        ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:158
    end -- LICHSCENETRANSITIONS.inc:159
    ctx:state().hCreature = ctx:objectOrNil("LichSorcererNew") -- LICHSCENETRANSITIONS.inc:161
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:162
    ctx:state().hCreature = ctx:objectOrNil("EscortLich0") -- LICHSCENETRANSITIONS.inc:164
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:165
    ctx:state().hCreature = ctx:objectOrNil("EscortLich1") -- LICHSCENETRANSITIONS.inc:167
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:168
    ctx:state().hCreature = ctx:objectOrNil("EscortLich2") -- LICHSCENETRANSITIONS.inc:170
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:171
    ctx:state().hCreature = ctx:objectOrNil("EscortLich3") -- LICHSCENETRANSITIONS.inc:173
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:174
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice0") -- LICHSCENETRANSITIONS.inc:176
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:177
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice1") -- LICHSCENETRANSITIONS.inc:179
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:180
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice2") -- LICHSCENETRANSITIONS.inc:182
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:183
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice3") -- LICHSCENETRANSITIONS.inc:185
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:186
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice4") -- LICHSCENETRANSITIONS.inc:188
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:189
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice5") -- LICHSCENETRANSITIONS.inc:191
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:192
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice6") -- LICHSCENETRANSITIONS.inc:194
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:195
    ctx:state().hCreature = ctx:objectOrNil("KiddieSacrifice7") -- LICHSCENETRANSITIONS.inc:197
    ctx:object("hCreature"):remove() -- LICHSCENETRANSITIONS.inc:198
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:200
end

return script
