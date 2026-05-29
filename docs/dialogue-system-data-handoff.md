# MM8 Dialogue / House / Trainer Data Handoff

This document is for another Codex session implementing MM8 dialogue and house systems from
original data in a new C++ engine.

The goal is to describe the real data relationships and the engine-side semantics behind them, so the
other session can build a clean system without ad hoc heuristics.

This document uses three sources:

- current OpenMM8 implementation in this repo
- original-style data as represented by the imported MM8 text tables
- OpenEnroth as behavioral/reference evidence for hidden engine-side semantics

Known hardcoded assumptions, data-backed inferences, and incomplete areas are tracked separately in:

- [dialogue-system-assumptions.md](/home/pjasicek/github/OpenYAMM/docs/dialogue-system-assumptions.md)

## Current OpenYAMM Canonical Data State

The canonical runtime dialogue/house tables in this repo are now:

- [NPC.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC.txt)
- [NPC_TOPIC.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_TOPIC.txt)
- [NPC_TOPIC_TEXT.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_TOPIC_TEXT.txt)
- [NPC_GREET.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_GREET.txt)
- [NPC_NEWS.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_NEWS.txt)
- [HOUSE_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/HOUSE_DATA.txt)
- [HOUSE_ANIMATIONS.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/HOUSE_ANIMATIONS.txt)

The old duplicated dialogue tables under `assets_dev/Data/EnglishT/` were intentionally removed:

- `NPCDATA.txt`
- `npctopic.txt`
- `npctext.txt`
- `npcgreet.txt`
- `NPCNEWS.txt`
- `2DEvents.txt`

One legacy table is still intentionally kept and loaded from `EnglishT` because there is not yet a
replacement under `assets_dev/Data/`:

- [NPCGROUP.TXT](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/NPCGROUP.TXT)

So if another session changes dialogue loading, it should preserve the current canonical layout
instead of restoring the deleted `EnglishT` duplicates.

## High-Level Model

There are three distinct dialogue contexts in MM8:

1. outdoor NPC talk
2. outdoor NPC news talk
3. house/building talk

Do not collapse these into one blob.

They share some tables, but not the same semantics.

## Core Data Tables

### NPC Table

Primary source in OpenMM8:

- [NPC.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/NPC.txt)

Parsed by:

- [NpcTalkDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcTalkDb.cs)

Relevant fields:

- `NpcId`
- display `Name`
- portrait `Pic`
- `Greet`
- six topic/event ids in columns `A..F`

OpenMM8 currently loads:

- `Name`
- `PictureId`
- `GreetId`
- `TopicList`

Important:

- the six topic ids are not just text ids
- they are topic/event ids
- the topic id is both:
  - the thing shown in the sidebar
  - the thing handed to global NPC-topic/event logic when clicked

### NPC Topic Table

Primary source:

- [NPC_TOPIC.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/NPC_TOPIC.txt)

Parsed by:

- [NpcTopicDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcTopicDb.cs)

Fields that matter:

- `TopicId`
- sidebar label `Topic`
- `TextId`

Meaning:

- `Topic` is the button label shown in the sidebar
- `TextId` points into the body-text table and is usually the message-pane text shown when that topic
  is selected

This separation is important.
Do not assume the sidebar text and the message-pane text are the same string.

### NPC Topic Text Table

Primary source:

- [NPC_TOPIC_TEXT.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/NPC_TOPIC_TEXT.txt)

Parsed by:

- [NpcTextDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcTextDb.cs)

Meaning:

- `TextId -> long-form body text`

This is what should appear in the main message pane for normal NPC topics and also for trainer offer
screens.

### NPC Greet Table

Primary source:

- [NPC_GREET.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/NPC_GREET.txt)

Parsed by:

- [NpcGreetDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcGreetDb.cs)

Meaning:

- each greet id has:
  - `Greeting1`
  - `Greeting2`

Semantics:

- first time you talk in a given visit/state -> use `Greeting1`
- later repeats -> use `Greeting2`

This is stateful per active NPC talk context, not globally stateless text lookup.

### NPC News Table

Primary source:

- [NPC_NEWS.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/NPC_NEWS.txt)

Parsed by:

- [NpcNewsDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcNewsDb.cs)

Meaning:

- `NewsId -> one body text`

This is used for the "friendly outside NPCs say current local news" flow.

In OpenMM8 this is currently implemented by reusing `NpcTalkProperties` and overloading `GreetId` with
the news id when `IsNpcNews == true`.

For a new engine, do not overload that field.
Use a typed context such as:

- `DialogueContextKind::NpcNews`
- `context.newsId`

### House Data Table

Primary source in current OpenMM8:

- [HOUSE_DATA.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/HOUSE_DATA.txt)

