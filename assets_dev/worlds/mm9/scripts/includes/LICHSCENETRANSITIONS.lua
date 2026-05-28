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
    ctx:command("getobjecthandle", "LichKing1, hCreature") -- LICHSCENETRANSITIONS.inc:16
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:17
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:18
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:19
    ctx:command("getobjecthandle", "LichKing2, hCreature") -- LICHSCENETRANSITIONS.inc:21
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:22
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:23
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:24
    ctx:command("getobjecthandle", "LichKing3, hCreature") -- LICHSCENETRANSITIONS.inc:26
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:27
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:28
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:29
    ctx:command("getobjecthandle", "Oculus0, hCreature") -- LICHSCENETRANSITIONS.inc:31
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:32
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:33
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:34
    ctx:command("getobjecthandle", "Oculus1, hCreature") -- LICHSCENETRANSITIONS.inc:36
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:37
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:38
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:39
    ctx:command("getobjecthandle", "Oculus2, hCreature") -- LICHSCENETRANSITIONS.inc:41
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:42
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:43
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:44
    ctx:command("getobjecthandle", "Oculus3, hCreature") -- LICHSCENETRANSITIONS.inc:46
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:47
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:48
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:49
    ctx:command("getobjecthandle", "Oculus4, hCreature") -- LICHSCENETRANSITIONS.inc:51
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:52
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:53
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:54
    ctx:command("getobjecthandle", "SkeletonMaster0, hCreature") -- LICHSCENETRANSITIONS.inc:56
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:57
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:58
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:59
    ctx:command("getobjecthandle", "SkeletonMaster1, hCreature") -- LICHSCENETRANSITIONS.inc:61
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:62
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:63
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:64
    ctx:command("getobjecthandle", "SkeletonMaster4, hCreature") -- LICHSCENETRANSITIONS.inc:66
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:67
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:68
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:69
    ctx:command("getobjecthandle", "SkeletonMaster5, hCreature") -- LICHSCENETRANSITIONS.inc:71
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:72
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:73
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:74
    ctx:command("getobjecthandle", "SkeletonMaster6, hCreature") -- LICHSCENETRANSITIONS.inc:76
    ctx:command("setstat", "hCreature, gravity, FALSE") -- LICHSCENETRANSITIONS.inc:77
    ctx:command("clearflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:78
    ctx:command("clearflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:79
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:81
end

script.labels["ReplaceCreatures"] = function(ctx)
    -- LICHSCENETRANSITIONS.inc:84
    ctx:command("getobjecthandle", "LichKing1, hCreature") -- LICHSCENETRANSITIONS.inc:86
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:87
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:88
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:89
    ctx:command("getobjecthandle", "LichKing2, hCreature") -- LICHSCENETRANSITIONS.inc:91
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:92
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:93
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:94
    ctx:command("getobjecthandle", "LichKing3, hCreature") -- LICHSCENETRANSITIONS.inc:96
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:97
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:98
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:99
    ctx:command("getobjecthandle", "Oculus0, hCreature") -- LICHSCENETRANSITIONS.inc:101
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:102
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:103
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:104
    ctx:command("getobjecthandle", "Oculus1, hCreature") -- LICHSCENETRANSITIONS.inc:106
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:107
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:108
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:109
    ctx:command("getobjecthandle", "Oculus2, hCreature") -- LICHSCENETRANSITIONS.inc:111
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:112
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:113
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:114
    ctx:command("getobjecthandle", "Oculus3, hCreature") -- LICHSCENETRANSITIONS.inc:116
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:117
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:118
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:119
    ctx:command("getobjecthandle", "Oculus4, hCreature") -- LICHSCENETRANSITIONS.inc:121
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:122
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:123
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:124
    ctx:command("getobjecthandle", "SkeletonMaster0, hCreature") -- LICHSCENETRANSITIONS.inc:126
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:127
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:128
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:129
    ctx:command("getobjecthandle", "SkeletonMaster1, hCreature") -- LICHSCENETRANSITIONS.inc:131
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:132
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:133
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:134
    ctx:command("getobjecthandle", "SkeletonMaster4, hCreature") -- LICHSCENETRANSITIONS.inc:136
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:137
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:138
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:139
    ctx:command("getobjecthandle", "SkeletonMaster5, hCreature") -- LICHSCENETRANSITIONS.inc:141
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:142
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:143
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:144
    ctx:command("getobjecthandle", "SkeletonMaster6, hCreature") -- LICHSCENETRANSITIONS.inc:146
    ctx:command("setstat", "hCreature, gravity, TRUE") -- LICHSCENETRANSITIONS.inc:147
    ctx:command("setflag", "hCreature, FLAG_SOLID") -- LICHSCENETRANSITIONS.inc:148
    ctx:command("setflag", "hCreature, FLAG_VISIBLE") -- LICHSCENETRANSITIONS.inc:149
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:151
end

script.labels["RemoveActors"] = function(ctx)
    -- LICHSCENETRANSITIONS.inc:154
    ctx:command("getobjecthandle", "LichSorcerer, hCreature") -- LICHSCENETRANSITIONS.inc:156
    if ctx:condition("hCreature!=0") then -- LICHSCENETRANSITIONS.inc:157
        ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:158
    end -- LICHSCENETRANSITIONS.inc:159
    ctx:command("getobjecthandle", "LichSorcererNew, hCreature") -- LICHSCENETRANSITIONS.inc:161
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:162
    ctx:command("getobjecthandle", "EscortLich0, hCreature") -- LICHSCENETRANSITIONS.inc:164
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:165
    ctx:command("getobjecthandle", "EscortLich1, hCreature") -- LICHSCENETRANSITIONS.inc:167
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:168
    ctx:command("getobjecthandle", "EscortLich2, hCreature") -- LICHSCENETRANSITIONS.inc:170
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:171
    ctx:command("getobjecthandle", "EscortLich3, hCreature") -- LICHSCENETRANSITIONS.inc:173
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:174
    ctx:command("getobjecthandle", "KiddieSacrifice0, hCreature") -- LICHSCENETRANSITIONS.inc:176
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:177
    ctx:command("getobjecthandle", "KiddieSacrifice1, hCreature") -- LICHSCENETRANSITIONS.inc:179
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:180
    ctx:command("getobjecthandle", "KiddieSacrifice2, hCreature") -- LICHSCENETRANSITIONS.inc:182
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:183
    ctx:command("getobjecthandle", "KiddieSacrifice3, hCreature") -- LICHSCENETRANSITIONS.inc:185
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:186
    ctx:command("getobjecthandle", "KiddieSacrifice4, hCreature") -- LICHSCENETRANSITIONS.inc:188
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:189
    ctx:command("getobjecthandle", "KiddieSacrifice5, hCreature") -- LICHSCENETRANSITIONS.inc:191
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:192
    ctx:command("getobjecthandle", "KiddieSacrifice6, hCreature") -- LICHSCENETRANSITIONS.inc:194
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:195
    ctx:command("getobjecthandle", "KiddieSacrifice7, hCreature") -- LICHSCENETRANSITIONS.inc:197
    ctx:command("removeobject", "hCreature") -- LICHSCENETRANSITIONS.inc:198
    do return ctx:exit("TRUE") end -- LICHSCENETRANSITIONS.inc:200
end

return script
