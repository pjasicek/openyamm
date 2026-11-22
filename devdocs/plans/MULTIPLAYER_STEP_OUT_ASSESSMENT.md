# Stepping out of a co-op session into your own game: assessment

An idea from the Discord server (2026-11-20): a guest who wants to go elsewhere, to a skill teacher for example, is
put back into its own world for the time, stays in the party greyed out, and reconnects by going back to the host's
map. This is an assessment from reading the code and the two planning documents
([the architecture](MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md), [the open items](MULTIPLAYER_OPEN_ITEMS.md)).
It is the open items' CO-144. The user asked for it on 2026-11-21, in the simpler of the two shapes below: the
connection ends and both games remember the seat. What was built is the next section; the rest of the document is
the assessment as it was written, kept for the questions it lists.

Function names are the reference; line numbers move.

## What was built (2026-11-21)

**For the player**

- **A guest's travel that waits for the others offers to go alone.** Any map travel a guest sets off (the map's
  edge, a door, a coach or boat, Town Portal) is its proposal to the others. While it waits, the guest's game shows
  "Waiting for the other players ..." with **Go Alone** and **Wait**. Go Alone takes the guest out of the session:
  its own game comes back and travels to where the proposal led, in the guest's own world, paying that trip's fare
  and time there.
- **Step Out for Now** on the Multiplayer screen does the same without a trip (the console's `coop stepout`).
- **The others see the player greyed, "away"** in the players panel and on the Multiplayer screen, and are told
  "{name} stepped out for now" and later "{name} is back".
- **Return to {name}'s Game** on the Multiplayer screen joins again the way the game had joined (`coop stepback`);
  Forget drops the memory. Any other join of that host takes the kept seat as well.
- The returning player is the player it was (the same number), stands beside the host as after a join, and brings
  what its character gained at home.

**How it works**

- **Two steps out.** The guest's game sends `Message::StepOut` with a key it made up; the host notes the key on the
  peer, drops what that player had proposed and answers `Message::SteppedOut`; the guest's game then leaves as
  `leave()` does (`CoopSession::guestFinishStepOut`). A last word sent while closing would be lost, so the seat is
  agreed before the connection ends.
- **The seat** is the host's `AwaySeat`: the key and what the others are shown of the player. It is made when that
  peer's connection ends (`hostDropPeer`) and lives as long as the hosting does, across the host's map changes; it
  is not saved.
- **The way back** is an ordinary join whose Hello names the key (`AwayFrom::seatKey`). The host gives the seat's
  player number (`GameSession::addGuestPlayer` with a wanted id; numbers kept for those away are not handed out).
- **A kept seat never keeps a present player out:** with the session full of present and away players, the longest
  away gives its seat up to a newcomer.
- **The guest's memory** (`CoopSession::awayFrom`) is how it joined (an address, or a lobby and code), the
  password and the key. It lasts until the game joins a session again, the player forgets it or the game closes.
- Protocol version 8 (the Hello's key, the players list's away flag, the two messages).
- Scenarios: `net_step_out.yml` (out by the console, seat kept, gains brought back, the same player number) and
  `net_step_out_travel.yml` (the edge, Go Alone, the own world's map, the host left where it was, back again).

**Not built, of what the assessment lists**

- The connection is not kept: no chat while away, and a host that ended its session is found out only on trying to
  return.
- No refusal while down or with monsters near, and no cooldown: stepping out is as free as leaving and joining.
- A character joined from a file cannot step out.
- The memory does not outlive the game's run, on either side.
- The host has no equivalent.

## Verdict

- **The mechanism holds and is mostly built.** "Step out" is today's leave without closing the connection, and
  "step back" is today's join without a new connection.
- **It does not work without awkwardness.** The errand happens in a different world, starting where the guest's solo
  game was left, and that world's progress decides which teacher is reachable.
- **It leaks single-player comforts into the session.** A stepped-out player can rest, pause, save and reload, then
  come back.
- **The host can never use it, and a guest who joined with a character file cannot use it** without extra work.
- **The return path was broken, and is mended.** A second join in the same run of the game left the guest's character
  standing still in both games (CO-141, closed on 2026-11-20).
- **The recommendation for the errand problem is a remote house visit in the host's world** (alternative A below).
  Step-out is worth building as a small separate feature, "take a break without losing your seat", not as the
  answer to errands.

## 1. How close leave, come-home and rejoin already are

| Step | Today | What step out and step back need |
| --- | --- | --- |
| Leaving | `CoopSession::leave` calls `guestReturnToOwnGame`. That puts the session's character into the kept own game (`m_guestOwnGame`) with the own game's quests, writes its Autosave, calls `close()`, loads the own game and returns own quest items to the bags | The same without `close()`: keep the transport and the guest role, add an away flag, and do by hand what `close()` does for the game (`setCoopSession(false)`, `setCoopRole(None)`, `playerCommands().setRemote(nullptr)`) |
| Host, on a leave | `hostDropPeer` calls `GameSession::removeGuestPlayer` and erases the `HostPeer` | Call `removeGuestPlayer` but keep the `HostPeer` with its player id, name and a cached panel entry |
| Joining | `join` and `joinOn` set the shared quest pouch first, so own quest items stay home. `guestSendHello` sends versions, name, character, content identity and password | Step back sends the same payload on the open connection. `hostHandleHello` ignores a Hello from an admitted peer, so it needs a new message or an "away" exception |
| Admission | `hostHandleHello` checks versions, content, password and `MaxGuests`, then calls `GameSession::addGuestPlayer`, which takes the lowest free id and places the body beside the host | Check the content again: the guest may have loaded a save of another ruleset while away. Reuse the reserved id, which `addGuestPlayer` cannot do today. Count away members in the limit |
| The world | `hostSendWorldState`, then `guestHandleWorldState`, which captures the own game when `m_guestOwnGame` is empty, loads the host's map as a replica and sends `MapReady` | Nothing. Step out empties `m_guestOwnGame`, so step back captures the own game afresh, including what the errand changed |

**Removing the guest record while away makes most of the host right for free.** These already skip a peer whose guest
record is missing:

- the silence notice and the map-load timeout in `updateHost`;
- `hostSendWorldState`, `hostSendPartyStates` and `hostSendOutcome`;
- `hostHandlePosition`, `hostHandleCommand` and `hostHandleCharacterPut`.

Votes, monster health, rewards and the defeat test all go over the guest players, so they behave as after a leave,
which is tested. The alternative, a flag on a kept guest record, needs about fifteen places patched (the travel and
rest votes, `anyPlayerCanAct`, `updateGuestPlayers`, `startAgreedRest`, fares, the defeat's payment). A missed one
means a rest vote that never passes or a defeat that never triggers.

**Still to mute by hand on the host:**

- `hostSendMapMessage` queues map news for a peer that is not ready, without limit.
- `sendToAll` keeps sending bodies twenty times a second, plus the campaign and the votes.

On the guest's side, `guestHandleMessage` already holds campaign, ruleset and vote news while the map is not loaded
(`m_guestHeldGameNews`). That is what protects the own game from the host's quests.

## 2. The hard questions

**Which world does the errand happen in?**

- The guest's own game, exactly as it was when it joined: its map, position, calendar, quests, shop stock and MAW
  state.
- **Reach is the real limit.** The guest stands wherever its solo game stopped. A character made for co-op has a fresh
  world at its start map. A teacher on another continent, or behind story progress, may be unreachable there.
- **Quest gates.** Promotions and awards travel with the character; quest bits do not. What of a character is tied to
  a world's quests was never gone through (CO-50).
- **Loot and gold.** A guest can loot its own world and bring it back. That is no new kind of exploit, since joining
  with a played character allows it today. It does become a loop inside one session, with pause, fast mode and save
  and reload available.
- **Rest.** A stepped-out player can rest in its own world and return at full health, which bypasses the rest vote.
  Refusing step-out while down or with hostile monsters near would limit it (`PlayerCommands::restRefusal` is that
  test).
- **Quest items and the shared pouch.** This works by existing code: own quest items go home, and the host's pouch
  stays the host's. The exception is quest items that are gear (CO-112), which leave with their holder.
- **MAW.** The level bank, map progress and difficulty are each world's own. The errand may run in an easier world
  with other shop levels. Auras, held food and deaths travel with the character.
- **Time.** The two calendars are unrelated. Buff times are relative and survive. Condition expiry and fixed-aura end
  times are absolute minutes, and they cross calendars at every hand-over. This already happens on leave; step-out
  multiplies it.
- **Saving and dying while out.** These are ordinary single-player events in the own game. Loading an older own save
  while out brings back an older character, which among friends is acceptable.

**Where does the guest come back to?**

- A button, not a walk. The host's map in the guest's own world is a different place and may not be reachable.
- It arrives on whatever map the host is on now, by the join path.
- At the map's arrival point (`GameSession::mapArrivalBody`), not beside the host as a join does. Otherwise step out
  and back is a free teleport to the host.

**What the others see, and who waits for whom**

- **Votes and monster health.** With the record removed, an away member has no vote and is not counted for monster
  health. Living monsters keep their share, so stepping out mid-fight gains nothing.
- **Rewards.** An away member gets no kill experience, no event rewards and no found gold. This matches the rule "to
  every player on the map".
- **The host saving** does not concern the away member.
- **The host leaving.** The guest gets a disconnect and is already home. This is the idea's best property.
- **A third player joining** works, but the away member's id and slot must be reserved. Today `addGuestPlayer` would
  hand its id out, and the `MaxGuests` check counts only present guests.

**The connection: keep it open.**

- ENet pings twice a second by itself, so the silence limit is not reached while the guest's game runs frames.
- Chat and the players list carry no map revision and flow as they are.
- Pings and bodies do carry a map revision. They must be dropped while away, or the others' marks appear on the
  guest's own map.
- A guest joined through the relay holds one of its ports while away.
- Dropping and re-establishing needs an identity the host can recognise, which is the open reconnect work (CO-6,
  CO-8). It also needs the lobby code, which changes when the lobby loses the session.
- If the line drops while away, membership simply ends and the player joins anew.

**The two-writer character**

- While out, the guest's game is the only writer, and step back hands the whole character over as a Hello does.
  Today's join already does that.
- Step out can be made better than today's leave. The guest asks, the host answers on the ordered control channel
  with a final whole character, and the guest takes that home. Today's leave takes the mirror as it stands, so
  anything in flight is lost.

**Can the host step out?**

- No. The host's game is the one world runtime, and its "own world" is the session's world (CO-60).
- What it gets instead: once every guest is away, no travel vote is proposed, so the host travels freely. Returning
  guests land on its new map.

## 3. Alternatives

- **A. Remote house visit in the host's world (recommended).** From the journal's trainer finder
  (`TrainerDirectory.h` lists every teacher by house), a player opens a known teacher's, shop's or temple's house
  screen for a fee.
  - It is the same world with no duplication, takes no map loads, and works for the host.
  - A house opens from its id alone (`luaEnterHouse`), and the host already serves houses to a guest
    (`net_guest_house_services.yml`).
  - Cost: small to medium, plus a design decision, because it cheapens geography; it could be limited to maps the
    world has visited.
  - Not checked: doors whose map script decides the entry, and MM9's walk-in shops, which are not house screens.
- **B. A "Rejoin" button after Leave.** Remember the last host, code and password. Leave, errand and rejoin already
  work in about six clicks. Cost: tiny. It gives no greyed-out seat, chat or reserved slot.
- **C. A round trip for the group in one vote.** Everyone still loads two maps and waits. Cost: small, benefit small.
- **D. Nothing.** The travel vote is cheap and training already takes no time in co-op. The tedium is the map loads
  on every machine.

## 4. Proposal, if step-out is built

**Behaviour**

- On the Multiplayer screen a guest clicks "Step Out to Your Own Game". It is refused while down, with monsters
  near, with a chest or conversation open, or if the guest joined with a character file.
- Everyone sees "&lt;name&gt; stepped out" and the portrait greyed with "away".
- The guest plays its own game as single-player; chat still works, and its panel shows the others greyed.
- "Return to &lt;host&gt;'s Game" loads the host's current map at its arrival point.
- While out the member has no vote and no rewards, and is not counted for monster health.
- If the host ends the session, the guest is told and simply stays home.

**First version (medium overall)**

- **`CoopSession`** (medium, about 200 lines):
  - `stepOut()` and `stepBack()`, split out of `guestReturnToOwnGame` and `guestSendHello`;
  - an away flag on `HostPeer` and on the guest;
  - the mutes in `hostSendMapMessage` and `sendToAll`;
  - `away()` beside `joined()` and `joining()`, so that `quickLoadFromPath` and the "Joining ..." text do not
    misfire.
- **`GameSession::addGuestPlayer`** with a reserved id, and `MaxGuests` counting away members: small.
- **A new protocol version:** `StepOut` and `StepBack` from the guest, a final character and acknowledgement from
  the host, and one `away` flag per player in the players list.
- **Screens** (small):
  - `CoopMenuScreen.cpp`: the two buttons;
  - `renderCoopPlayersRail` (`GameplayUiRenderer.cpp`): the grey state;
  - `syncCoopPlayerBodies`: no bodies or marks while away;
  - `updateCoopChat`: allow chat while away;
  - console `coop stepout` and `coop stepback` for the tests.

**Later**

- Character-file joiners.
- A reconnect that survives a cut line (with CO-6).
- A status line of the away member's level and health.
- A cooldown, if play shows abuse.

**Tests** (two-game scenarios in `tests/scenarios/coop/`)

- `net_step_out.yml`: own map, the seat and id kept, gains brought back.
- `net_step_out_travel.yml`: the host travels without a vote, and the guest returns onto the new map.
- `net_step_out_rewards.yml`: a kill and an event reward do not reach the away member, and monster health is
  resized.
- `net_step_out_host_ends.yml`: the guest stays home untouched.
- `net_step_out_refused.yml`: down, or monsters near.
- `net_step_out_quest_items.yml`.
- `net_step_out_save_load.yml`.
- The reserved id with a third player, as a case in `tests/CoopNetTests.cpp`: the scenario runner has only two
  games.

**Risks**

- A place that still sees the away member.
- The hand-over losing an item in flight.
- A wrong ruleset loaded while out; this is caught by checking the content again on return.
- Returning to the title or starting a new game calls no leave today. Leave is called only from the console, the
  Leave button, a failed join and loading a save.

## 5. What stays awkward

- It is another world, another place and another calendar, and the reachable teachers depend on the guest's own save.
- The host has no equivalent.
- A stepped-out player gets free rest and reloads.
- The guest sits through two map loads and lands at the arrival point.

It is a good break-and-return feature. It is a weak errand feature.

## Side findings, read not run

Both are the open items' CO-143.

- **The own game's Adventurer's Inn roster looks lost on coming home.** `hostHandleHello` clears it from the
  character, and `guestReturnToOwnGame` replaces the own game's whole party with that character.
- **An item on the cursor at the moment of leaving is not put back** in `guestReturnToOwnGame`, although the design
  says it should be.