Parsed by:

- [HouseDataDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/HouseDataDb.cs)

Important fields:

- `HouseId`
- local id
- `TypeName`
- `MapId`
- `AnimationId`
- house display `Name`
- proprietor name/title
- proprietor portrait/picture id
- `PriceMultiplier`
- `SkillPriceMultiplier`
- `TrainingMaxLevel`
- `OpenFrom`, `OpenTo`
- exit metadata
- restriction quest bit
- `EnterText`
- `SkillOffers`

Important note:

- this file is no longer a pristine original export
- it is an adapted runtime table derived from original house data plus OpenMM8 augmentation

Current OpenYAMM choice:

- use `HOUSE_DATA.txt` as the canonical house table
- use `HOUSE_ANIMATIONS.txt` as the augmentation/presentation table

The old `2DEvents.txt` copy is no longer present in this repo.

### House Animation / Augmentation Table

Primary source in current OpenMM8:

- [HOUSE_ANIMATIONS.txt](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Resources/Data/HOUSE_ANIMATIONS.txt)

Parsed by:

- [HouseAnimationDb.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/HouseAnimationDb.cs)

Important fields:

- `HouseId`
- `AnimationId`
- NPC ids inside that house
- video resource name
- enter sound resource path

This table exists because original text data does not contain all of the following directly:

- house movie name/path
- room sound family id in a friendly exported table
- house NPC wiring in the same shape OpenMM8 needed

## What Comes From Original Data vs Engine Semantics

This distinction is critical.

### Truly Data-Driven

- outside NPC identity, portrait, greet id, and six topic ids from `NPC.txt`
- sidebar topic labels from `NPC_TOPIC.txt`
- long-form topic message text from `NPC_TOPIC_TEXT.txt`
- greet texts from `NPC_GREET.txt`
- NPC news texts from `NPC_NEWS.txt`
- house id/type/animation/open hours/proprietor/pricing from `HOUSE_DATA.txt`

### Engine-Side Semantic Conventions

These are deterministic rules, but not plain text-table lookups:

- first-vs-repeat greeting selection
- nested dialogue states
- mastery trainer topic id range semantics
- roster-join yes/no nested state
- house service dispatch by `HouseType`
- house entry/leave sounds
- service-specific submenu structure

### Original Engine Data Not Present In Exported Text Tables

This is the big trap.

In original MM7/MM8-style engine behavior, house entry presentation depends on:

- `houseTable[houseId].uAnimationID` from the house table
- then an engine-side animation table `pAnimatedRooms[animationId]`

OpenEnroth references:

- `HouseTable.cpp`: `uAnimationID` is loaded from the house table
- `UIHouses.cpp`: `pAnimatedRooms`

That `pAnimatedRooms` table contains things like:

- `video_name`
- `house_npc_id`
- `uBuildingType`
- `uRoomSoundId`

That table is not present in the original text exports you currently have.

So a new engine must do one of these explicitly:

1. reconstruct/import the equivalent animation table into data
2. author a small augmentation table
3. hardcode the table in engine code

Option 1 or 2 is better than heuristics.

## Wiring For Outdoor NPC Talk

The direct relationship is:

1. `NpcId -> NPC row`
2. NPC row gives:
   - portrait
   - greet id
   - up to six topic ids
3. each topic id resolves through `NPC_TOPIC.txt`:
   - sidebar label
   - `TextId`
4. `TextId` resolves through `NPC_TOPIC_TEXT.txt`

Runtime state required:

- whether this NPC has already delivered greeting 1 in the current conversation/state
- current nested dialogue state, if any
- whether the NPC is still present/available

OpenMM8 runtime shape:

- [NpcTalkProperties.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/TalkContext/NpcTalkProperties.cs)

Recommended C++ shape:

- immutable `NpcDialogueDefinition`
- mutable `NpcDialogueRuntimeState`

Do not mutate the raw data objects directly if you can avoid it.

## Wiring For Outdoor NPC News

The direct relationship is:

1. choose a normal `NpcId` for portrait/name/context
2. choose a `NewsId`
3. open a dialogue context in "news mode"

In OpenMM8:

- `TalkNPCNews(npcId, npcNewsId)` uses the NPC's portrait/name but replaces the greet path with a news
  path

Recommended C++ interpretation:

- this is not a separate NPC row
- it is a different conversation mode bound to the same NPC identity

Suggested model:

- `DialogueContextKind::NpcTalk`
- `DialogueContextKind::NpcNews`

Then:

- same portrait/name
- different body-text resolver
- usually no normal topic list

## Wiring For House Entry

There are two distinct house cases:

1. service houses
2. houses/buildings with NPCs inside

They can coexist in the same entered scene.

