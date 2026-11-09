# Quad Remesher trial 01 — prepared, not executed

The user installed/activated the trial. Source is loaded and selected in Blender scene
`MM6 Goblin - Quad Remesher Trial 01`. Press **Remesh It** in **N > Quad Remesh**.
Settings are already configured: 9,000 target quads, adaptive size 50%, adaptive count off,
vertex density guide on, symmetry off. The source is the dense repaired main mesh; separate back
plates are retained and their tiny separate rivets are hidden for later baking. `density_guide.png`
is a diagnostic color image, not a texture. Red means denser, cyan means coarser.

The checkpoint `prepared_trial.blend` is a saved copy of the working session. Preparation does not
run the licensed remesher. Standard license restrictions require human interaction inside Blender
for the remesh operation. No other operation or purchase is requested.

After the user runs it, measure output quads/triangles and compare face, fingers, spikes and skirt
allocation against the source. Inspect joint topology before rigging. This is a bounded density-guided
trial; simplifying the skirt and baking shallow details remain necessary. 9K quads roughly correspond
to 18K triangles for the main mesh; actual topology plus plates/weapon determines the final count.

## First launch failure and dependency repair

User reported `Remeshing failed! (returned without preogressfile - 0)` after clicking Remesh It.
The FBX and settings were exported correctly. `ldd` run from inside the active Blender process found
`libxml2.so.2 => not found`. Ubuntu 26.04 supplies libxml2.so.16, which is a different ABI.
Installed actual ABI-2 libxml2 and its ICU-74 dependencies from verified Ubuntu Noble packages into
Quad Remesher's private engine directory. Its existing $ORIGIN RPATH resolves these without altering
system libraries, system apt repositories, plugin code or engine binaries. See dependency_repair.json.

Post-fix `ldd -r` from inside Blender returns 0 with no missing libraries or undefined symbols;
see dependency_verification.json. The actual remesh still requires a new user click and has not yet
been proven successful. Source selection and the prepared settings remain in place. A reinstall of
the external remeshing engine may remove these private dependencies.

## Second attempt: diagnostic capture pending

The repaired engine now writes `_UserLog_Remesher.txt` with "Settings file read successfully!";
license helper logs are created, but no progress/output FBX appears. Both main engine and license helper
resolve their linked libraries/symbols. User confirms License Manager says active trial, 30 days remaining.
Do not claim this is an activation failure or that the asset is at fault: current logs do not explain it.

Temporary loader diagnostics are enabled in the live Blender process: LD_DEBUG=libs,
LD_DEBUG_OUTPUT=/tmp/openyamm-qr-loader. The next user-triggered remesh will produce per-process logs.
Previous environment is held in bpy.openyamm_qr_diagnostic_previous_env; restore it after collecting
that attempt. No engine binary or plugin code was modified. Do not run proprietary engine directly.

## Confirmed Linux signal-launch failure

The detailed loader logs were inconclusive. A one-attempt strace wrapper caused a separate
`HostApp com failed. (FERRCNT0/3)` because the parent was strace instead of Blender; that wrapper
was removed and is not a valid normal-launch reproduction. Temporary loader logging was also restored.

Direct inspection from the live Blender process found three earlier normal-launch `xremesh` jobs in
`t (tracing stop)` with `TracerPid` equal to Blender and zombie license-helper children. The bridge had
already reported failure and discarded its process handles. This matches the firsthand Linux reproduction
at https://blenderartists.org/t/help-to-reproduce-an-issue-with-quad-remesher-on-linux/1629871/2 .

Patched only the GPL bridge's `qr_exe.py` launch: block SIGCHLD in the calling thread around Popen so
the remesher inherits that mask, then immediately restore Blender's original mask. Direct launch preserves
Blender as the parent. The proprietary engine and license checks are unchanged. Original bridge file is
backed up beside it as `qr_exe.py.before_openyamm_sigchld`; exact diff and hashes are retained here.
A harmless child launched through the actual patched function confirms blocked SIGCHLD, correct parent,
normal child exit and restored Blender mask. The live module was reloaded; no Blender restart needed.
Only the three confirmed suspended failed jobs were killed/reaped. Actual remesh result remains pending.
