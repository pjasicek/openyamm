#pragma once

#include "core/Coplanar.h"

#include "core/MapLoad.h"

#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// core/Reachability.h
struct SolveResult;

struct AuditFinding
{
    // Stable name of the check: "event.unhandled", "event.unbound", "door.missing", "door.empty" ...
    std::string code;
    // "error": the map is broken for the player there. "warning": probably a mistake. "info": worth a look.
    std::string severity;
    std::string message;
    // How to fix it, in one sentence.
    std::string hint;
};

struct MapOverview
{
    size_t sectors = 0;
    size_t faces = 0;
    size_t bmodels = 0;
    size_t doors = 0;
    size_t actors = 0;
    size_t spawns = 0;
    size_t decorations = 0;
    size_t lights = 0;
    size_t chests = 0;
    // Loot containers of the scene file (the form new maps use for chests).
    size_t containers = 0;
    size_t handlers = 0;
    size_t boundEvents = 0;
};

MapOverview overviewOf(const LoadedMap &map);

// Checks of wiring (PLAN.md section 6, tier 1): what the map's faces and decorations call against what its script
// handles, and the doors its script moves against the doors the map has.
std::vector<AuditFinding> auditWiring(const LoadedMap &map);

// How many pairs of faces in one plane a map has, and of them how many its original has at the same place.
struct CoplanarSummary
{
    size_t pairs = 0;
    size_t asOriginal = 0;
    // The original the pairs were matched against; empty when there was none to match.
    std::string original;
};

// Faces in one plane over each other (core/Coplanar.h), as the map starts, with its moving parts a quarter, half and
// three quarters of their way along and at the other end: one "geometry.coplanar" finding for each pair. With the
// original's pairs (`pOriginalPlaces`, coplanarPlaces of the original map) a pair the original has at the same place
// is "info" and says so; the others are warnings, or with `strict` errors (`oymap audit --strict` fails on them).
// Outdoors the models' faces, all models together (`outdoorParts`: the part of each face, from the build's
// build.json, for the messages); `pOriginalPlaces` then from outdoorCoplanarPlaces.
std::vector<AuditFinding> auditCoplanarFaces(
    const LoadedMap &map,
    const std::vector<CoplanarPlace> *pOriginalPlaces,
    bool strict,
    CoplanarSummary &summary,
    const CoplanarNames &names = {},
    const OutdoorFaceParts &outdoorParts = {});

// Walkable tops where the party's eye lies in another sector's space than the game draws from (core/EyeSector.h): one
// "geometry.eye_sector" warning for each such floor face.
std::vector<AuditFinding> auditEyeSectors(const LoadedMap &map);

// Pictures squashed one way (core/Looks.h: texels per unit across and down more than 1.6 apart), by texture: one
// "texture.squashed" note (info) for each texture, with its worst face. And decorations standing in the air (more than
// 16 over the highest floor or top under them, not hanging kinds by their hint in `decorationTableText`, the asset
// root's decoration_data.txt): "thing.floating".
// `hanging`: the decorations (by entity number) a project says hang (`hangs: true`, or on a wall), which the built
// map cannot tell (XD-04's braziers on chains from a beam).
std::vector<AuditFinding> auditLooks(
    const LoadedMap &map, const std::string &decorationTableText, const std::set<int> &hanging = {});

// Questions the player is asked (evt.AskQuestion) whose answer he must know: for each answer that is no yes or no,
// the handlers whose texts (messages, signs, status lines) hold it, each with its hover name and the step of
// `solveMap` (`flowJson`, core/EventFlow) at which the party first reaches it, against the question's own step (the
// user's walk through XD-04: a door asking for a word given only by a cage nobody would click). "question.answer"
// warnings where no text gives the answer, where only a thing without a hover name gives it, or only later in the
// order; an "info" note listing where each answer is given. `pSolved`: the solve of the same map and flow when the
// caller has it already (check.audit with `solve`), so it is not walked twice; a map that asks nothing is not solved.
std::vector<AuditFinding> auditQuestions(
    const LoadedMap &map, const std::string &flowJson, const SolveResult *pSolved = nullptr);

// Clicked things (faces and decorations with an event) that on some branch of their handler do nothing the player
// sees: no text, window, door or part moving, item, chest, light, picture or teleport (the user's second walk through
// XD-04: a hoist's call button held by its brake). One "click.silent" note (info) for each such branch, with the tests
// that lead to it (`flowJson`: core/EventFlow).
std::vector<AuditFinding> auditSilentClicks(const LoadedMap &map, const std::string &flowJson);

// Moving parts that carry the party (a door record with a level top 64 or more across: a car, a cage, a lift) and are
// worked by clicked things, at each end of their way: is one of those things (other than the part's own faces) in
// reach of a rider on the deck there, within the game's 512 of his eye and facing him? (The user's walk through
// XD-02: "How am I supposed to press that lever while being on the moving platform?" Every car lever stood behind its
// gate's wall.) A ride is a part that carries the party as the game does (up and down, or a slide whose mover says
// so), travels 64 or more with its whole top and stops level with a floor beside it at both ends; a clicked thing
// counts when nothing drawn stands between the rider's eye and it. One "ride.no_switch" warning for each part with an
// end where none is, also where the part's own faces run its event (it works, but nothing tells a rider to click
// the car); a part moved only by its own faces, steps or timers is not judged. `names`: a project's lock names.
std::vector<AuditFinding> auditRides(
    const LoadedMap &map, const std::string &flowJson, const CoplanarNames &names = {});
}
