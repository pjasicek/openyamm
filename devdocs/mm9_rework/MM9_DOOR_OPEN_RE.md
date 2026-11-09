# MM9 door opening: use, touch and monsters (reverse engineering)

This note covers when a Might and Magic IX door opens: when the player uses it, and when the player or a monster walks into it.
It also covers what the DAT door keys `PushOpen`, `TouchToOpen`, `ReopenOnContact`, `OpenAway`, `Locked`, `AITriggerable`
and `AutoTrigger` do. The findings come from the shipped binaries. Research date 2026-11-04, using `objdump -M intel`
listings (the full listings from the [slope RE](MM9_PLAYER_SLOPE_RE.md) in `re_mm8/work/mm9_slope/`) and Python
vtable, class-definition and DAT scans. Scratch files are in `re_mm8/work/mm9_doors/`, which git ignores. The method and
conventions follow the [monster collision RE](MM9_MONSTER_COLLISION_RE.md). The LithTech headers in `mm9/lithtech/`
(Blood2 `AppHeaders`, Jupiter `runtime/`) were used only to read flag values, message IDs and the engine's
touch-notify logic.

| Binary (`mm9/game/`) | SHA-256 | Role |
| --- | --- | --- |
| `data/object.lto` | `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162` | Server game code: the `Door`/`RotatingDoor` classes, the player's server object and the AI |
| `data/cshell.dll` | `678700ff1cc795aeee49fe8427a42e1686d5a20dfdc1617eb46a8ef19f82f7ae` | Client: input commands and messages to the server |
| `lithtech.exe` | `4e9ddd2b69db934ecbd7399dd92992004e596907da4a214450f31c5dd39e56d8` | Engine: the server interface and the collision touch notification |

## Answer

**When the player walks into an ordinary MM9 door, the door does not open.** This is the typical city door:
`PushOpen` 1, `TouchToOpen` 0, unlocked, for example the 61 free doors of `STURMFORDCITY`. The player opens it only
with the **Use** command (Space, `AddAction Use 68`) or **AttackUse** (command 143) when no NPC or monster is in front.
Both commands send a `"USE"` message to the object the player is looking at, within 180 LT. The collision does reach
the door: every door gets a touch notification with a force limit of 1. The door's touch handler, however, opens it
only when `TouchToOpen` is set. Neither the client nor the server player turns a bump into a use.

**Monsters do open doors by walking into them.** The standard AI script (`BASEDOOR.inc`, included from `BASE.inc`) stops
the creature, turns it to face the door and sends the door `"Use"`. This needs `AITriggerable` 1, an unlocked door and
`PushOpen` 1. The AI must also be walking, running or flying and heading within 45° of the door.

### 1. `PushOpen` and `TouchToOpen`

- **`PushOpen`** (byte `+0x494`, default 1) means "the door is worked with **USE**", by the player or by a trigger
  or script that sends `use`. It has two effects:
  - **USE** works only on `PushOpen` doors. It toggles the door: a closed or closing door opens, and an open or
    opening door closes. On a `RotatingDoor` with `OpenAway`, the door swings away from the user. With
    `PushOpen` 0, USE does nothing: `Door` returns "not handled" and `RotatingDoor` swallows it.
  - **OPEN, and TOGGLE when it would open, are ignored by a closed or closing `PushOpen` door.** OPEN works only on
    `PushOpen` 0 doors, such as event-driven gates and the auto-trigger volume. The data agrees: 1,348 of the 1,401
    `PushOpen` Door/RotatingDoor objects are the target of no message. Designers wire `PushOpen` doors with `use`
    (31 links) or `unlock`. They wire `open` and `toggle` almost only to `PushOpen` 0 doors.
