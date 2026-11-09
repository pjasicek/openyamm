#!/usr/bin/env python3
"""Collect the attack/cast timing data of every 3D actor for the timing review viewer.

For each model bound in assets_dev/worlds/<world>/models/actors.yml this gathers, per descriptor (tier):
the native sprite action lengths and frames (the billboard timing the game uses), the monster recovery, which
attacks the monster data actually uses, the attack sound, the bound clips with their lengths and the current
`animation.events` impact markers (with the comment written above them), and whether the installed runtime clips
match their accepted source.

    level_generation/creatures/timing_review/build_review_data.py [--world mm6|mm7|mm8]

Writes data/<world>/review_data.json, the native sprite frames as data/<world>/sprites/*.png and the attack sounds as
data/<world>/sounds/*.wav (all rebuildable).
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
TOOL = Path(__file__).resolve().parent
DATA_TABLES = ROOT / "assets_dev/engine/data_tables"
# Native sprite frames: MM6's, the modelled MM8 monsters' and MM7's were retired from the runtime when their 3D models
# were installed (MM7 on 2026-10-21, with a few MM7 families from the world's own sprites), and the remaining monster
# frames the same day; the runtime folders are searched last.
NATIVE_SPRITE_DIRS = [ROOT / "assets_source/creatures/mm6/backups/20261004/native_runtime_retired/engine/sprites",
                      ROOT / "assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites",
                      ROOT / "assets_legacy/sprites_mm7_monsters_20261021/assets_dev/engine/sprites",
                      ROOT / "assets_legacy/sprites_mm7_monsters_20261021/assets_dev/worlds/mm7/sprites",
                      ROOT / "assets_legacy/sprites_monsters_remaining_20261021/assets_dev/engine/sprites",
                      ROOT / "assets_dev/engine/sprites",
                      *sorted((ROOT / "assets_dev/worlds").glob("*/sprites"))]
ATTACK_TIMING = ROOT / "assets_dev/engine/rendering/sprite_attack_timing.yml"
PROJECTILES = ROOT / "assets_dev/engine/effects/projectiles.yml"
TICKS_PER_SECOND = 128.0
RECOVERY_SCALE = 2.133333333333333  # OeRealtimeRecoveryScale in OutdoorWorldRuntime.cpp
NO_MISSILE = {"", "0"}

# History that changes how a marker or a clip should be read; shown with the model.
HISTORY = {
    "mm6_min1.glb": "User decision 2026-10-14: Attack (and Death) retimed 2x faster; the attack markers were halved "
                    "with it (0.948 -> 0.474 s). A short melee wind-up is intended "
                    "(mm6_min1_reduce_claude/README.md).",
    "mm6_natf.glb": "Marker provenance unclear: mm6_natf_anim_claude/README.md asks for Attack 0.908 s and a Codex "
                    "round measured 0.573 s on a 1.83 s Attack, but the installed Attack is 0.93 s with 0.458 s.",
}


def readTable(path):
    rows = []
    with open(path, encoding="latin-1") as handle:
        for line in handle:
            row = line.rstrip("\n").split("\t")
            if row and row[0].strip().isdigit():
                rows.append([cell.strip() for cell in row])
    return rows


def cell(row, index):
    return row[index] if index < len(row) else ""


def loadDescriptors():
    descriptors = {}
    for row in readTable(DATA_TABLES / "monster_descriptors.txt"):
        descriptors[cell(row, 1).lower()] = {
            "attackSoundId": int(cell(row, 7) or 0),
            "sprites": {"standing": cell(row, 11), "melee": cell(row, 13), "ranged": cell(row, 14)},
        }
    return descriptors


# Charge colours as the game derives them (WorldFxSystem::resolveActorCharge), approximated for the preview: a missile
# token's projectile recipe (monster_projectiles.txt), a spell's school, and the enhanced style's flight light of the
# monster's projectile binding when it has one. Physical missiles have no charge.
MISSILE_RECIPES = {"air": "monster_air_bolt", "earth": "monster_earth_bolt", "fire": "monster_fire_bolt",
                   "water": "monster_water_bolt", "body": "monster_body_bolt", "mind": "monster_mind_bolt",
                   "spirit": "monster_spirit_bolt", "light": "monster_light_bolt", "dark": "monster_dark_bolt",
                   "ener": "blaster"}
RECIPE_COLOURS = {"monster_air_bolt": (10, 170, 255), "monster_earth_bolt": (92, 49, 14),
                  "monster_fire_bolt": (255, 60, 30), "monster_water_bolt": (0, 98, 208),
                  "monster_body_bolt": (10, 180, 80), "monster_mind_bolt": (200, 200, 5),
                  "monster_spirit_bolt": (10, 170, 255), "monster_light_bolt": (255, 255, 255),
                  "monster_dark_bolt": (126, 126, 126), "blaster": (255, 0, 0)}
SCHOOL_COLOURS = {"Fire": (255, 60, 30), "Air": (200, 200, 20), "Water": (158, 185, 241), "Earth": (92, 49, 14),
                  "Spirit": (10, 170, 255), "Mind": (180, 96, 255), "Body": (10, 180, 80), "Light": (255, 255, 255),
                  "Dark": (126, 126, 126)}
SCHOOLS = ["Fire", "Air", "Water", "Earth", "Spirit", "Mind", "Body", "Light", "Dark"]
SPELL_COLOURS = {"fireball": (255, 120, 32), "meteorshower": (255, 120, 32), "mindblast": (180, 96, 255),
                 "toxiccloud": (100, 180, 50), "poisonspray": (10, 180, 80)}


def spellKey(name):
    return re.sub(r"[^a-z]", "", name.split(",")[0].lower())


def loadSpellSchools():
    """Spell name (letters only) -> school, from the spell's id (eleven per school)."""
    schools = {}
    for row in readTable(DATA_TABLES / "spells.txt"):
        spellId = int(row[0])
        if 1 <= spellId <= 99 and len(row) > 2:
            schools[spellKey(row[2])] = SCHOOLS[(spellId - 1) // 11]
    return schools


def loadProjectileLights():
    """(recipe, monster picture or None) -> flight light rgb of the enhanced projectile bindings."""
    lights = {}
    for recipe, binding in ((yaml.safe_load(PROJECTILES.read_text()) or {}).get("projectiles") or {}).items():
        if (binding or {}).get("light"):
            lights[(recipe, None)] = tuple(binding["light"]["rgb"])
        for variant in (binding or {}).get("variants") or []:
            light = variant.get("light") or binding.get("light")
            for monster in variant.get("monsters") or []:
                if light:
                    lights[(recipe, monster.lower())] = tuple(light["rgb"])
    return lights


def chargeSources(role, monsterRows, picture, schools, lights):
    """What the role's charge looks like per monster of the tier: label, colour and whether it glows."""
    sources = []
    for monster in monsterRows:
        if role == "attack_ranged":
            tokens = [monster["attack1Missile"]] + ([monster["attack2Missile"]] if monster["attack2Chance"] > 0 else [])
            for token in tokens:
                if token in NO_MISSILE:
                    continue
                recipe = MISSILE_RECIPES.get(token.lower())
                colour = lights.get((recipe, picture), lights.get((recipe, None), RECIPE_COLOURS.get(recipe)))
                sources.append({"label": f"{token} missile", "rgb": list(colour or (255, 255, 255)),
                                "glows": recipe is not None})
        else:
            for chance, spell in ((monster["spell1Chance"], monster["spell1"]),
                                  (monster["spell2Chance"], monster["spell2"])):
                if chance <= 0 or spell in NO_MISSILE:
                    continue
                school = schools.get(spellKey(spell))
                colour = SPELL_COLOURS.get(spellKey(spell), SCHOOL_COLOURS.get(school, (255, 255, 255)))
                sources.append({"label": f"{spell.split(',')[0]} ({school or 'unknown spell'})", "rgb": list(colour),
                                "glows": True})
    unique = []
    for source in sources:
        if source not in unique:
            unique.append(source)
    return unique


def loadMonsters():
    monsters = {}
    for row in readTable(DATA_TABLES / "monster_data.txt"):
        monsters.setdefault(cell(row, 2).lower(), []).append({
            "name": cell(row, 1),
            "aiType": cell(row, 11),
            "recovery": int(cell(row, 14) or 0),
            "attack1Missile": cell(row, 19),
            "attack2Chance": int(cell(row, 20) or 0),
            "attack2Missile": cell(row, 23),
            "spell1Chance": int(cell(row, 24) or 0),
            "spell1": cell(row, 25).strip('"'),
            "spell2Chance": int(cell(row, 26) or 0),
            "spell2": cell(row, 27).strip('"'),
        })
    return monsters


def loadSpriteFrames():
    paths = [ROOT / "assets_dev/engine/rendering/sprite_frame_data_common.yml"]
    paths += sorted((ROOT / "assets_dev/engine/rendering/sprite_frames/monsters").glob("*.yml"))
    sprites = {}
    for path in paths:
        for sprite in (yaml.safe_load(path.read_text()) or {}).get("sprites", []):
            name = sprite["sprite_name"].lower()
            if name in sprites:
                continue
            frames = [{"texture": frame["texture_name"].split("/")[-1].lower(),
                       "seconds": frame["frame_length_raw"] * 8 / TICKS_PER_SECOND}
                      for frame in sprite.get("frames", [])]
            length = sprite.get("animation_length_raw", 0) * 8 / TICKS_PER_SECOND
            # Runtime fallback for a sprite without a length (animationSecondsForSpriteFrame): 0.3 s.
            sprites[name] = {"seconds": length if length > 0 else 0.3, "frames": frames}
    # A tier recoloured by palette (rob2ata: rob1ata__palette_8110) names the base frames without their direction
    # digit: point it at the base frame so it shows that image and shares the base sprite's signature and pick.
    textures = {frame["texture"] for sprite in sprites.values() for frame in sprite["frames"]}
    for sprite in sprites.values():
        for frame in sprite["frames"]:
            base = re.sub(r"__palette_\d+$", "", frame["texture"])
            if base != frame["texture"]:
                frame["texture"] = base + "0" if base + "0" in textures else base
    return sprites


def loadSounds():
    sounds = {}
    with open(DATA_TABLES / "sounds.txt", encoding="latin-1") as handle:
        for line in handle:
            row = line.rstrip("\n").split("\t")
            if len(row) > 1 and row[1].strip().isdigit():
                sounds[int(row[1])] = row[0].strip()
    return sounds


def soundPath(name, world):
    # Case-insensitive: MM8's files differ in case from sounds.txt ("cleric attk" is Cleric attk.wav).
    wanted = f"{name}.wav".lower()
    for directory in (ROOT / f"assets_dev/worlds/{world}/audio", ROOT / "assets_dev/engine/audio"):
        if directory.is_dir():
            for candidate in sorted(directory.glob("*.wav")):
                if candidate.name.lower() == wanted:
                    return candidate
    return None


def readGlb(path):
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    offset = 20 + length
    binary = b""
    if offset < len(data):
        binaryLength = struct.unpack_from("<I", data, offset)[0]
        binary = data[offset + 8:offset + 8 + binaryLength]
    return gltf, binary


def accessorBytes(gltf, binary, index):
    accessor = gltf["accessors"][index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return binary[start:start + components * 4 * accessor["count"]]


def clipInfo(path):
    """Clip name -> (duration, keyframe interval, hash of all channel data)."""
    gltf, binary = readGlb(path)
    clips = {}
    for animation in gltf.get("animations", []):
        duration = 0.0
        step = None
        digest = hashlib.sha1()
        channels = sorted(animation["channels"], key=lambda channel: (
            gltf["nodes"][channel["target"]["node"]].get("name", ""), channel["target"]["path"]))
        for channel in channels:
            sampler = animation["samplers"][channel["sampler"]]
            accessor = gltf["accessors"][sampler["input"]]
            duration = max(duration, accessor.get("max", [0.0])[0])
            times = accessorBytes(gltf, binary, sampler["input"])
            if accessor["count"] > 1:
                interval = (accessor["max"][0] - accessor["min"][0]) / (accessor["count"] - 1)
                step = interval if step is None else min(step, interval)
            digest.update((gltf["nodes"][channel["target"]["node"]].get("name", "")
                           + channel["target"]["path"]).encode())
            digest.update(times)
            digest.update(accessorBytes(gltf, binary, sampler["output"]))
        clips[animation.get("name", "")] = {"seconds": round(duration, 6), "step": step,
                                            "hash": digest.hexdigest()[:12]}
    return clips


def displayUrl(modelPath):
    """The GLB the browser shows: the accepted source in assets_source. Runtime copies in assets_dev are cooked (their
    textures/*.oytex are GPU formats a browser cannot decode) and are built from that source."""
    source = ROOT / "assets_source" / modelPath
    return "../../../" + ("assets_source/" if source.exists() else "assets_dev/") + modelPath


def markerComments(actorsPath):
    """Descriptor -> the comment lines written in its animation block before `events:`."""
    comments = {}
    descriptor = None
    pending = []
    for line in actorsPath.read_text().splitlines():
        match = re.match(r"^- descriptor:\s*(.+?)\s*$", line)
        if match:
            descriptor = match.group(1)
            pending = []
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            pending.append(stripped.lstrip("#").strip())
        elif stripped == "events:" and descriptor:
            if pending:
                comments[descriptor] = " ".join(pending)
            pending = []
        elif stripped:
            pending = []
    return comments


def roleUse(monsters):
    """Which attack animations the monster data uses: melee, missile (ranged) and spell (cast)."""
    if monsters and all(monster["aiType"].lower() == "wimp" for monster in monsters):
        return {"attack_melee": False, "attack_ranged": False, "cast": False, "wimp": True}
    melee = ranged = cast = False
    for monster in monsters:
        if monster["attack1Missile"] in NO_MISSILE:
            melee = True
        else:
            ranged = True
        if monster["attack2Chance"] > 0:
            if monster["attack2Missile"] in NO_MISSILE:
                melee = True
            else:
                ranged = True
        for chance, spell in ((monster["spell1Chance"], monster["spell1"]), (monster["spell2Chance"], monster["spell2"])):
            if chance > 0 and spell not in NO_MISSILE:
                cast = True
    return {"attack_melee": melee, "attack_ranged": ranged, "cast": cast, "wimp": False}


def nativeSpriteIndex():
    """Lower-case file name -> path of the native sprite frames (MM8's names are mixed case: m596Aa0.bmp)."""
    index = {}
    for directory in NATIVE_SPRITE_DIRS:
        for path in sorted(directory.glob("*.bmp")):
            index.setdefault(path.name.lower(), path)
    return index


def exportSprite(texture, written, nativeSprites, dataDir):
    """Convert one native sprite frame to a transparent PNG; return its file name or None."""
    if texture in written:
        return written[texture]
    candidates = [nativeSprites.get(f"{texture}.bmp"), nativeSprites.get(f"{texture}0.bmp")]
    candidates += sorted(ROOT.glob(f"assets_source/creatures/mm6/*/review/aligned_2x/{texture}.png"))
    source = next((path for path in candidates if path is not None and path.exists()), None)
    name = None
    if source is not None:
        image = Image.open(source)
        if image.mode == "P":
            image.info["transparency"] = 0
            image = image.convert("RGBA")
        name = f"{texture}.png"
        image.save(dataDir / "sprites" / name, optimize=True)
    written[texture] = name
    return name


def spriteSequence(sprites, spriteName, written, attackTimings, nativeSprites, dataDir):
    sprite = sprites.get(spriteName.lower())
    if sprite is None:
        return None
    # Tiers recolour the same frames: sprites with equal frames share one contact frame.
    signature = hashlib.sha1(json.dumps([(frame["texture"], frame["seconds"]) for frame in sprite["frames"]])
                             .encode()).hexdigest()[:12]
    return {"name": spriteName.lower(), "seconds": sprite["seconds"], "signature": signature,
            "contactFrame": attackTimings.get(spriteName.lower(), {}).get("contact_frame"),
            "soundDelay": attackTimings.get(spriteName.lower(), {}).get("sound_delay", 0),
            "frames": [{"image": exportSprite(frame["texture"], written, nativeSprites, dataDir),
                        "seconds": frame["seconds"]}
                       for frame in sprite["frames"]]}


def exportSound(name, path, exported, dataDir):
    """PCM copy the browser can play (the game's WAVs are IMA ADPCM) and a 20 ms peak envelope."""
    if name in exported:
        return exported[name]
    target = dataDir / "sounds" / f"{name}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-c:a", "pcm_s16le", str(target)],
                   check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "22050", "-"],
                         check=True, capture_output=True).stdout
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    window = 441
    peaks = [max((abs(value) for value in samples[i:i + window]), default=0) for i in range(0, len(samples), window)]
    loudest = max(peaks, default=0) or 1
    exported[name] = {"name": name, "url": str(target.relative_to(TOOL)), "seconds": round(len(samples) / 22050, 3),
                      "envelopeStep": 0.02, "envelope": [round(peak / loudest, 3) for peak in peaks]}
    return exported[name]


