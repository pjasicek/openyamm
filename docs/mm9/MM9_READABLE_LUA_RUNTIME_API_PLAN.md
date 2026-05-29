# MM9 Readable Lua Runtime API Plan

This document defines the intended direction for MM9 `.scr` / `.inc` to Lua generation after the first faithful
transcoding pass. The current generated Lua is deliberately close to the source scripts and routes many operations
through `ctx:command(...)` and `ctx:condition(...)`. That is useful for early losslessness, but it should not be the
long-term shape for script readability or runtime ergonomics.

The goal is generated Lua that remains source-faithful while looking like normal Lua:

- control flow should be native Lua;
- arithmetic, comparisons, loop counters, booleans, and simple arrays should be native Lua;
- object handles should become Lua object proxies with methods;
- expensive or world-owned behavior should remain C++ services exposed through Lua;
- original source files remain the authority, and generated Lua must never be hand-edited.

Related docs:

- `docs/mm9/MM9_DIALOGUE_RUNTIME_PIPELINE_CHECKLIST.md`
- `docs/mm9/MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md`
- `docs/mm9/MM9_SCRIPT_OBJECT_HANDLE_DIRECT_VS_ROUTED.md`
- `docs/mm9/MM9_DAT_PHYSICS_COLLISION_CONTRACT.md`
- `docs/mm9/MM9_RUNTIME_EVENTS_PLAYABLE_SLICE_CHECKLIST.md`

## Current State

The pipeline currently generates one Lua file for each MM9 script source:

```text
mm9/extracted/SCRIPTS/SCRIPTS/*.scr -> assets_dev/worlds/mm9/scripts/*.lua
mm9/extracted/SCRIPTS/SCRIPTS/*.inc -> assets_dev/worlds/mm9/scripts/includes/*.lua
```

The generated Lua already preserves:

- labels as `script.labels["Name"] = function(ctx)`;
- includes as metadata rows;
- source line comments;
- original comments where useful;
- `gosub` / `goto` through generated runtime support;
- direct wrappers for known high-value commands such as `ctx:hasKey`, `ctx:giveKey`, `ctx:hasItem`, `ctx:trigger`.

It still emits many interpreter-like forms:

```lua
ctx:command("index", "= 0")
while ctx:condition("index < 10") do
    ctx:command("arrayget", "aGroup1,index,npc_id")
    ctx:command("index", "= index + 1")
end
```

That shape is acceptable as a compatibility bridge, but it hides simple script logic behind strings.

## Desired Shape

For pure script logic, generate normal Lua:

```lua
script.labels["LaunchGroup"] = function(ctx)
    local index = 0
    while index < 10 do
        local npc_id = 0

        if current_group == Group1 then
            npc_id = aGroup1:get(index)
        end
        if current_group == Group2 then
            npc_id = aGroup2:get(index)
        end

        if npc_id ~= 0 then
            mm9.gosub(script, ctx, "CreateMarker")
            mm9.gosub(script, ctx, "GoToLocation")
        end

        index = index + 1
    end
    return ctx:exit()
end
```

For object operations, generate object-oriented Lua:

```lua
local terrain = ctx:object("Terrain3")
terrain:trigger("open")
terrain:trigger("sinkspeed")
```

or for a single-use object:

```lua
ctx:object("Terrain3"):trigger("open")
```

This keeps object resolution and world behavior in C++, but makes authored script intent readable.

## Runtime Model

### Context

`ctx` remains the script execution context. It owns:

- access to the active script source and active object;
- MM9 state domains;
- command diagnostics;
- callback registration and dispatch;
- bridge methods into world, combat, audio, animation, and physics services.

The context should expose typed helpers instead of only generic command strings.

Expected top-level helpers:

```lua
ctx:self()                     -- active owning object proxy
ctx:player()                   -- player/party proxy where MM9 treats player as object
ctx:object(nameOrHandle)        -- object proxy by authored name, class/name alias, or handle
ctx:param(index)                -- raw script callback parameter
ctx:paramObject(index)          -- callback parameter resolved as object proxy
ctx:var(name)                   -- explicit fallback for dynamic variable access, if needed
ctx:exit(value)                 -- preserve SCR Exit behavior
```

### Object Proxies

Objects should be exposed to Lua as generic proxies. The proxy may be userdata or a table with a hidden handle. It must
not duplicate object state; it should call back into `Mm9ScriptRuntime` and the active MM9 world view.

This is intentionally aligned with LithTech's `HOBJECT` model: an object proxy is a generic handle-facing facade, not a
typed Lua subclass. Methods fall into the same buckets as the underlying runtime:

- direct generic operations such as name/class lookup, position, flags, stats, links, and removal;
- direct capability operations such as model animation, sockets, sound, FX, camera, and light behavior;
- routed operations such as `trigger`, callbacks, movement, actor policy, combat, and world mechanisms.