- **`TouchToOpen`** (byte `+0x495`, default 0) means the door **opens when touched by any object that has
  `FLAG_SOLID`**: the player, a monster, an NPC or a solid prop. A non-sticky door starts opening unless it is already
  opening. A `Sticky` door toggles: closed opens and open closes. The touch goes through `StartOpening`, so a locked
  door only jiggles. `PushOpen` does not affect this path. In the data, 7 Door/RotatingDoor objects have it: the
  2 `LICHLAB` `peasant door`s (`PushOpen` 0), 3 `Door`s with `PushOpen` 0 such as `DUNGEONOFSECRETS`
  `doubleaxe upper trigger`, and 2 `Door`s with `PushOpen` 1 such as `BATHHOUSE` `Door4`. All 14 `WeightedLift`s
  have it too.

The difference: `TouchToOpen` is the only flag that makes contact open a door. `PushOpen` makes a door open on USE and
blocks OPEN while it is closed. It never makes contact open the door.

### 2. A player walking into a typical city door

The collision reaches the door, but nothing opens it:

1. The client moves the player and sends position updates (message 0). The server player object (`Player`)
   copies the client velocity with SetVelocity, then calls **MoveObject** toward the client position. If the
   result is more than 120 LT off, it teleports instead (`0x100c3820`). MoveObject runs the engine collision.
2. Every door is created with `FLAG_TOUCH_NOTIFY`. The door's PostPropRead ORs `0xa10100` into the creation flags
   after the generic property reader. That reader has just cleared the bit, because every DAT door has `TouchNotify` 0.
   Door init then sets the force-ignore limit to **1.0** (the engine default is 1000). The engine's solid
   collision notifies each object that has the flag when the force reaches its limit (`lithtech.exe` `0x416428…0x416486`).
3. `Door::TouchNotify` (`0x100698e0`) with `TouchToOpen` 0 only runs the `ReopenOnContact` check (item 3), then
   passes the touch to the base handler. The base handler only notifies an attached script, and city doors have no
   `ScriptName`. The player's own TouchNotify (`0x100c3100`) does only the same base script hook.
4. The client sends the activate messages (0x05 and 0x88) only from the Use and AttackUse command handlers. No movement
   or collision code sends them, and nothing raises Use automatically.

### 3. Locked doors, `ReopenOnContact`, `OpenAway` and monsters

- **`Locked`** (byte `+0x497`): `StartOpening` (`0x10067d80`, vtable `+0x270`) checks it first. A locked door
  plays the lock jiggle instead (`+0x278`, `0x1006abd0`): state 4, `JiggleSound` or `sounds\door\locked_door02.wav`,
  at most once every 3 s. This applies to every path: USE, OPEN, TouchToOpen and ReopenOnContact. `StartClosing`
  also refuses while locked. The `LOCK` and `UNLOCK` messages set and clear the byte and are passed on to the double
  door. AI scripts never try a locked door, because the C++ AI checks `IsLocked` before it raises `OnDoor`.
- **`ReopenOnContact`** (byte `+0x498`, default 1): in `TouchNotify` with `TouchToOpen` 0, a door that is **closing**
  reverses and reopens when touched by an `Actor`. The player and every monster or NPC are Actors. The Actor must
  not be dead or dying, and must have `FLAG_SOLID` and `FLAG_VISIBLE`. This is the "blocked door reverses" behaviour.
  It never opens a closed door. A locked closing door jiggles instead of reopening. Lifts skip it when the Actor is
  standing on top (`+0x238`).
- **`OpenAway`** (`RotatingDoor` byte `+0x5e6`): only when a closed door opens from USE, or from OPEN with a sender.
  `0x1006a750` compares the user's position with the door's thin axis and its `RotationPoint`. If the door would
  swing toward the user, it negates `RotationAngles`, so the door always swings away from whoever opened it.
  Touch-opening does not use it.
- **`AITriggerable`** (dword `+0x57c`, getter `+0x248`): the AI checks it in its touch handler (`0x10012b8d…`) and in
  its obstacle probe while moving (`0x10013e81…`). When the AI hits an object that is a `Door`, the door is
  `AITriggerable` and **not locked**, and the AI can open doors (`+0x540`), the AI raises script event `0x19`
  (`OnDoor`) with the door handle and contact normal (`0x1001a440`). `BASEDOOR.inc` `BD_OnDoor` ignores the door if
  it is not closed. It also ignores it if the AI is not walking, running or flying, or if the AI faces more than 45°
  away from the door. Otherwise it stops the AI, faces the door and runs `Trigger g_hDoor,Use`. It then waits
  `DoorOpenTime` and resumes its path. Because the message is USE, monsters open only `PushOpen` doors. The same
  `AITriggerable` value is copied to the volume that `AutoTrigger` creates.
