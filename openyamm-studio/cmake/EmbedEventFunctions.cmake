# Writes OUT: a C++ file with the names of the event functions the game gives Lua (`evt.<name>`), read from the
# game's own registration (SOURCE: game/events/EventRuntime.cpp), so the studio never keeps a second list. Run as a
# script (cmake -P).
file(READ "${SOURCE}" source)
string(REGEX MATCHALL "registerLuaFunction\\(pLuaState, \"[A-Za-z_0-9]+\"" calls "${source}")
set(names "")

foreach(call IN LISTS calls)
    string(REGEX REPLACE ".*\"([A-Za-z_0-9]+)\"" "\\1" name "${call}")
    string(APPEND names "${name} ")
endforeach()

list(LENGTH calls count)

if (count LESS 100)
    message(FATAL_ERROR "EmbedEventFunctions: only ${count} registerLuaFunction calls found in ${SOURCE}; the "
        "registration has changed its form and this script must follow it")
endif()

file(WRITE "${OUT}" "// Generated from game/events/EventRuntime.cpp by cmake/EmbedEventFunctions.cmake.\n"
    "namespace OpenYAMM::Studio\n{\nextern const char *const EventFunctionNames;\n"
    "const char *const EventFunctionNames = \"${names}\";\n}\n")
