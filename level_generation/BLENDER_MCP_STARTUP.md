# Starting Blender MCP without manual setup

The agent can launch Blender and connect without asking the driver to open the application or press Connect.
This was verified on this workstation on 2026-09-07: the driver quit Blender, the agent launched `blender`, and the
installed add-on automatically started its server on port **9876**. Scene inspection, Python execution and a viewport
screenshot then succeeded. Leave a working Blender instance running for subsequent map work.

## Normal startup procedure

1. Try Blender MCP scene inspection first. If it responds, reuse that instance and preserve its existing scenes.
2. If it does not respond, check whether the actual Blender application is running. Python processes named
   `blender-mcp` are MCP clients/bridges, not proof that Blender's GUI is open. If Blender is still starting or rendering,
   allow it time to respond; do not launch a competing instance on the same port.
3. When Blender is closed, launch its normal GUI from the terminal:

   ```sh
   blender
   ```

   Use the execution tool's GUI/display permissions as required. Keep the process/session alive, retain its output
   for diagnosis, and let the enabled add-on start the server. Do not stop authorized work to request a manual Connect
   click when the agent can launch and verify the application itself. Actual permission restrictions still apply.
4. Allow startup to finish, then call MCP scene inspection again. The first request after a restart can encounter a
   stale connection from the previous process. In the verified run it returned **Connection closed before receiving
   any data**; one subsequent request connected successfully. Retry once before treating that specific error as a
   startup failure. Repeated failures need diagnosis, not an unbounded retry loop or repeated Blender launches.
5. Verify scene inspection, a short read-only Python call and a viewport screenshot. Confirm the screenshot actually
   contains the viewport. Record the active scene and whether it is a default scene or an already loaded project.
6. Load or create the intended project after checking existing scene ownership. A responding default cube scene proves
   the connection, not that the dungeon or outdoor project has been restored. Preserve existing unsaved work.

Through MCP `execute_blender_code`, a small connection check is:

```python
import bpy

server = getattr(bpy.types, "blendermcp_server", None)
print({
    "blender": bpy.app.version_string,
    "gui": not bpy.app.background,
    "scene": bpy.context.scene.name,
    "server_running": getattr(server, "running", False),
    "port": getattr(server, "port", None),
    "auto_start": getattr(bpy.context.scene, "blendermcp_auto_start_server", None),
})
```

Pass the user's actual request verbatim in the MCP tools' `user_prompt` field. Use their scene-inspection and viewport
screenshot tools as well as Python execution; a listening socket alone does not prove commands or screenshots work.

## Installed behavior and limits

The tested installation is Blender **5.2.1 LTS**, launched through `/snap/bin/blender`. Its enabled add-on module is
`addon`, with source at `/home/pjasicek/.config/blender/5.2/scripts/addons/addon.py`. These are observations about this
machine, not portable installation paths to assume after an upgrade. Inspect the current installation if they change.

The installed add-on's `register()` starts `BlenderMCPServer` when `blendermcp_auto_start_server` is enabled; that
option was enabled in the fresh-launch test. The default server is local, on port 9876. The UI's Connect action invokes
`bpy.ops.blendermcp.start_server()`. No add-on modification or preferences change was needed for the verified launch.

**Use a GUI process for MCP.** This installed add-on explicitly refuses to start its server under `blender -b` or
`--background`, because its command processing needs the GUI event loop. Background Blender remains appropriate for
standalone scripts such as packed-source verification or batch rendering; it is not the interactive MCP server.

If a physical display is unavailable, the installed add-on suggests `xvfb-run -a blender`: a normal GUI process on a
virtual display, without `-b`. This is an alternative requiring display/tool availability and separate verification;
the successful startup test described above used the normal desktop GUI.

If startup fails, inspect the launch output, add-on enablement/auto-start setting, port ownership and MCP response.
Do not reinstall the add-on, overwrite preferences, kill unrelated Blender processes or restart a busy scene as the
first recovery step. Report an actual missing prerequisite or permission block specifically if one remains.

Keep project sources saved, preserve unrelated scenes, and avoid disconnecting the add-on at the end of a task.
This is on-demand agent startup, not an installed login service or crash-recovery daemon.