- **`AutoTrigger`** (`+0x493`, 3 doors): at init (`0x100679f0`), the door creates a `Trigger` volume of
  `TriggerDims`. With dims 0, it uses the door's dims with the thin axis set to 72. The volume sends **OPEN**, which
  a closed `PushOpen` door ignores.
- MM9 doors have no `PlayerActivate`-style key. `Triggers` and `Options` are 0 on every door and are never tested.
  `Sticky` makes USE, OPEN and touch toggle the door and stops the auto-close.

## Evidence

### Door fields and init (`object.lto`)

Classes come from the class definitions in `.data`. `Door` is at `0x101a3628` (ctor `0x10065cf0`, vtable `0x1017329c`).
`RotatingDoor` is at `0x101a3658` (vtable `0x10173524`). `Button`, `Lift`, `WeightedLift` and `Switch` derive from them.
Door state is `+0x48c`: 0 Open, 1 Opening, 2 Closing, 3 Closed, 4 Jiggling. This comes from the `IsOpen`/`IsOpening`/
`IsClosed`/`IsClosing` getters at `0x10067210`.

| Address | What it does |
| --- | --- |
| `0x1006559b`, `0x1006562b`, `0x100657da` | Static property table: `PushOpen` default 1.0, `TouchToOpen` 0, `ReopenOnContact` 1.0, `Locked` 0 |
| `0x100675e1…0x100677ab` | Door ReadProp: `Sticky +0x490`, `StartOpen +0x491`, `Looping +0x492`, `AutoTrigger +0x493`, `PushOpen +0x494`, `TouchToOpen +0x495`, `Locked +0x497`, `ReopenOnContact +0x498`, `TriggerDims +0x530`, `AITriggerable +0x57c`; `OpenAway` → `+0x5e6` in RotatingDoor ReadProp `0x1006a033` |
| `0x10068650` (vtable `+0x178`, PreCreate from world file) | `0x100bed00` → base `0x100bcab0` → `0x100d39c0` (generic props: `TouchNotify` 0 clears `0x10000` at `0x100d3c20`), then ReadProp, then `0x10067940` |
| `0x10067976…0x10067984` | `flags |= 0xa10100` (FULLPOSITIONRES, **TOUCH_NOTIFY**, GOTHRUWORLD, DONTFOLLOWSTANDING), plus BOXPHYSICS |
| `0x10068951` | Door init: `SetForceIgnoreLimit(1.0)` (`0x100bcfe0` → server `+0x130`) |
| `0x10068973` / `0x10068987` | Init: AutoTrigger → `+0x27c` (`0x100679f0`); TouchToOpen → ORs `0x10000` again (redundant) |

### Messages and handlers

| Address | What it does |
| --- | --- |
| `0x100bd9f0` | Trigger-message dispatcher (string compare): `OPEN` → `+0x1c8`, `CLOSE` → `+0x1cc`, `TRIGGER` → `+0x1e8`, `USE` → `+0x1e4`, `LOCK` → `+0x204`, `UNLOCK` → `+0x208`, `TOGGLE` → `+0x1d0`. Door entry `0x10069b80` adds `JIGGLE`. |
| `0x10068c10` (Door USE) | `if (!PushOpen) return false;` Open/Opening → StartClosing `+0x274`; Closing/Closed → StartOpening `+0x270`; forwards to `DoubleDoorName` |
| `0x1006a920` (RotatingDoor USE) | `if (!PushOpen) return true;` Open/Opening → close; Closing/Closed → `OpenAway ? +0x234(user) : +0x270`; double door |
| `0x10068a30` (Door OPEN) | `if (PushOpen && (state==Closed || state==Closing)) return false;` otherwise Open → Sticky ? close : re-hold open, Opening → Sticky ? close, Closing/Closed → StartOpening |
| `0x1006a9f0` (RotatingDoor OPEN) | Same PushOpen refusal; then OpenAway from the sender, or the Door OPEN |
| `0x10068ce0` (TOGGLE) | Closed/Closing → OPEN `+0x1c8`, else CLOSE |
| `0x10067d80` / `0x10068320` | StartOpening (Locked → jiggle `+0x278`; state 1, open sound, portal) / StartClosing (refuses when Locked; state 2) |