Generated Lua must not call another object's generated label directly. `object:trigger("Use")` must route through the
MM9 runtime message/event bus so the target object's registered script handler, native capability handler, or future DAT
world object implementation decides what the message means.

Baseline object methods:

```lua
object:handle()
object:name()
object:className()
object:trigger(message)
object:pos()
object:setPos(x, y, z)
object:rotation()
object:setRotation(x, y, z, spin)
object:faceObject(target, rate, callback)
object:facePos(x, y, z, rate, callback)
object:walkTo(target, range, callback)
object:runTo(target, range, callback)
object:moveToPos(x, y, z, rate, callback)
object:moveDir(x, y, z, distance, rate, callback)
object:setFlag(flag, enabled)
object:flag(flag)
object:getStat(stat)
object:setStat(stat, value)
object:playAnimation(name, loop, callback)
object:loopAnimation(name, callback)
object:attack(callback)
object:rangeAttack(callback)
object:canAttack()
object:canRangeAttack()
object:isAttacking()
object:canReach(target)
object:distanceTo(target)
object:remove()
```

Typed helpers may be added later, but the first implementation should use one generic object interface because MM9
scripts treat handles uniformly.

If an object proxy is stored in `ctx:state()`, the stored value must be save/load-safe. The state backend may expose it
as a proxy to Lua, but the persisted value should be the stable object handle, not a raw Lua table or userdata pointer.

### Variables

SCR globals such as `g_nTemp`, `g_hObject`, `g_hTarget`, `current_group`, and `index` are real script variables. The
generator should not treat names like `g_hObject` as reserved aliases unless the source command actually asks for the
active object.

Runtime resolution order should be:

1. explicit Lua local generated by the current label;
2. assigned object handle variable;
3. script numeric/string variable;
4. console/map/global variable domains where applicable;
5. object lookup by name/class;
6. literal string fallback.

Important correction: `g_hObject` and `g_hobject` are declared handle variables in `GLOBALS.inc`. If a script assigns
`GetObjectHandle Terrain3 g_hObject`, later `g_hObject` use must resolve to `Terrain3`, not to the active object.

### Arrays

MM9 SCR arrays appear to be addressed like C-style zero-based arrays in several scripts. Do not emit plain Lua tables
without confirming and preserving index semantics.

Use a runtime array wrapper first:

```lua
npc_id = aGroup1:get(index)
aGroup1:set(index, npc_id)
```

Later, generated helpers can provide a natural syntax only if it preserves original indexing.

## What Stays In C++

Keep these as engine/world services:

- object lookup and stable handle resolution;
- pathing, collision, movement, obstacle/stuck callbacks;
- floor/LOS/reachability and world queries;
- target discovery and object searches;
- combat, attack hit logic, damage, projectiles;
- animation dispatch and model key callbacks;
- sound, music, client FX, presentation events;
- timers, waits, callback queues, and save/load of pending script state.

Lua should decide policy. C++ should execute world primitives.

## What Should Become Native Lua

Translate these away from `ctx:command(...)` where semantics are clear:

- bare assignment: `index = 0`;
- `set`, `add`, `sub`, `mul`, `div` on script variables;
- numeric and boolean comparisons in `if` / `while`;
- simple local counters and temporaries;
- boolean scratch variable patterns;
- simple string concatenation if the SCR expression is unambiguous;
- `arrayget` / `arrayput` through zero-based wrapper methods;
- immediate object-handle temporary patterns.

## Concrete Generation Examples

These examples are not hand-authored replacements. They describe what the exporter should eventually produce from the
same source scripts while keeping the same source line mapping, labels, callbacks, and command semantics.

### `MAGICCARPET.lua`

`MAGICCARPET.scr` is a small moving-object script. It is a good test case because it combines script parameters,
callbacks, object handles, position queries, velocity math, sound, and scheduled looping.

Current generated shape:

```lua
script.labels["InitMagicCarpet"] = function(ctx)
    ctx:addTrigger("Use", "StartRising") -- MAGICCARPET.scr:37
    ctx:command("getplayerhandle", "hPlayer") -- MAGICCARPET.scr:39
    ctx:command("getmyhandle", "hMe") -- MAGICCARPET.scr:40
    ctx:command("getpos", "hMe, xMe,yMe,zMe") -- MAGICCARPET.scr:42
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:44
end

script.labels["RiseLoop"] = function(ctx)
    if ctx:condition("nVel>0") then -- MAGICCARPET.scr:62
        mm9.gosub(script, ctx, "CheckPOS") -- MAGICCARPET.scr:63
    end -- MAGICCARPET.scr:64
    ctx:command("getfacedir", "hPlayer, nVelx,nTemp,nVelz") -- MAGICCARPET.scr:65
    ctx:command("vecnorm", "nVelx,nTemp,nVelz") -- MAGICCARPET.scr:66
    ctx:command("vecscale", "nVelx,nTemp,nVelz, nVel") -- MAGICCARPET.scr:67
    ctx:command("setvelocity", "hMe, nVelx,nVely,nVelz") -- MAGICCARPET.scr:68
    ctx:command("wait", "0, .1, RiseLoop") -- MAGICCARPET.scr:70
    do return ctx:exit("TRUE") end -- MAGICCARPET.scr:72
end
```

