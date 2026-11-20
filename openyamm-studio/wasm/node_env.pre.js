// Linked into the Node build with --pre-js: hands the host's environment to the program before main(). Emscripten
// gives the program an environment of its own (HOME=/home/web_user), which under NODERAWFS names a folder that does
// not exist on the host, and PhysicsFS's PHYSFS_init needs a user directory (HOME, else getpwuid, which Emscripten
// does not answer): without this the asset root does not open. OYMAP_* (OYMAP_ASSETS and the rest) pass as natively.
Module['preRun'] = Module['preRun'] || [];
Module['preRun'].push(function () {
    if (typeof process !== 'undefined' && process.env) {
        for (const name of Object.keys(process.env)) {
            if (name === 'HOME' || name === 'XDG_DATA_HOME' || name.startsWith('OYMAP_')) {
                ENV[name] = process.env[name];
            }
        }
    }
});