Excerpt of the `PushOpen` test in Door OPEN:

```
10068a33: mov al,BYTE PTR [esi+0x494]   ; PushOpen
10068a3b: je  0x10068a53
10068a3d: mov eax,DWORD PTR [esi+0x48c] ; state
10068a43: cmp eax,0x3 / je 0x10068a4d   ; Closed  -> return false
10068a48: cmp eax,0x2 / jne 0x10068a53  ; Closing -> return false
```

### Touch (`Door::TouchNotify` `0x100698e0`, vtable `+0x190` on every door class)

```
100698f7: mov al,BYTE PTR [esi+0x495]   ; TouchToOpen
1006990f: jne 0x100699e5
  ; TouchToOpen == 0:
  1006995f: vt+0x23c ReopenOnContact; !onTop; state==2 (Closing); IsKindOf(hObj,"Actor") (0x10005d70);
            !dead/dying (+0x25c/+0x260); flags & 0x2000 (SOLID); flags & 1 (VISIBLE)
  100699c2: mov DWORD PTR [esi+0x48c],0x3 ; then StartOpening (+0x270)
  100699d6: call 0x100c02c0               ; otherwise the base handler (script OnTouchNotify only)
  ; TouchToOpen == 1:
  100699ee: call [server+0x148]           ; GetObjectFlags(hObj)
  100699f4: test ah,0x20                  ; FLAG_SOLID, else base handler
  10069a10: Sticky ? (Closed→open, Open→close) : (state!=Opening → StartOpening); forward to double door
```

Server `+0x148`/`+0x14c` are GetObjectFlags/SetObjectFlags (OFT_Flags). User flags are the function pointers
`+0x184`/`+0x188`. The server interface vtable in `lithtech.exe` is `0x484284`. There, `+0x140` → `0x457bb8` =
`Physics()->MoveObject(h, pos, 0)`, `+0x148`/`+0x14c` → `0x457c2c`/`0x457c4f` = `Common()->Get/SetObjectFlags(h, 0)`,
and `+0x130` → physics `+0xc` SetForceIgnoreLimit (`0x42f247`, which writes the squared limit to `+0xe4`).
The user-flag accessors are installed at `0x458cbd` (`+0x184` = `0x45a22a`, `+0x188` = `0x45a23a`). The object
default `+0xe4 = 1e6` (a limit of 1000) is set at `0x44af57`.

### Player use (client and server)

| Address | What it does |
| --- | --- |
| cshell `0x100aaa90` | OnCommandOn (vtable `0x100c9a68`): command 68 (`Use`) → `0x100aad90`; 143 (`AttackUse`) → `0x100aaea0` |
| cshell `0x100aad90` / `0x100aaea0` | Send message 0x05 / 0x88 with the camera forward vector (`0x100ad040`, the only senders of these IDs) |
| object `0x100c3130` | `Player` client-message switch: 0x05 → `0x100c4020`, 0x88 → `0x100c4140`, 0x00 → update `0x100c3820` |
| object `0x100c4020` | If not dead: `0x100d77b0(this, pos, dir, 180.0, "USE", 0, 48.0)` |
| object `0x100c4140` | `0x100d7680` first: a live Actor (not an NPC) on the ray → attack; otherwise the same USE probe |
| object `0x100d77b0` | Segment of 180 LT; hit object that is an ObjectBase → send `USE`. Otherwise spheres of radius 48 along the segment, filtered by `0x100d7540` |
| object `0x100c39dd` → `0x100c3a65` | Update: SetVelocity (vtable `+0x18` → server `+0x168`), then MoveObject (`+0x140`) when more than 4 LT off; TeleportObject (`+0x28` → `+0x1b0`) when the result is more than 120 LT off |