Desired generated shape:

```lua
script.labels["InitMagicCarpet"] = function(ctx)
    ctx:addTrigger("Use", "StartRising") -- MAGICCARPET.scr:37

    local state = ctx:state()
    state.hPlayer = ctx:player() -- MAGICCARPET.scr:39
    state.hMe = ctx:self() -- MAGICCARPET.scr:40
    state.xMe, state.yMe, state.zMe = state.hMe:pos() -- MAGICCARPET.scr:42

    return ctx:exit(true) -- MAGICCARPET.scr:44
end

script.labels["RiseLoop"] = function(ctx)
    local state = ctx:state()

    if state.nVel > 0 then -- MAGICCARPET.scr:62
        mm9.gosub(script, ctx, "CheckPOS") -- MAGICCARPET.scr:63
    end

    local velocity = state.hPlayer:faceDir() -- MAGICCARPET.scr:65
    velocity = velocity:normalized():scaled(state.nVel) -- MAGICCARPET.scr:66-67
    state.hMe:setVelocity(velocity.x, state.nVely, velocity.z) -- MAGICCARPET.scr:68

    ctx:wait(0, 0.1, "RiseLoop") -- MAGICCARPET.scr:70
    return ctx:exit(true) -- MAGICCARPET.scr:72
end
```

Notes:

- `hPlayer`, `hMe`, `nHeight`, `nVel`, and `nVely` must live in runtime-backed script state because callbacks resume
  later through `Wait`.
- `ctx:self()` and `ctx:player()` should return object proxies, not raw strings.
- Vector helpers can be generated either as `ctx:vec(...)` values or as direct runtime calls. The key improvement is
  that vector math should not remain hidden in command strings.
- `ctx:wait(...)` remains a C++ scheduler service. Lua should not implement timer dispatch itself.
- `ResetLift` should similarly become direct state assignment plus `ctx:playSound(...)` and `ctx:addTrigger(...)`.

### `MM_DRANGHEIMCITY.lua`

`MM_DRANGHEIMCITY.scr` is a larger scheduling and NPC movement script. It is a good test case for arrays, state,
object proxies, and repeated generated boilerplate.

Current generated `LaunchGroup`:

```lua
script.labels["LaunchGroup"] = function(ctx)
    ctx:command("index", "= 0") -- MM_DRANGHEIMCITY.scr:127
    while ctx:condition("index < 10") do -- MM_DRANGHEIMCITY.scr:129
        ctx:command("npc_id", "= 0") -- MM_DRANGHEIMCITY.scr:131
        if ctx:condition("current_group == Group1") then -- MM_DRANGHEIMCITY.scr:133
            ctx:command("arrayget", "aGroup1,index,npc_id") -- MM_DRANGHEIMCITY.scr:134
        end -- MM_DRANGHEIMCITY.scr:135
        if ctx:condition("current_group == Group2") then -- MM_DRANGHEIMCITY.scr:137
            ctx:command("arrayget", "aGroup2,index,npc_id") -- MM_DRANGHEIMCITY.scr:138
        end -- MM_DRANGHEIMCITY.scr:139
        if ctx:condition("npc_id != 0") then -- MM_DRANGHEIMCITY.scr:149
            mm9.gosub(script, ctx, "CreateMarker") -- MM_DRANGHEIMCITY.scr:150
            mm9.gosub(script, ctx, "GoToLocation") -- MM_DRANGHEIMCITY.scr:151
        end -- MM_DRANGHEIMCITY.scr:152
        ctx:command("index", "= index + 1") -- MM_DRANGHEIMCITY.scr:154
    end -- MM_DRANGHEIMCITY.scr:155
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:157
end
```

Desired generated `LaunchGroup`:

```lua
script.labels["LaunchGroup"] = function(ctx)
    local state = ctx:state()
    local currentGroup = state.current_group

    for index = 0, 9 do -- MM_DRANGHEIMCITY.scr:127-129
        local npcId = 0 -- MM_DRANGHEIMCITY.scr:131

        if currentGroup == state.Group1 then -- MM_DRANGHEIMCITY.scr:133
            npcId = state.aGroup1:get(index) -- MM_DRANGHEIMCITY.scr:134
        elseif currentGroup == state.Group2 then -- MM_DRANGHEIMCITY.scr:137
            npcId = state.aGroup2:get(index) -- MM_DRANGHEIMCITY.scr:138
        elseif currentGroup == state.Group3 then -- MM_DRANGHEIMCITY.scr:141
            npcId = state.aGroup3:get(index) -- MM_DRANGHEIMCITY.scr:142
        elseif currentGroup == state.Group4 then -- MM_DRANGHEIMCITY.scr:145
            npcId = state.aGroup4:get(index) -- MM_DRANGHEIMCITY.scr:146
        end

        if npcId ~= 0 then -- MM_DRANGHEIMCITY.scr:149
            state.npc_id = npcId
            mm9.gosub(script, ctx, "CreateMarker") -- MM_DRANGHEIMCITY.scr:150
            mm9.gosub(script, ctx, "GoToLocation") -- MM_DRANGHEIMCITY.scr:151
        end
    end

    return ctx:exit() -- MM_DRANGHEIMCITY.scr:157
end
```