def projectExportIndex():
    index = {}
    for path in (ROOT / "level_generation/creatures").rglob("*.glb"):
        index.setdefault(path.name, []).append(path)
    return index


def newerProjectExports(index, name, sourcePath, sourceClips):
    """Project exports newer than the accepted source whose clips differ from it (work that may get installed)."""
    sourceTime = sourcePath.stat().st_mtime
    found = []
    for path in index.get(name, []):
        if path.stat().st_mtime <= sourceTime + 60:
            continue
        try:
            clips = clipInfo(path)
        except Exception:
            continue
        differing = sorted(clip for clip in set(clips) | set(sourceClips)
                           if clips.get(clip, {}).get("hash") != sourceClips.get(clip, {}).get("hash"))
        if differing:
            found.append({"path": str(path.relative_to(ROOT)),
                          "hoursNewer": round((path.stat().st_mtime - sourceTime) / 3600), "clips": differing})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm6")
    args = parser.parse_args()

    dataDir = TOOL / "data" / args.world
    (dataDir / "sprites").mkdir(parents=True, exist_ok=True)
    (dataDir / "sounds").mkdir(parents=True, exist_ok=True)
    nativeSprites = nativeSpriteIndex()
    attackTimings = {}
    if ATTACK_TIMING.exists():
        authored = (yaml.safe_load(ATTACK_TIMING.read_text()) or {}).get("sprites") or {}
        attackTimings = {name.lower(): timing for name, timing in authored.items()}
    exportedSounds = {}
    descriptors = loadDescriptors()
    monsters = loadMonsters()
    sprites = loadSpriteFrames()
    sounds = loadSounds()
    schools = loadSpellSchools()
    lights = loadProjectileLights()
    actorsPath = ROOT / f"assets_dev/worlds/{args.world}/models/actors.yml"
    actors = yaml.safe_load(actorsPath.read_text())["actors"]
    comments = markerComments(actorsPath)
    written = {}
    models = {}
    exportIndex = projectExportIndex()
    missingSprites = set()

    for actor in actors:
        modelPath = actor["model"]
        name = Path(modelPath).name
        runtime = ROOT / "assets_dev" / modelPath
        if name not in models:
            runtimeClips = clipInfo(runtime)
            source = ROOT / "assets_source" / modelPath
            sourceClips = clipInfo(source) if source.exists() else None
            models[name] = {
                "model": name,
                "url": displayUrl(modelPath),
                "attachments": [{"url": displayUrl(attachment["model"]), "node": attachment["node"]}
                                for attachment in actor.get("attachments", []) or []],
                # Clip lengths of the GLB the browser plays (the source); the runtime copy is checked against it.
                "clips": {clip: {"seconds": info["seconds"], "step": info["step"]}
                          for clip, info in (sourceClips or runtimeClips).items()},
                "upperBodyRoot": (actor.get("animation") or {}).get("upper_body_root"),
                "standingClip": (actor.get("clips") or {}).get("standing"),
                "walkingClip": (actor.get("clips") or {}).get("walking"),
                "source": {
                    "exists": sourceClips is not None,
                    "differingClips": sorted(clip for clip in set(runtimeClips) | set(sourceClips or {})
                                             if (sourceClips or {}).get(clip, {}).get("hash")
                                             != runtimeClips.get(clip, {}).get("hash")) if sourceClips else [],
                    "newerProjectExports": newerProjectExports(exportIndex, name, source, sourceClips)
                    if sourceClips else [],
                },
                "history": HISTORY.get(name),
                "descriptors": [],
            }
        model = models[name]
        descriptorName = actor["descriptor"]
        descriptor = descriptors.get(descriptorName.lower(), {"attackSoundId": 0, "sprites": {}})
        monsterRows = monsters.get(descriptorName.lower(), [])
        animation = actor.get("animation") or {}
        clips = actor.get("clips") or {}
        events = animation.get("events") or {}
        use = roleUse(monsterRows)
        spriteNames = descriptor["sprites"]
        sequences = {key: spriteSequence(sprites, spriteNames.get(key, ""), written, attackTimings,
                                         nativeSprites, dataDir)
                     for key in ("standing", "melee", "ranged")}
        for sequence in sequences.values():
            for frame in (sequence or {}).get("frames", []):
                if frame["image"] is None:
                    missingSprites.add(sequence["name"])
        recoveries = [max(0.3, monster["recovery"] / TICKS_PER_SECOND * RECOVERY_SCALE) for monster in monsterRows]
        roles = {}
        castClip = animation.get("cast")
        # Without a cast clip a spell plays the ranged attack clip and its marker (WorldFxSystem `casting`).
        for role, clip, spriteKey in (("attack_melee", clips.get("attack_melee"), "melee"),
                                      ("attack_ranged", clips.get("attack_ranged"), "ranged"),
                                      ("cast", castClip, "ranged")):
            if not clip:
                continue
            event = events.get(role) or {}
            roles[role] = {
                "clip": clip,
                "used": use[role] or (role == "attack_ranged" and not castClip and use["cast"]),
                "spellsUseThisClip": role == "attack_ranged" and not castClip and use["cast"],
                "nativeSeconds": (sequences[spriteKey] or {}).get("seconds"),
                "impact": event.get("impact"),
                # Charge and release sockets (WorldFxSystem ActionEvent), ranged attack and cast only.
                "glow": event.get("glow") or [],
                "release": event.get("release"),
                "glowScale": event.get("glow_scale", 1.0),
                "color": event.get("color"),
                "effects": event.get("effects") or {},
                "charge": chargeSources(role, monsterRows, descriptorName.lower(), schools, lights)
                if role != "attack_melee" else [],
            }
        soundName = sounds.get(descriptor["attackSoundId"])
        sound = soundPath(soundName, args.world) if soundName else None
        model["descriptors"].append({
            "name": descriptorName,
            "monsters": [monster["name"] for monster in monsterRows],
            "wimp": use["wimp"],
            "recoverySeconds": [round(value, 4) for value in sorted(set(recoveries))],
            "attackSound": exportSound(soundName, sound, exportedSounds, dataDir) if sound
            else {"name": soundName, "url": None},
            "sprites": sequences,
            "roles": roles,
            "scale": actor.get("scale", 1.0),
            "sockets": animation.get("sockets") or {},
            "markerComment": comments.get(descriptorName),
            "spells": sorted({monster[key] for monster in monsterRows for key in ("spell1", "spell2")
                              if monster[key] not in NO_MISSILE}),
            "missiles": sorted({monster[key] for monster in monsterRows for key in ("attack1Missile", "attack2Missile")
                                if monster[key] not in NO_MISSILE}),
        })

    # A model without attack or cast clips (a fleeing peasant) has nothing to review.
    skipped = sorted(name for name, model in models.items()
                     if not any(descriptor["roles"] for descriptor in model["descriptors"]))
    for name in skipped:
        del models[name]
    output = {"world": args.world, "models": sorted(models.values(), key=lambda model: model["model"])}
    (dataDir / "review_data.json").write_text(json.dumps(output, indent=1))
    print(f"{len(models)} models, {sum(len(model['descriptors']) for model in models.values())} descriptors, "
          f"{sum(1 for image in written.values() if image)} sprite frames")
    if skipped:
        print("without attack clips (left out):", ", ".join(skipped))
    if missingSprites:
        print("sprites without frame images:", ", ".join(sorted(missingSprites)))


if __name__ == "__main__":
    main()