### Monsters

| Address / file | What it does |
| --- | --- |
| object `0x10012b8d…0x10012c08` | AI TouchNotify: solid toucher → IsKindOf Door (`0x1006abb0`) → `door+0x248` AITriggerable → `ai+0x540` can open doors → `!door+0x24c` (`0x10066450`, IsLocked) → `ai+0x6c0` |
| object `0x10013e81…0x10013edf` | The same chain from the AI movement obstacle probe |
| object `0x1001a440` | `ai+0x6c0`: formats `"%d %.2f, %.2f, %.2f"` (door handle and normal) and raises script event `0x19` |
| object `0x10098e34…0x10098e66` | Script command `OnDoor` registers the handler for event `0x19` |
| `mm9/extracted/SCRIPTS/SCRIPTS/BASEDOOR.inc` | `g_sOpenString=Use`; `BD_OnDoor`: door closed, AI walking, running or flying, within 45° → `Stop`, `FaceDir`, `Trigger g_hDoor,g_sOpenString`, wait `DoorOpenTime`, resume. 24 scripts include it, among them `BASE.inc` (`gosub BaseDoorInit`). |

### DAT data

The scans are in `re_mm8/work/mm9_doors/`: `door_props.py`, `door_props2.py`, `msg_targets.py` and `city.py`.
They cover 1,834 door-family objects across all worlds.

- `TouchNotify` is 0 on all of them, `Triggers` and `Options` are 0, and `Solid` is 1 on 1,763.
- `AutoTrigger` is 1 on 3 objects.
- Door/RotatingDoor `TouchToOpen` is 1 on 7 objects.
- Door/RotatingDoor `PushOpen`: 1,401 are 1, and 1,348 of those are targeted by no message. Messages sent to doors
  are mostly `open`, `close`, `lock` and `unlock` to `PushOpen` 0 doors, and `use`, `unlock` and `close` to
  `PushOpen` 1 doors.
- City maps are almost all free `PushOpen` doors. `STURMFORDCITY` has 61 unlocked and 42 locked ones, plus
  `Jaildoor` (`PushOpen` 0).

## Confidence and open points

- **High:** what `PushOpen`, `TouchToOpen`, `ReopenOnContact`, `Locked` and `OpenAway` do, and the claim that player
  contact never opens a `TouchToOpen` 0 door. These are read directly from the handlers above. The message names and
  the vtable slots are tied together by the dispatcher.
- **High:** the player opens doors only through Use or AttackUse. Those are the only senders of client messages 0x05
  and 0x88, and no code path raises them from movement.
- **High:** monsters open unlocked `AITriggerable` `PushOpen` doors on contact through the AI script. The script text
  is shipped. That every creature's script includes `BaseDoor` was not checked creature by creature (24 scripts
  include it), and neither was the condition behind `ai+0x540` (`!ai+0x37c`).
- **Medium-high:** that the door receives the touch notification at all. This rests on the flag and force-limit
  setup above and on the engine's collision code. It was not checked in the running game. It matters only for
  `TouchToOpen` and `ReopenOnContact`. The main conclusion does not depend on it, because a `TouchToOpen` 0 door
  never opens on touch.
- Not traced: the `Trigger` class's own touch filters, so whether an `AutoTrigger` volume reacts to the player, AI or
  both. Its OPEN has no effect on a closed `PushOpen` door either way.

Consequences for the conversion: keep USE (click) for `PushOpen` doors. Doors with `TouchToOpen` 1 should open when
anything solid touches them, and closing doors with `ReopenOnContact` 1 should reverse when an actor blocks them.
Monsters should open unlocked `AITriggerable` `PushOpen` doors they walk into. Our docs' "`PushOpen` = opens on use"
(`devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md`, `level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md`) is
correct, with one addition: a closed `PushOpen` door ignores `open` and `toggle` messages.