Current generated object movement:

```lua
script.labels["GoToLocation"] = function(ctx)
    ctx:getObjectHandleByRudeId("npc_id", "npc_object") -- MM_DRANGHEIMCITY.scr:109
    ctx:command("setstat", "npc_object, PARAM, goto_marker") -- MM_DRANGHEIMCITY.scr:111
    if ctx:condition("bWarp == FALSE") then -- MM_DRANGHEIMCITY.scr:113
        ctx:trigger("npc_object", "GoToLoc") -- MM_DRANGHEIMCITY.scr:114
    end -- MM_DRANGHEIMCITY.scr:115
    if ctx:condition("bWarp == TRUE") then -- MM_DRANGHEIMCITY.scr:117
        ctx:trigger("npc_object", "WarpToLoc") -- MM_DRANGHEIMCITY.scr:118
    end -- MM_DRANGHEIMCITY.scr:119
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:121
end
```

Desired generated object movement:

```lua
script.labels["GoToLocation"] = function(ctx)
    local state = ctx:state()
    local npc = ctx:objectByRudeId(state.npc_id) -- MM_DRANGHEIMCITY.scr:109

    npc:setStat("PARAM", state.goto_marker) -- MM_DRANGHEIMCITY.scr:111
    if state.bWarp == false then -- MM_DRANGHEIMCITY.scr:113
        npc:trigger("GoToLoc") -- MM_DRANGHEIMCITY.scr:114
    else -- MM_DRANGHEIMCITY.scr:117
        npc:trigger("WarpToLoc") -- MM_DRANGHEIMCITY.scr:118
    end

    return ctx:exit() -- MM_DRANGHEIMCITY.scr:121
end
```

Current generated array setup:

```lua
script.labels["InitArrays"] = function(ctx)
    ctx:command("index", "= 0") -- MM_DRANGHEIMCITY.scr:484
    while ctx:condition("index < 10") do -- MM_DRANGHEIMCITY.scr:485
        ctx:command("arrayput", "aGroup1, index , 0") -- MM_DRANGHEIMCITY.scr:486
        ctx:command("arrayput", "aGroup2, index , 0") -- MM_DRANGHEIMCITY.scr:487
        ctx:command("arrayput", "aGroup3, index , 0") -- MM_DRANGHEIMCITY.scr:488
        ctx:command("arrayput", "aGroup4, index , 0") -- MM_DRANGHEIMCITY.scr:489
        ctx:command("index", "= index + 1") -- MM_DRANGHEIMCITY.scr:490
    end -- MM_DRANGHEIMCITY.scr:491
    do return ctx:exit("") end -- MM_DRANGHEIMCITY.scr:493
end
```

Desired generated array setup:

```lua
script.labels["InitArrays"] = function(ctx)
    local state = ctx:state()

    for index = 0, 9 do -- MM_DRANGHEIMCITY.scr:484-485
        state.aGroup1:set(index, 0) -- MM_DRANGHEIMCITY.scr:486
        state.aGroup2:set(index, 0) -- MM_DRANGHEIMCITY.scr:487
        state.aGroup3:set(index, 0) -- MM_DRANGHEIMCITY.scr:488
        state.aGroup4:set(index, 0) -- MM_DRANGHEIMCITY.scr:489
    end

    return ctx:exit() -- MM_DRANGHEIMCITY.scr:493
end
```

The repeated `GroupN_GoWork`, `GroupN_WarpWork`, `GroupN_GoHome`, and related labels should keep their original labels,
because schedules and callbacks refer to those names. Internally they can still be made clearer:

```lua
script.labels["Group1_GoWork"] = function(ctx)
    setGroupDestination(ctx, ctx:state().Group1, ctx:state().Work, false)
    return ctx:exit()
end
```

The helper can be generated in the same file only if it preserves label-level source mapping and does not hide behavior
from diagnostics. If that is too opaque, keep the explicit assignments:

```lua
state.bWarp = false
state.current_group = state.Group1
state.goto_location = state.Work
mm9.gosub(script, ctx, "LaunchGroup")
```

Notes:

