#!/usr/bin/env python3
"""Copy a ru_local v89/v90 save with an explicit branch-format tag.

The branch reused upstream version numbers for a different binary layout. Only
run this on saves written by ru_local, never on ordinary upstream v89/v90 saves.
The engine imports the tagged copy and writes its current format on the next save.
"""

import argparse
from pathlib import Path
import struct

SOURCE_MAGIC = b"OYSAVE1\0"
IMPORT_MAGIC = b"OYRULOC\0"


def tagged_copy(data):
    if len(data) < 12 or data[:8] != SOURCE_MAGIC:
        raise ValueError("Expected an unmodified OpenYAMM save header")
    version, = struct.unpack_from("<I", data, 8)
    if version not in (89, 90):
        raise ValueError(f"Expected a ru_local version 89 or 90 save, got {version}")
    return IMPORT_MAGIC + data[8:]


def migrate(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError("The output must be a new path; the original save is preserved")
    data = tagged_copy(source.read_bytes())
    with destination.open("xb") as output:
        output.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    try:
        migrate(arguments.source, arguments.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Created tagged import copy: {arguments.destination}")


if __name__ == "__main__":
    main()
