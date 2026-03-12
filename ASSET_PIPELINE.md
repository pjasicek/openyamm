
# Asset Pipeline

OpenYAMM keeps most original data formats unchanged.

Only container formats and video codecs are replaced.

---

# Original Assets

Stored in:

data/

Structure example:

data/
    Anims/
    Data/
    Music/

These contain files extracted from original MM8 LOD archives.

---

# Container Conversion

Original:

LOD archives

OpenYAMM:

ZIP archives

---

# Video Conversion

Original formats:

SMK (looping animations)
BINK (cutscenes)

Converted to:

OGV

---

# Audio

Sound effects:

WAV

Music:

MP3 / FLAC

---

# Gameplay Tables

Original TXT tables remain unchanged.

They are tab-separated.

Examples:

items.txt
monsters.txt
spells.txt

---

# Asset Packaging

Assets are packed into ZIP archives.

Example:

assets/base.zip

Runtime loads ZIP archives instead of LOD files.

For development, assets are loaded directly from `assets_dev/` on the plain filesystem for fast iteration.

Example:

assets_dev/Anims/
assets_dev/Data/
assets_dev/Music/