- Arrays should use zero-based wrappers until MM9 array indexing is fully verified.
- `npc_id`, `goto_marker`, `current_group`, and `bWarp` are shared script state, not local-only values.
- `index` can be local because it is only a loop counter.
- `@m` schedule commands should become `ctx:scheduleMinute(...)` or equivalent runtime scheduler calls.
- `GetObjectHandleByRudeId` should return an object proxy when the generated Lua needs object methods.
- Repeated label families can be made readable, but their public label names must remain stable.

### Common Actor And NPC Examples

Common actor and NPC scripts should become readable without turning Lua into a full engine. Lua should keep the authored
policy, branching, random choices, and label/callback wiring. C++ should still own AI queries, pathing, animation,
combat hit resolution, projectile spawning, reachability, target search, and movement callbacks.

#### `DRAGON.lua`

`DRAGON.scr` is a heavy actor AI script. It is a good target for proving that complex combat policy can be generated as
normal Lua while the expensive behavior stays in engine services.

Current generated attack selection:

```lua
script.labels["DoAttack"] = function(ctx)
    if ctx:condition("g_hTarget==NULL") then -- DRAGON.scr:262
        ctx:command("setidle", "") -- DRAGON.scr:263
        do return ctx:exit("") end -- DRAGON.scr:264
    end
    ctx:command("aigetdistance", "g_hTarget, g_nTemp") -- DRAGON.scr:267
    ctx:command("faceobject", "g_hTarget, 180, AttackFaceTargetDone") -- DRAGON.scr:269
    ctx:command("battacking", "= TRUE") -- DRAGON.scr:271
    if ctx:condition("g_nTemp < WING_ATTACK_DIST") then -- DRAGON.scr:273
        mm9.gosub(script, ctx, "DoCloseAttack") -- DRAGON.scr:274
    else
        ctx:command("canrangeattack", "g_bTemp") -- DRAGON.scr:276
        if ctx:condition("g_bTemp==FALSE") then -- DRAGON.scr:277
            do return mm9.gotoLabel(script, ctx, "CantAttackRightNow") end -- DRAGON.scr:278
        end
        if ctx:condition("g_nTemp < BREATH_ATTACK_DIST") then -- DRAGON.scr:284
            mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGON.scr:285
        else
            mm9.gosub(script, ctx, "DoFireBoltAttack") -- DRAGON.scr:288
        end
    end
    do return ctx:exit("") end -- DRAGON.scr:298
end
```

Desired generated attack selection:

```lua
script.labels["DoAttack"] = function(ctx)
    local state = ctx:state()
    local dragon = state.g_hMyObject or ctx:self()
    local target = state.g_hTarget

    if target == nil then -- DRAGON.scr:262
        dragon:setIdle() -- DRAGON.scr:263
        return ctx:exit() -- DRAGON.scr:264
    end

    local distance = dragon:aiDistanceTo(target) -- DRAGON.scr:267
    dragon:faceObject(target, 180, "AttackFaceTargetDone") -- DRAGON.scr:269
    state.bAttacking = true -- DRAGON.scr:271

    if distance < state.WING_ATTACK_DIST then -- DRAGON.scr:273
        mm9.gosub(script, ctx, "DoCloseAttack") -- DRAGON.scr:274
    elseif not dragon:canRangeAttack(target) then -- DRAGON.scr:276-277
        return mm9.gotoLabel(script, ctx, "CantAttackRightNow") -- DRAGON.scr:278
    elseif distance < state.BREATH_ATTACK_DIST then -- DRAGON.scr:284
        mm9.gosub(script, ctx, "DoBreathAttack") -- DRAGON.scr:285
    elseif distance < state.MAX_ATTACK_DIST then -- DRAGON.scr:287
        mm9.gosub(script, ctx, "DoFireBoltAttack") -- DRAGON.scr:288
    else
        dragon:setIdle() -- DRAGON.scr:291
        state.bAttacking = false -- DRAGON.scr:292
        mm9.gosub(script, ctx, "SetupAttack") -- DRAGON.scr:293
    end

    return ctx:exit() -- DRAGON.scr:298
end
```

Desired generated startup:

```lua
script.labels["Main"] = function(ctx)
    local state = ctx:state()
    local dragon = ctx:self()

    dragon:addEnemyClass("AIBase") -- DRAGON.scr:1158
    state.g_hMyObject = dragon -- DRAGON.scr:1160

    if ctx:paramBool(0) == false then -- DRAGON.scr:1162-1164
        mm9.gosub(script, ctx, "NormalSetup") -- DRAGON.scr:1165
    else
        mm9.gosub(script, ctx, "HideSetup") -- DRAGON.scr:1167
    end

    ctx:addTrigger("SpawnMutants", "SpawnMutants") -- DRAGON.scr:1170
    dragon:addModelKey("Growl1", "OnGrowl1") -- DRAGON.scr:1171
    dragon:addModelKey("Growl2", "OnGrowl2") -- DRAGON.scr:1172
    dragon:addModelKey("HitFloor", "OnHitFloor") -- DRAGON.scr:1173
    dragon:onCacheFiles("CacheFiles") -- DRAGON.scr:1174
    mm9.gosub(script, ctx, "CacheFiles") -- DRAGON.scr:1176
    dragon:onDeath("OnDeath") -- DRAGON.scr:1178
    return ctx:exit() -- DRAGON.scr:1180
end
```

