
# Engine Architecture

OpenYAMM is divided into four major layers.

engine/
game/
editor/
tools/

---

# Engine Layer

Platform-independent engine systems.

Responsibilities:

* window management
* input
* rendering
* audio
* filesystem
* resource management
* logging

---

# Game Layer

Game-specific logic.

Examples:

* combat
* monsters
* items
* spells
* quests
* maps

Gameplay data is loaded from original TXT tables.

---

# Editor Layer

Content creation tools.

Examples:

* map editor
* asset browser
* data editors

Editor must reuse runtime systems.

---

# Tools Layer

Offline utilities.

Examples:

* asset packager
* video converters
* archive utilities
