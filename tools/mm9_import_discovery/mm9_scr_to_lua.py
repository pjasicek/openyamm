#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml


MM9_RUDE_EXIT_EVENT_ID_BASE = 50000
MM9_RUDE_EXIT_EVENT_ID_MAX = 52999
MM9_RUDE_USE_EVENT_ID_BASE = 53000
MM9_RUDE_USE_EVENT_ID_MAX = 55999
MM9_RUDE_FOUND_PLAYER_EVENT_ID_BASE = 56000
MM9_RUDE_FOUND_PLAYER_EVENT_ID_MAX = 58999


QUEST_XP_PROFILE_PATH = Path(__file__).with_name("mm9_quest_xp_profile.yml")


class ScrCompileError(RuntimeError):
    pass


QuestXpProfile = dict[tuple[str, str, int], int]


@lru_cache(maxsize=None)
def load_quest_xp_profile(path: Path = QUEST_XP_PROFILE_PATH) -> QuestXpProfile:
    """The balanced amount of each original GiveExp, by (script file, routine, original amount), all lower case
    (devdocs/mm9_rework/BALANCE_PLAN.md section 5.4)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profile: QuestXpProfile = {}
    for award in data.get("awards") or []:
        key = (str(award["script"]).lower(), str(award["routine"]).lower(), int(award["original"]))
        if key in profile:
            raise ValueError(f"{path}: duplicate quest XP award {key}")
        profile[key] = int(award["xp"])
    return profile


@dataclass
class ScrLine:
    number: int
    code: str


@dataclass
class ScrProgram:
    source_name: str
    declarations: dict[str, str] = field(default_factory=dict)
    declaration_kinds: dict[str, str] = field(default_factory=dict)
    routines: dict[str, list[ScrLine]] = field(default_factory=dict)
    routine_sources: dict[str, str] = field(default_factory=dict)  # routine -> include file it came from
    rude_exit_routine: str = ""
    use_routine: str = ""
    found_player_routine: str = ""


@dataclass
class CompiledRudeExit:
    source_name: str
    source_object_index: int
    event_id: int | None
    callback_routine: str
    lua_lines: list[str]
    use_event_id: int | None = None
    found_player_event_id: int | None = None
    excluded_operations: list[str] = field(default_factory=list)


UNSUPPORTED_ACTOR_OPERATIONS = {
    "addnpc",
    "addtrigger",
    "clearflag",
    "debugout",
    "dorude",
    "faceobject",
    "getmyhandle",
    "getobjecthandle",
    "getplayerhandle",
    "getpos",
    "loopanim",
    "onfoundplayer",
    "onfoundtarget",
    "ontargetwithindist",
    "playanim",
    "playsound",
    "rollovertext",
    "removeobject",
    "removetrigger",
    "resumewait",
    "runto",
    "setflag",
    "setpropnumber",
    "screenfadeout",
    "spawn",
    "stop",
    "target",
    "traceoff",
    "traceon",
    "trigger",
    "wait",
    "walkto",
}

SHARED_CONVERSATION_OPERATIONS = {
    "faceobject",
    "getplayerhandle",
    "target",
}

# A DoRude object's Use routine also stops the actor, reads the user's handle and plays a greeting animation before the
# engine opens its dialogue; the shared conversation path owns that presentation (MM9_RUDE_SCR_INTEGRATION.md).
DORUDE_USE_PRESENTATION_OPERATIONS = {
    "getparam",
    "loopanim",
    "playanim",
    "stop",
}

EXCLUDED_EXTERNAL_ROUTINE_PREFIXES = (
    "base",
    "follow",
    "gs_",
)

# NPC378's RUDE-exit wait only delays a cosmetic town-portal effect before permanently removing the messenger.
# Compile the required actor-state result directly instead of introducing a general SCR scheduler for one hook.
IMMEDIATE_ACTOR_REMOVAL_WAITS = {
    ("npc378.scr", "vanish"),
}


def strip_comment(raw_line: str) -> str:
    return raw_line.split(";", 1)[0].strip()


def parse_scr(source_text: str, source_name: str, discover_rude_exit: bool = True) -> ScrProgram:
    program = ScrProgram(source_name=source_name)
    current_routine = ""

    for line_number, raw_line in enumerate(source_text.splitlines(), start=1):
        code = strip_comment(raw_line)
        if not code:
            continue

        array_declaration = re.match(
            r"^#numberarray\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[([0-9]+)\]$",
            code,
            re.IGNORECASE)
        if array_declaration:
            declaration_name = array_declaration.group(1).lower()
            program.declarations[declaration_name] = "{}"
            program.declaration_kinds[declaration_name] = "numberarray"
            continue

        declaration = re.match(
            r"^#(number|string)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*=\s*(.*))?$",
            code,
            re.IGNORECASE)
        if declaration:
            declaration_kind = declaration.group(1).lower()
            declaration_name = declaration.group(2).lower()
            initializer = (declaration.group(3) or "").strip()
            if not initializer:
                lua_initializer = "0" if declaration_kind == "number" else "nil"
            elif declaration_kind == "string":
                lua_initializer = lua_token_string(initializer)
            else:
                lua_initializer = lua_value(initializer)
            program.declarations[declaration_name] = lua_initializer
            program.declaration_kinds[declaration_name] = declaration_kind
            continue

        if code.startswith("#"):
            continue

        if code.startswith(":"):
            current_routine = code[1:].strip().lower()
            if current_routine:
                program.routines.setdefault(current_routine, [])
            continue

        rude_exit = re.match(r"^OnRudeExit\s+([A-Za-z_][A-Za-z0-9_]*)", code, re.IGNORECASE)
        if rude_exit and discover_rude_exit:
            callback = rude_exit.group(1).lower()
            if program.rude_exit_routine and program.rude_exit_routine != callback:
                raise ScrCompileError(
                    f"{source_name}:{line_number}: multiple OnRudeExit callbacks are not supported")
            program.rude_exit_routine = callback

        trigger = re.match(
            r"^AddTrigger\s+Use\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)",
            code,
            re.IGNORECASE)
        if trigger:
            program.use_routine = trigger.group(1).lower()

        found_player = re.match(
            r"^OnFoundPlayer\s+([A-Za-z_][A-Za-z0-9_]*)",
            code,
            re.IGNORECASE)
        if found_player:
            program.found_player_routine = found_player.group(1).lower()

        if current_routine:
            program.routines[current_routine].append(ScrLine(line_number, code))

    return program


def merge_include_program(program: ScrProgram, include_program: ScrProgram) -> None:
    for name, initializer in include_program.declarations.items():
        program.declarations.setdefault(name, initializer)
    for name, declaration_kind in include_program.declaration_kinds.items():
        program.declaration_kinds.setdefault(name, declaration_kind)
    for routine, body in include_program.routines.items():
        if routine not in program.routines:
            program.routines[routine] = body
            program.routine_sources[routine] = include_program.source_name


def source_object_event_id(source_object_index: int, event_id_base: int, event_id_maximum: int) -> int:
    event_id = event_id_base + source_object_index
    if source_object_index < 0 or event_id > event_id_maximum:
        raise ScrCompileError(
            f"source object {source_object_index} cannot be represented by the MM9 RUDE callback event range")
    return event_id


def rude_exit_event_id(source_object_index: int) -> int:
    return source_object_event_id(
        source_object_index,
        MM9_RUDE_EXIT_EVENT_ID_BASE,
        MM9_RUDE_EXIT_EVENT_ID_MAX)


def rude_use_event_id(source_object_index: int) -> int:
    return source_object_event_id(
        source_object_index,
        MM9_RUDE_USE_EVENT_ID_BASE,
        MM9_RUDE_USE_EVENT_ID_MAX)


def rude_found_player_event_id(source_object_index: int) -> int:
    return source_object_event_id(
        source_object_index,
        MM9_RUDE_FOUND_PLAYER_EVENT_ID_BASE,
        MM9_RUDE_FOUND_PLAYER_EVENT_ID_MAX)


def split_arguments(arguments: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    quote = ""

    for character in arguments.strip():
        if quote:
            current.append(character)
            if character == quote:
                quote = ""
            continue
        if character in {'"', "'"}:
            quote = character
            current.append(character)
        elif character == "," or character.isspace():
            if current:
                values.append("".join(current))
                current = []
        else:
            current.append(character)

    if current:
        values.append("".join(current))
    return values


def normalize_expression(expression: str, variables: set[str] | None = None) -> str:
    normalized = expression.strip()
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1].strip()
    normalized = normalized.rstrip(",").strip()
    normalized = normalized.replace("<>", "!=")
    normalized = re.sub(r"\bTRUE\b", "1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bFALSE\b", "0", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bNULL\b", "nil", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bAND\b", "and", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bOR\b", "or", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("!=", "~=")

    keywords = {"and", "or", "not", "true", "false", "nil"}

    def replace_identifier(match: re.Match[str]) -> str:
        identifier = match.group(0)
        if identifier.lower() in keywords:
            return identifier.lower()
        normalized_identifier = identifier.lower()
        if variables is not None and normalized_identifier not in variables:
            return lua_token_string(identifier.lower())
        return f'state["{normalized_identifier}"]'

    return re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", replace_identifier, normalized)


def lua_value(value: str) -> str:
    stripped = value.strip().rstrip(",")
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", stripped):
        return stripped
    if stripped.lower() in {"true", "false"}:
        return "1" if stripped.lower() == "true" else "0"
    if stripped.lower() == "null":
        return "nil"
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        escaped = stripped[1:-1].replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return f'state["{stripped.lower()}"]'


def lua_token_string(value: str) -> str:
    stripped = value.strip().strip('"\'')
    escaped = stripped.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def lua_parameter_value(value: str) -> str:
    stripped = value.strip()
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", stripped):
        return stripped
    if stripped.lower() in {"true", "false"}:
        return "1" if stripped.lower() == "true" else "0"
    return lua_token_string(stripped.lower())


class RudeExitCompiler:
    def __init__(
        self,
        program: ScrProgram,
        source_object_index: int,
        script_params: list[str],
        actor_handles: dict[str, int],
        source_actor_handle: int | None,
        dorude_id: int | None = None,
        quest_xp_profile: QuestXpProfile | None = None,
    ):
        self.program = program
        self.quest_xp_profile = load_quest_xp_profile() if quest_xp_profile is None else quest_xp_profile
        self.source_object_index = source_object_index
        self.script_params = script_params
        self.actor_handles = {name.lower(): handle for name, handle in actor_handles.items()}
        self.source_actor_handle = source_actor_handle
        self.dorude_id = dorude_id
        self.reachable_routines: list[str] = []
        self.excluded_operations: list[str] = []
        self.root_routine = ""
        self.callback_kind = ""

    def compile(self) -> CompiledRudeExit | None:
        callback_specs: list[tuple[str, str, int, str]] = []
        if self.program.rude_exit_routine:
            callback_specs.append((
                "OnRudeExit",
                self.program.rude_exit_routine,
                rude_exit_event_id(self.source_object_index),
                "RegisterEvent"))
        if self.program.use_routine and self._routine_opens_rude(self.program.use_routine, set()):
            callback_specs.append((
                "Use",
                self.program.use_routine,
                rude_use_event_id(self.source_object_index),
                "RegisterEvent"))
        elif self.program.use_routine and self.dorude_id is not None:
            # The object's DoRude property opens dialogue NPCNbr on use after its script's Use trigger ran.
            callback_specs.append((
                "DoRudeUse",
                self.program.use_routine,
                rude_use_event_id(self.source_object_index),
                "RegisterEvent"))
        if (
            self.program.found_player_routine
            and self._routine_opens_rude(self.program.found_player_routine, set())
        ):
            callback_specs.append((
                "OnFoundPlayer",
                self.program.found_player_routine,
                rude_found_player_event_id(self.source_object_index),
                "RegisterEvent"))
        if not callback_specs:
            return None

        lines: list[str] = []
        event_ids: dict[str, int] = {}
        for callback_kind, callback, event_id, registration in callback_specs:
            if callback not in self.program.routines:
                raise ScrCompileError(
                    f"{self.program.source_name}: {callback_kind} callback {callback!r} has no routine")
            if lines:
                lines.append("")
            lines.extend(self._compile_event(callback_kind, callback, event_id, registration))
            event_ids[callback_kind] = event_id

        exit_callback = self.program.rude_exit_routine
        return CompiledRudeExit(
            source_name=self.program.source_name,
            source_object_index=self.source_object_index,
            event_id=event_ids.get("OnRudeExit"),
            callback_routine=exit_callback,
            lua_lines=lines,
            use_event_id=event_ids.get("Use", event_ids.get("DoRudeUse")),
            found_player_event_id=event_ids.get("OnFoundPlayer"),
            excluded_operations=sorted(set(self.excluded_operations)),
        )

    def _compile_event(self, callback_kind: str, callback: str, event_id: int, registration: str) -> list[str]:
        self.reachable_routines = []
        self.root_routine = callback
        self.callback_kind = callback_kind
        self._collect_routine(callback, set())
        title = f"MM9 RUDE {'Use' if callback_kind == 'DoRudeUse' else callback_kind} {self.source_object_index}"
        lines = [
            f"-- {self.program.source_name}: compiled {callback_kind} :{callback}",
            f'{registration}({event_id}, "{title}", function()',
        ]
        if callback_kind == "OnFoundPlayer":
            lines.extend([
                f"    if not MM9.foundPlayerEnabled({self.source_object_index}) then",
                "        return",
                "    end",
            ])
        body = []
        for routine in self.reachable_routines:
            body.append(f"    routine_{routine} = function()")
            body.extend(self._compile_routine(routine, "        "))
            body.append("    end")
            body.append("")
        # Only the variables the compiled routines read or write (the includes' AI globals, baseMelee.inc's ~100,
        # are never touched by a dialogue routine): an unused one would only be read and dropped.
        used = set(re.findall(r'state\["([^"]+)"\]', "\n".join(body)))
        lines.append("    local state = {}")
        declared = False
        for declaration, initializer in sorted(self.program.declarations.items()):
            if declaration not in used:
                continue
            declared = True
            if self._persistent_declaration(declaration):
                lines.append(
                    f'    state["{declaration}"] = '
                    f'MM9.scrValue({self.source_object_index}, "{declaration}", {initializer})')
            else:
                lines.append(f'    state["{declaration}"] = {initializer}')
        for parameter_index, target in self._parameter_bindings():
            if parameter_index < len(self.script_params) and target in used:
                declared = True
                lines.append(
                    f'    state["{target}"] = {lua_parameter_value(self.script_params[parameter_index])}')
        if declared:
            lines.append("")

        for routine in self.reachable_routines:
            lines.append(f"    local routine_{routine}")
        lines.append("")
        lines.extend(body)

        lines.append(f"    routine_{callback}()")
        if callback_kind == "DoRudeUse":
            lines.append(f"    MM9.openRude({self.dorude_id})")
        lines.append(f'end, "{title}")')
        return lines

    def _persistent_declaration(self, declaration: str) -> bool:
        initializer = self.program.declarations.get(declaration, "")
        return (
            self.program.declaration_kinds.get(declaration) == "number"
            and re.fullmatch(r"[-+]?\d+", initializer) is not None)

    def _routine_opens_rude(self, routine: str, visiting: set[str]) -> bool:
        if routine in visiting:
            return False
        body = self.program.routines.get(routine)
        if body is None:
            return False
        visiting.add(routine)
        for line in body:
            if re.match(r"^DoRude(?:\s|$)", line.code, re.IGNORECASE):
                return True
            call = re.match(r"^(?:gosub|goto)\s+([A-Za-z_][A-Za-z0-9_]*)", line.code, re.IGNORECASE)
            if call and self._routine_opens_rude(call.group(1).lower(), visiting):
                return True
        visiting.remove(routine)
        return False

    def _parameter_bindings(self) -> list[tuple[int, str]]:
        result: list[tuple[int, str]] = []
        for line in self.program.routines.get("main", []):
            match = re.match(
                r"^GetParam\s+([0-9]+)\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)",
                line.code,
                re.IGNORECASE)
            if match:
                result.append((int(match.group(1)), match.group(2).lower()))
        return result

    def _collect_routine(self, routine: str, visiting: set[str]) -> None:
        if routine in visiting:
            raise ScrCompileError(f"{self.program.source_name}: recursive routine :{routine} is not supported")
        if routine in self.reachable_routines:
            return
        if routine != self.root_routine and routine.startswith(EXCLUDED_EXTERNAL_ROUTINE_PREFIXES):
            self.excluded_operations.append(f"external routine {routine}")
            return
        body = self.program.routines.get(routine)
        if body is None:
            if routine.startswith(EXCLUDED_EXTERNAL_ROUTINE_PREFIXES):
                self.excluded_operations.append(f"external routine {routine}")
                return
            raise ScrCompileError(f"{self.program.source_name}: required routine :{routine} was not found")

        visiting.add(routine)
        self.reachable_routines.append(routine)
        for line in body:
            call = re.match(r"^(?:gosub|goto)\s+([A-Za-z_][A-Za-z0-9_]*)", line.code, re.IGNORECASE)
            if call:
                self._collect_routine(call.group(1).lower(), visiting)
        visiting.remove(routine)

    def _compile_routine(self, routine: str, indent: str) -> list[str]:
        output: list[str] = []
        block_depth = 0
        for line in self.program.routines[routine]:
            code = line.code.strip()
            assignment = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", code)
            if assignment:
                statement_indent = f"{indent}{'    ' * block_depth}"
                target_name = assignment.group(1).lower()
                output.append(
                    f'{statement_indent}state["{target_name}"] = '
                    f"{normalize_expression(assignment.group(2), set(self.program.declarations))}")
                if self._persistent_declaration(target_name):
                    output.append(
                        f'{statement_indent}MM9.setScrValue('
                        f'{self.source_object_index}, "{target_name}", state["{target_name}"])')
                continue
            command_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s+|,\s*)?(.*)$", code)
            if command_match is None:
                raise self._error(line, "cannot parse statement")
            command = command_match.group(1).lower()
            arguments = command_match.group(2).strip()

            if command in {"onrudeexit", "onpoststartworld", "onpostminisaveload", "onpostsaveload"}:
                continue
            if command == "if":
                expression = normalize_expression(arguments, set(self.program.declarations))
                output.append(f"{indent}{'    ' * block_depth}if {expression} then")
                block_depth += 1
                continue
            if command == "else":
                if block_depth == 0:
                    raise self._error(line, "else without if")
                block_depth -= 1
                output.append(f"{indent}{'    ' * block_depth}else")
                block_depth += 1
                continue
            if command == "endif":
                if block_depth == 0:
                    raise self._error(line, "endif without if")
                block_depth -= 1
                output.append(f"{indent}{'    ' * block_depth}end")
                continue

            statement_indent = f"{indent}{'    ' * block_depth}"
            values = split_arguments(arguments)
            if command == "exit":
                output.append(f"{statement_indent}do return end")
            elif command in {"gosub", "goto"}:
                if not values:
                    raise self._error(line, f"{command} requires a routine")
                target = values[0].lower()
                if target not in self.reachable_routines:
                    output.append(
                        f'{statement_indent}MM9.excludedActorOperation("external routine {target}")')
                else:
                    output.append(f"{statement_indent}routine_{target}()")
                    if command == "goto":
                        output.append(f"{statement_indent}do return end")
            elif command in {"set", "add"}:
                if len(values) != 2:
                    raise self._error(line, f"{command} requires two arguments")
                target = f'state["{values[0].lower()}"]'
                value = lua_value(values[1])
                if command == "set":
                    output.append(f"{statement_indent}{target} = {value}")
                else:
                    output.append(f"{statement_indent}{target} = ({target} or 0) + {value}")
                if self._persistent_declaration(values[0].lower()):
                    output.append(
                        f'{statement_indent}MM9.setScrValue('
                        f'{self.source_object_index}, "{values[0].lower()}", {target})')
            elif command in {"haskey", "hasitem", "hasgold"}:
                expected_count = 2
                if len(values) != expected_count:
                    raise self._error(line, f"{command} requires {expected_count} arguments")
                query = {
                    "haskey": "hasKey",
                    "hasitem": "hasItem",
                    "hasgold": "hasGold",
                }[command]
                arguments = lua_value(values[0])
                if command == "hasitem":
                    provenance = lua_token_string(f"{self.program.source_name}:{line.number}")
                    arguments += f", {provenance}"
                output.append(
                    f'{statement_indent}state["{values[1].lower()}"] = MM9.{query}({arguments})')
            elif command in {"givekey", "takekey", "givegold", "takegold", "giveexp"}:
                if len(values) != 1:
                    raise self._error(line, f"{command} requires one argument")
                operation = {
                    "givekey": "giveKey",
                    "takekey": "takeKey",
                    "givegold": "giveGold",
                    "takegold": "takeGold",
                    "giveexp": "giveExperience",
                }[command]
                balanced = self._balanced_experience(routine, values[0]) if command == "giveexp" else None
                if balanced is not None:
                    output.append(
                        f"{statement_indent}MM9.giveExperience({balanced}) "
                        f"-- MM9 GiveExp {values[0]}, mm9_quest_xp_profile.yml")
                else:
                    output.append(f"{statement_indent}MM9.{operation}({lua_value(values[0])})")
            elif command in {"giveitem", "takeitem"}:
                if len(values) != 1:
                    raise self._error(line, f"{command} requires one argument")
                operation = "giveItem" if command == "giveitem" else "takeItem"
                provenance = lua_token_string(f"{self.program.source_name}:{line.number}")
                output.append(
                    f"{statement_indent}MM9.{operation}({lua_value(values[0])}, {provenance})")
            elif command == "getrandomint":
                if len(values) != 3:
                    raise self._error(line, "getrandomint requires minimum, maximum, and destination")
                output.append(
                    f'{statement_indent}state["{values[2].lower()}"] = '
                    f"MM9.random({lua_value(values[0])}, {lua_value(values[1])}, {line.number % 256})")
            elif command == "arrayput":
                if len(values) != 3:
                    raise self._error(line, "arrayput requires array, index, and value")
                array_name = values[0].lower()
                output.append(
                    f'{statement_indent}state["{array_name}"][{lua_value(values[1])}] = '
                    f"{lua_value(values[2])}")
            elif command == "arrayget":
                if len(values) != 3:
                    raise self._error(line, "arrayget requires array, index, and destination")
                array_name = values[0].lower()
                output.append(
                    f'{statement_indent}state["{values[2].lower()}"] = '
                    f'(state["{array_name}"][{lua_value(values[1])}] or 0)')
            elif command == "clearcondition":
                if len(values) != 1:
                    raise self._error(line, "clearcondition requires one condition id")
                output.append(f"{statement_indent}if not MM9.clearCondition({lua_value(values[0])}) then")
                output.append(f"{statement_indent}    return")
                output.append(f"{statement_indent}end")
            elif command == "givepromo":
                if len(values) != 2:
                    raise self._error(line, "givepromo requires promotion and character")
                output.append(
                    f"{statement_indent}if not MM9.givePromotion("
                    f"{lua_token_string(values[0])}, {lua_token_string(values[1])}) then")
                output.append(f"{statement_indent}    return")
                output.append(f"{statement_indent}end")
            elif command == "dorude":
                if len(values) != 1:
                    raise self._error(line, "DoRude requires one dialogue id")
                output.append(f"{statement_indent}MM9.openRude({lua_value(values[0])})")
            elif command == "playsound":
                if not values:
                    raise self._error(line, "PlaySound requires a sound name")
                output.append(f"{statement_indent}MM9.playSound({lua_token_string(values[0])})")
            elif command == "getmyhandle":
                if len(values) != 1 or self.source_actor_handle is None:
                    raise self._error(line, "getmyhandle requires a generated actor destination")
                output.append(f'{statement_indent}state["{values[0].lower()}"] = {self.source_actor_handle}')
            elif command == "getobjecthandle":
                if len(values) != 2:
                    raise self._error(line, "getobjecthandle requires an object name and destination")
                actor_handle = self.actor_handles.get(values[0].lower())
                if actor_handle is None:
                    raise self._error(line, f"getobjecthandle target {values[0]!r} is not a generated actor")
                output.append(f'{statement_indent}state["{values[1].lower()}"] = {actor_handle}')
            elif command == "removeobject":
                if len(values) != 1:
                    raise self._error(line, "removeobject requires one object handle")
                output.append(f"{statement_indent}MM9.removeActor({lua_value(values[0])})")
            elif command == "setpos":
                if len(values) != 4:
                    raise self._error(line, "setpos requires an object handle and three coordinates")
                output.append(
                    f"{statement_indent}MM9.setActorPosition("
                    f"{lua_value(values[0])}, {lua_value(values[1])}, "
                    f"{lua_value(values[2])}, {lua_value(values[3])})")
            elif command == "wait":
                if len(values) != 3:
                    raise self._error(line, "wait requires timing values and a callback routine")
                wait_key = (self.program.source_name.lower(), values[2].lower())
                if wait_key not in IMMEDIATE_ACTOR_REMOVAL_WAITS or self.source_actor_handle is None:
                    raise self._error(line, "unsupported reachable actor operation 'wait'")
                output.append(f"{statement_indent}MM9.removeActor({self.source_actor_handle})")
            elif command == "onfoundplayer" and not values:
                output.append(f"{statement_indent}MM9.disableFoundPlayer({self.source_object_index})")
            elif command in SHARED_CONVERSATION_OPERATIONS or (
                    self.callback_kind == "DoRudeUse" and command in DORUDE_USE_PRESENTATION_OPERATIONS):
                self.excluded_operations.append(f"shared conversation operation {command} at line {line.number}")
                output.append(f"{statement_indent}-- {code} is handled by shared conversation behavior")
            elif command in UNSUPPORTED_ACTOR_OPERATIONS:
                raise self._error(line, f"unsupported reachable actor operation {command!r}")
            else:
                raise self._error(line, f"unsupported reachable command {command!r}")

        if block_depth != 0:
            raise ScrCompileError(f"{self.program.source_name}: routine :{routine} has an unterminated if")
        if not output:
            output.append(f"{indent}return")
        return output

    def _balanced_experience(self, routine: str, value: str) -> int | None:
        if not value.isdigit():
            return None
        source = self.program.routine_sources.get(routine, self.program.source_name)
        key = (Path(source).name.lower(), routine.lower(), int(value))
        return self.quest_xp_profile.get(key)

    def _error(self, line: ScrLine, message: str) -> ScrCompileError:
        return ScrCompileError(f"{self.program.source_name}:{line.number}: {message}: {line.code}")


def compile_rude_exit(
    source_text: str,
    source_name: str,
    source_object_index: int,
    include_sources: list[tuple[str, str]] | None = None,
    script_params: list[str] | None = None,
    actor_handles: dict[str, int] | None = None,
    source_actor_handle: int | None = None,
    dorude_id: int | None = None,
    quest_xp_profile: QuestXpProfile | None = None,
) -> CompiledRudeExit | None:
    """dorude_id: the object's DoRude dialogue (its NPCNbr). When given, a Use routine that does not open dialogue
    itself still compiles, as the Use event, followed by opening that dialogue."""
    program = parse_scr(source_text, source_name)
    for include_name, include_text in include_sources or []:
        merge_include_program(program, parse_scr(include_text, include_name, discover_rude_exit=False))
    return RudeExitCompiler(
        program,
        source_object_index,
        script_params or [],
        actor_handles or {},
        source_actor_handle,
        dorude_id,
        quest_xp_profile,
    ).compile()
