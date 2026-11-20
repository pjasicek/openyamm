#pragma once

#include <yaml-cpp/yaml.h>

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The typed request list (openyamm-studio/schema/rpc/*.rpc.json, S5_BROWSER_EDITOR.md 2.3). One call of one method:
// the params are checked against the method's schema, the method runs, and the answer is the JSON text of
// {"result": ...} or {"error": {"code", "message", "data": {"kind", ...}}}. `oymap serve` puts it into its JSON-RPC
// response, `oymap call` prints it and the WebAssembly core's oymap_call returns it.
std::string callRpcMethod(const std::string &method, const YAML::Node &params);
std::string callRpcMethod(const std::string &method, const std::string &paramsJson);

bool isRpcMethod(const std::string &method);
// Work the core leaves for when no call waits (`oymap serve` calls it after each answer is written).
void rpcIdle();
// Every method of the catalogue, by full name.
std::vector<std::string> rpcMethodNames();
}