Notes:

- Target selection arrays in `FindTarget` / `ArrayFind` should use zero-based array wrappers until indexing is verified.
- `FindTargets`, `AIGetDistance`, `CanAttack`, `CanRangeAttack`, `FaceObject`, `Attack`, and `RangeAttack` stay C++
  services and return typed Lua values.
- Persistent combat state such as `g_hTarget`, `g_hMyObject`, `bAttacking`, and timers must live in `ctx:state()`.
- Height and vector helpers can become typed math values, but LOS and reachability should remain world services.

#### `CAT.lua`

`CAT.scr` is smaller, but it is a useful callback-driven NPC behavior example: wander, follow a target, sit, react to
dogs/projectiles, and resume wandering after scheduled waits.

Current generated target acquisition:

```lua
script.labels["FoundTarget"] = function(ctx)
    if ctx:condition("g_hTarget!=NULL") then -- CAT.scr:101
        do return ctx:exit("") end -- CAT.scr:102
    end
    if ctx:condition("g_bRunning==TRUE") then -- CAT.scr:105
        do return ctx:exit("") end -- CAT.scr:106
    end
    ctx:getParam(0, "g_hTarget") -- CAT.scr:109
    ctx:command("target", "g_hTarget, FALSE") -- CAT.scr:110
    mm9.gosub(script, ctx, "DisableWandering") -- CAT.scr:112
    ctx:command("walkto", "g_hTarget, 0, OnHangoutArrival") -- CAT.scr:114
    do return ctx:exit("") end -- CAT.scr:115
end
```

Desired generated target acquisition:

```lua
script.labels["FoundTarget"] = function(ctx)
    local state = ctx:state()
    local cat = ctx:self()

    if state.g_hTarget ~= nil then -- CAT.scr:101
        return ctx:exit() -- CAT.scr:102
    end
    if state.g_bRunning == true then -- CAT.scr:105
        return ctx:exit() -- CAT.scr:106
    end

    state.g_hTarget = ctx:paramObject(0) -- CAT.scr:109
    cat:target(state.g_hTarget, false) -- CAT.scr:110
    mm9.gosub(script, ctx, "DisableWandering") -- CAT.scr:112
    cat:walkTo(state.g_hTarget, 0, "OnHangoutArrival") -- CAT.scr:114

    return ctx:exit() -- CAT.scr:115
end
```

Desired generated hangout callbacks:

```lua
script.labels["DoneHangingOut"] = function(ctx)
    local state = ctx:state()
    local cat = ctx:self()

    ctx:cancelWait("HANGOUT_WAIT") -- CAT.scr:75
    ctx:cancelWait("SITTING_WAIT") -- CAT.scr:76
    cat:onTargetBeyondDist(0, "DoNothing") -- CAT.scr:77

    state.g_bSitting = false -- CAT.scr:79
    state.g_hTarget = nil -- CAT.scr:80
    cat:clearTarget() -- CAT.scr:81
    cat:stop() -- CAT.scr:82

    mm9.gosub(script, ctx, "BaseWanderStart") -- CAT.scr:84
    cat:onFoundTarget("DoNothing") -- CAT.scr:86
    ctx:wait("HANGOUT_WAIT", ctx:randomInt(10, 20), "LookForPerson") -- CAT.scr:88-90

    return ctx:exit() -- CAT.scr:92
end

script.labels["OnHangoutArrival"] = function(ctx)
    local state = ctx:state()
    local cat = ctx:self()

    ctx:wait("HANGOUT_WAIT", ctx:randomFloat(8, 15), "DoneHangingOut") -- CAT.scr:152-154
    cat:stop() -- CAT.scr:155
    cat:onTargetBeyondDist(120, "GoAfterHim") -- CAT.scr:157
    state.g_bSitting = true -- CAT.scr:158
    mm9.gosub(script, ctx, "HaveASeat") -- CAT.scr:159
    state.g_hTarget:trigger("LookAtMe") -- CAT.scr:160

    return ctx:exit(true) -- CAT.scr:162
end
```

Notes:

- `baseWander.inc` and `baseRun.inc` can be generated into shared include modules, but label names must remain stable.
- The overloaded `BaseRunCancel` label in `CAT.scr` must keep its authored label behavior and source mapping.
- `OnProjectile` should use `ctx:paramObject(1)` for the incoming object handle, then reuse the same `RunAway` policy.
- Wandering, running, obstacle, stuck, and target-distance callbacks remain engine services on the active object proxy.

