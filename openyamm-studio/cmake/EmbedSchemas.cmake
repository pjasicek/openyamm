# Writes OUT: a C++ file holding every schema/*.schema.json as a string. Run as a script (cmake -P).
file(GLOB schemaFiles "${DIR}/*.schema.json")
list(SORT schemaFiles)
set(text "// Generated from openyamm-studio/schema by cmake/EmbedSchemas.cmake.\n#include \"core/Schema.h\"\n\n")
string(APPEND text "namespace OpenYAMM::Studio\n{\nconst EmbeddedSchema EmbeddedSchemas[] = {\n")
set(count 0)

foreach(schemaFile IN LISTS schemaFiles)
    get_filename_component(name "${schemaFile}" NAME)
    file(READ "${schemaFile}" content)
    string(APPEND text "    {\"${name}\", R\"oyschema(${content})oyschema\"},\n")
    math(EXPR count "${count} + 1")
endforeach()

if (count EQUAL 0)
    string(APPEND text "    {nullptr, nullptr},\n")
endif()

string(APPEND text "};\nconst size_t EmbeddedSchemaCount = ${count};\n}\n")
file(WRITE "${OUT}" "${text}")