In OpenMM8, a house entry creates a `TalkScene`:

- [TalkScene.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/TalkContext/TalkScene.cs)

A `TalkScene` may contain:

- one synthetic proprietor/service talk node
- zero or more normal NPC talk nodes for NPCs inside

The runtime relation is:

1. `HouseId -> HouseData`
2. optional `HouseId -> HouseAnimationData`
3. `HouseServiceFactory.ResolveServiceType(HouseData.TypeName)`
4. if service exists, create synthetic house-service talk participant
5. if animation row lists inside NPC ids, append those real NPC talk participants

This produces either:

- a single speaker view
- or a house "lobby" with multiple avatars to choose from

## How Houses Are Wired Together Through Data

### Service Type

Current OpenMM8 dispatch:

- [HouseServiceFactory.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/Houses/HouseServiceFactory.cs)

It maps `TypeName` to service family:

- weapon/armor/magic/alchemy -> shop
- temple -> temple service
- bank -> bank
- tavern -> tavern
- training -> training hall
- elemental/light/dark/self/spell shop -> guild

This is not heuristic text guessing.
It is a closed mapping on the house type field.

### Proprietor Identity

For service houses, the visible dialogue participant is usually synthetic:

- name from house proprietor fields
- portrait from house picture id
- behavior from service type

It is not necessarily a normal NPC row from `NPC.txt`.

### NPCs Inside Houses

These are explicit NPC ids in `HOUSE_ANIMATIONS.txt` in OpenMM8.

For a faithful ground-up engine:

- treat this as `HouseId -> [NpcId...]`
- do not infer inside NPCs from proprietor name text or topic ownership strings

### Video / Enter Sound

Original-style lookup chain in OpenEnroth:

1. `HouseId -> uAnimationID` from house table
2. `uAnimationID -> pAnimatedRooms[animationId]`
3. `video_name` from that animation table
4. load `video_name + ".bik"` or `".smk"`

Relevant OpenEnroth references:

- `HouseTable.cpp`
- `UIHouses.cpp`
- `MediaPlayer.cpp`

For room/proprietor speech:

1. `HouseId -> uAnimationID`
2. `uAnimationID -> roomSoundId`
3. `HouseSoundType` chosen by engine logic
4. final sound id computed as:
   - `type + 100 * (roomSoundId + 300)`

Relevant reference:

- `UIHouses.cpp::playHouseSound(...)`

Generic enter/leave door sounds are separate:

- enter: `SOUND_enter`
- leave: `SOUND_WoodDoorClosing`

## How Dialogue Nesting Works

There are three distinct nesting/state mechanisms in current OpenMM8.

### 1. Generic Nested Topic Lists

Used for:

- simple yes/no prompts
- small explicit topic submenus

OpenMM8 runtime:

- `NpcTalkProperties.NestedTopicIds`

Conceptually:

- push a new topic list
- show that list instead of the base NPC topic list
- `Escape` pops it

### 2. Runtime House-Service Menus

Used for:

- temple/bank/tavern/training/shop/guild menus and submenus

OpenMM8 runtime:

- `NpcTalkProperties.RuntimeMenuIds`

Conceptually:

- service class owns submenu graph
- UI requests current runtime options from the service
- `Escape` pops one runtime menu id

### 3. Structured Special Offer States

Used for:

- mastery trainers

OpenMM8 runtime:

- `NpcTalkProperties.CurrentOffer`

Fields:

- offer type
- source topic id
- message text id
- offered topic ids

This is important.
Do not represent mastery trainers as a random one-off special case with scattered flags.

The clean model is:

- static trainer topic in the normal sidebar
- click it
- enter a typed offer state
- message pane switches to fixed descriptive text
- sidebar becomes one dynamic offer/rejection action

That is what OE does, and this is how OpenMM8 now mirrors it.

## Mastery Trainers In Houses / Outside

### What Is Data and What Is Not

Trainer topics are not normal free-form topics.

There is a deterministic topic-id block:

- `300..416`

These are mastery offer topics, ordered in groups of three:

- expert
- master
- grandmaster

Examples:

- `312` Expert Spear
- `313` Master Spear
- `314` Grand Master Spear

Teacher-hint topics are separate:

- `417+`

Those are just normal topics naming the trainer NPCs, e.g.:

- `431 = Yarrow`

### Why This Is Not a Heuristic

The engine should explicitly encode the trainer topic contract:

- trainer offer topic range
- skill ordering table
- mastery ordering within each skill block

OpenMM8 uses an explicit `MasteryTeacherSkillMap` array in
[TalkEventMgr.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/GameEvents/TalkEventMgr.cs)
for this reason.

Do not assume enum ordinal alignment.

Recommended C++ approach:

- explicit `std::array<SkillType, N>` matching the topic block order
- decode:
  - `zeroBased = topicId - firstTrainerTopicId`
  - `skillIndex = zeroBased / 3`
  - `teacherLevel = zeroBased % 3`

### Offer Flow

Correct flow:

1. sidebar shows static topic label from data, e.g. `Grand Master Spear`
2. clicking it opens trainer offer state
3. message pane shows the topic's `TextId` body text from `NPC_TOPIC_TEXT`
4. sidebar shows one dynamic action:
   - approved purchase text
   - or rejection reason
5. active character switching refreshes that dynamic action
6. successful training applies mastery, gold deduction, reaction, and usually exits/closes that offer state

### Approval Logic

This is engine semantic logic, not plain data lookup.

Inputs:

- active character
- character class
- class max mastery table
- current skill level/mastery
- promotion chain
- some special stat prerequisites
- gold

Data dependency:

- class skill caps from `CLASS_SKILLS`

Recommended:

- keep this as explicit gameplay logic
- do not try to infer it from topic text

## Shop / Service Houses

Service houses are not normal NPC dialogues.

They are better modeled as:

- `HouseDialogueContext`
- resolved `HouseServiceType`
- runtime-generated options

This is the current OpenMM8 direction and the correct one.

### Data Inputs

- house type
- house pricing
- house open hours
- service-specific fields
- offered-skill list from `SkillOffers`

### Engine-Side Menu Semantics

Examples:

- bank:
  - deposit
  - withdraw
  - amount-entry prompt
- temple:
  - heal
  - donate
  - learn skills
- training:
  - train
  - learn skills
- tavern:
  - rent room
  - buy food
  - learn skills
  - arcomage submenu
- shops:
  - buy standard
  - buy special
  - display equipment
  - learn skills
- guilds:
  - buy spellbooks
  - learn skills

These menus are not stored as plain text rows in the original NPC topic data.
They are engine-defined service flows parameterized by house data.

So the correct "no heuristics" approach is:

- service type dispatch is deterministic from house type
- menu structure is explicit engine logic per service family
- prices/offers/open-hours/etc. come from data

## Roster Joining Dialogues

Current OpenMM8 behavior:

- a specific clicked topic id opens a yes/no nested submenu
- synthetic topic ids are used:
  - `10000 = Yes`
  - `10001 = No`
- yes/no is currently stored in a small runtime object `RosterInvite`

Relevant implementation:

- [TalkEventMgr.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/GameEvents/TalkEventMgr.cs)
- [PlayerParty.cs](/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Gameplay/Game/Player/PlayerParty.cs)

Current limitation in OpenMM8:

- actual roster-id-to-character recruitment is still placeholder

Recommended clean C++ design:

- treat roster join as a typed dialogue action with payload:
  - `rosterId`
  - `partyFullMessageTextId`
- do not infer it from the text "Join"
- do not random-add a character like current OpenMM8 placeholder

Then:

1. topic click emits `DialogueAction::RosterJoinOffer`
2. runtime pushes `Yes/No` submenu
3. yes:
   - if party full -> route to inn/roster logic
   - else recruit the correct roster entry
4. no:
   - return to the previous dialogue state

## Recommended C++ Runtime Decomposition

To avoid heuristics and spaghetti flags, build these layers explicitly:

### Immutable Data

- `NpcDefinition`
- `NpcTopicDefinition`
- `NpcTextDefinition`
- `NpcGreetDefinition`
- `NpcNewsDefinition`
- `HouseDefinition`
- `HousePresentationDefinition` or `HouseAnimationDefinition`

### Runtime State

- `NpcDialogueRuntimeState`
  - visited flag
  - presence flag
  - nested topic stack
  - current special offer
- `HouseDialogueRuntimeState`
  - current service submenu
  - temporary text input state

### Typed Contexts

- `NpcTalkContext`
- `NpcNewsContext`
- `HouseContext`
- `HouseServiceContext`

### Typed Actions

- `RunTopicEvent(topicId)`
- `OpenHouse(houseId)`
- `OpenNpcNews(npcId, newsId)`
- `OpenRosterJoinOffer(rosterId, fullPartyTextId)`
- `OpenMasteryOffer(topicId)`
- `SubmitHouseNumericInput(inputKind, value)`

That is the clean way to eliminate ad hoc branching.

## Final Guidance

If the other session wants a system "fully from data", the important correction is:

- most identity and content selection is data-driven
- but several semantics are not directly in original text files and must be represented explicitly as
  engine contracts or augmentation tables

The main examples are:

- house animation/movie/sound family lookup
- service-house menu graphs
- mastery trainer topic block semantics
- roster-join yes/no special handling

Those should be implemented as explicit typed systems, not guessed from strings.