#### `NPC180.lua`

`NPC180.scr` is representative of quest NPC scripts: mostly state flags, key checks, rewards, sounds, and RUDE/dialogue
callbacks. It should be very close to normal Lua.

Current generated vanish logic:

```lua
script.labels["Vanish"] = function(ctx)
    ctx:command("getmyhandle", "g_hobject") -- NPC180.scr:61
    if ctx:condition("bVanish==TRUE") then -- NPC180.scr:63
        ctx:command("clearflag", "g_hobject, visible") -- NPC180.scr:64
        ctx:command("clearflag", "g_hobject, solid") -- NPC180.scr:65
        ctx:command("clearflag", "g_hobject, gravity") -- NPC180.scr:66
        do return ctx:exit("") end -- NPC180.scr:67
    else
        ctx:command("setflag", "g_hobject, visible") -- NPC180.scr:69
        ctx:command("setflag", "g_hobject, solid") -- NPC180.scr:70
        ctx:command("setflag", "g_hobject, gravity") -- NPC180.scr:71
        do return ctx:exit("") end -- NPC180.scr:72
    end
end
```

Desired generated vanish logic:

```lua
script.labels["Vanish"] = function(ctx)
    local state = ctx:state()
    local npc = ctx:self() -- NPC180.scr:61
    local enabled = not state.bVanish -- NPC180.scr:63

    npc:setFlag("visible", enabled) -- NPC180.scr:64,69
    npc:setFlag("solid", enabled) -- NPC180.scr:65,70
    npc:setFlag("gravity", enabled) -- NPC180.scr:66,71

    return ctx:exit() -- NPC180.scr:67,72
end
```

Current generated quest reward logic:

```lua
script.labels["Yanmir"] = function(ctx)
    ctx:hasKey(172, "keycheck") -- NPC180.scr:94
    if ctx:condition("keycheck==0") then -- NPC180.scr:95
        if ctx:hasKey(70) then -- NPC180.scr:97-98
            ctx:giveKey(172) -- NPC180.scr:100
            ctx:giveExp(58000) -- NPC180.scr:101
            ctx:giveGold(10000) -- NPC180.scr:102
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100")
            do return ctx:exit("") end -- NPC180.scr:106
        end
    end
    do return ctx:exit("") end -- NPC180.scr:110
end
```

Desired generated quest reward logic:

```lua
script.labels["Yanmir"] = function(ctx)
    if not ctx:hasKey(172) and ctx:hasKey(70) then -- NPC180.scr:94-98
        ctx:giveKey(172) -- NPC180.scr:100
        ctx:giveExp(58000) -- NPC180.scr:101
        ctx:giveGold(10000) -- NPC180.scr:102
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, false, 100) -- NPC180.scr:103
        return ctx:exit() -- NPC180.scr:106
    end

    return ctx:exit() -- NPC180.scr:110
end

script.labels["Breakice"] = function(ctx)
    if not ctx:hasKey(175) and ctx:hasKey(73) then -- NPC180.scr:127-131
        ctx:giveKey(175) -- NPC180.scr:133
        ctx:giveExp(30000) -- NPC180.scr:134
        ctx:giveGold(3000) -- NPC180.scr:135
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, false, 100) -- NPC180.scr:136
        return ctx:exit() -- NPC180.scr:139
    end

    return ctx:exit() -- NPC180.scr:143
end
```

Desired generated startup:

```lua
script.labels["Main"] = function(ctx)
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC180.scr:178
    ctx:addTrigger("Use", "OnUse") -- NPC180.scr:179
    ctx:state().Jarl = "Tryygva" -- NPC180.scr:180
    mm9.gosub(script, ctx, "UnitedInit") -- NPC180.scr:181
    mm9.gosub(script, ctx, "Init") -- NPC180.scr:182
    return ctx:exit() -- NPC180.scr:183
end
```

Notes:

- Key checks should become predicates when the result is used immediately and not needed as a named script variable.
- `bVanish` must remain script state because `Init` assigns it before calling `Vanish`.
- `OnUse`, `OnRude`, `UnitedInit`, and `United` still need runtime/dialogue services, but their control flow should be
  visible in Lua.
- Quest reward scripts are a good regression target for proving no comments or source line references are lost.

## Object Handle Collapse

The source often contains temporary handle boilerplate:

```scr
GetObjectHandle Terrain3 g_hObject
Trigger g_hObject open
Trigger g_hObject sinkspeed
```

Preferred generated Lua:

```lua
local terrain3 = ctx:object("Terrain3")
terrain3:trigger("open")
terrain3:trigger("sinkspeed")
```

Single-use form:

```lua
ctx:object("Terrain3"):trigger("open")
```

Safe substitution rules:

- map `tempHandle -> objectName` only after `GetObjectHandle objectName tempHandle`;
- substitute later uses only in commands whose parameter is known to be an object handle;
- keep the original temporary if the script tests it against `NULL`;
- invalidate the mapping when the temp handle is assigned by any other command;
- invalidate on label boundaries, `wait`, callback registration that may resume later, `goto`, and unknown control flow;
- do not collapse dynamic values from `GetParam`, `ArrayGet`, `GetTarget`, `AttachProp`, `Spawn`, or arbitrary
  assignment;
- dynamic object-name variables may be collapsed only to `ctx:object(variableName)`, not to a string literal.

Examples:

```scr
GetObjectHandle Camera2 g_hObject
Trigger g_hObject On
Trigger g_hObject Play
```

```lua
local camera2 = ctx:object("Camera2")
camera2:trigger("On")
camera2:trigger("Play")
```

Unsafe:

```scr
GetObjectHandle Target g_hObject
if (g_hObject != NULL)
    Trigger g_hObject message
endif
```

Should become:

```lua
local target = ctx:objectOrNil("Target")
if target ~= nil then
    target:trigger("message")
end
```

not a blind collapse that loses the null check.

## Condition Translation

Current form:

```lua
if ctx:condition("g_ntemp==TRUE") then
```

Target form:

```lua
if g_ntemp == true then
```

or when generated from a predicate:

```lua
if ctx:hasKey(108) then
```

Translation should cover:

- `==`, `!=`, `<`, `<=`, `>`, `>=`;
- `TRUE`, `FALSE`, `NULL`;
- basic arithmetic expressions;
- variable references;
- handle equality comparisons;
- parentheses.

Unknown or ambiguous expressions can remain behind `ctx:condition(...)` until supported.

## State And Save/Load

Native Lua locals are safe only inside a single label invocation. Values that must survive across callbacks, waits, map
events, or save/load need a runtime-backed state domain.

Exporter rule of thumb:

- local loop counters and scratch temporaries can be generated as Lua locals when their lifetime is fully contained;
- globals declared in includes should resolve through generated script state accessors unless proven localizable;
- object handles used across callbacks must be stored in runtime state, not only Lua locals;
- object proxies stored in runtime state must serialize as stable handles and rehydrate through the object registry;
- scheduled callbacks should restore the same script owner, active object, parameters, and relevant variable state that
  LithTech scripts expect.

## Implementation Phases

### Phase 1: Runtime Correctness

- Fix handle resolution so assigned `g_hObject` / `g_hobject` variables win over active-object aliases.
- Add object proxy API with `ctx:object`, `ctx:self`, `ctx:paramObject`, and `object:trigger`.
- Keep `ctx:command` fallback for unsupported commands.
- Add unit tests for `GetObjectHandle Terrain3 g_hObject; Trigger g_hObject open` dispatching the Terrain3 target.

### Phase 2: Narrow Object Collapse

- Add exporter peephole for immediate `GetObjectHandle X temp` followed by one or more safe object-handle commands.
- Emit `local objectName = ctx:object("X")` when there are multiple safe uses.
- Emit direct `ctx:object("X"):method(...)` for single-use cases.
- Preserve source line comments on the generated method call.

### Phase 3: Native Expressions

- Translate `set`, bare assignment, `add`, `sub`, `mul`, and simple conditions into Lua.
- Keep a fallback path for expressions the parser cannot prove.
- Add golden tests for representative AI and event scripts, including `MM_GUBERLANDCITY.scr:LaunchGroup`.

### Phase 4: Arrays

- Implement zero-based MM9 array wrappers.
- Translate `arrayget` and `arrayput` to wrapper calls.
- Validate all generated Lua compiles and package checks remain idempotent.

### Phase 5: Broader Object Methods

- Add object proxy methods for movement, flags, stats, animation, attack, reachability, and position.
- Convert known commands from `ctx:command` to object method calls when signatures are understood.
- Keep command inventory updated with implemented, translated, and fallback commands.

## Testing Requirements

Every phase needs focused unit tests before regenerating all Lua:

- generator tests for exact readable output snippets;
- runtime tests for object lookup, handle variable resolution, trigger dispatch, and source line diagnostics;
- idempotency test for the full MM9 dialogue pipeline;
- generated Lua compile test for every script and include;
- package loader tests that verify the common runtime support file is present;
- smoke tests for representative scripted map objects once DAT world runtime hooks are available.

Use the original source scripts as fixtures. Do not edit generated Lua to make tests pass.

## Non-Goals

- Do not hand-author replacement AI in C++.
- Do not lose source script line mapping.
- Do not rewrite all commands in one pass.
- Do not treat every `g_*` variable as local; many are global script state by design.
- Do not replace runtime world services with Lua implementations of physics, pathing, combat, or animation.

The intended end state is still MM9-authored behavior: Lua remains the generated policy layer, while OpenYAMM provides a
faithful MM9/LithTech-like service layer underneath it.
