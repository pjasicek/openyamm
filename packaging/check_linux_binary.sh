#!/usr/bin/env bash
# Checks that Linux release executables run on every supported distribution: they may need only the C library up to
# glibc $OPENYAMM_MAX_GLIBC (default 2.35, Ubuntu 22.04 and Debian 12 or newer) and no libstdc++. SDL loads X11,
# Wayland, the audio servers and the GPU drivers at runtime, and the updater loads libcurl.
# Usage: check_linux_binary.sh EXECUTABLE...
set -euo pipefail

max_glibc="${OPENYAMM_MAX_GLIBC:-2.35}"
allowed='^(libc\.so\.6|libm\.so\.6|libdl\.so\.2|libpthread\.so\.0|librt\.so\.1|ld-linux-x86-64\.so\.2)$'
status=0

for binary in "$@"; do
    needed="$(objdump -p "$binary" | awk '$1 == "NEEDED" { print $2 }')"
    while read -r library; do
        if [ -n "$library" ] && ! [[ "$library" =~ $allowed ]]; then
            printf 'error: %s needs %s\n' "$binary" "$library" >&2
            status=1
        fi
    done <<< "$needed"

    symbols="$(objdump -T "$binary")"
    newest="$(grep -o 'GLIBC_[0-9.]*' <<< "$symbols" | sed 's/^GLIBC_//' | sort -uV | tail -n 1)"
    if [ -n "$newest" ] && [ "$(printf '%s\n%s\n' "$newest" "$max_glibc" | sort -V | tail -n 1)" != "$max_glibc" ]; then
        printf 'error: %s needs glibc %s, newer than %s:\n' "$binary" "$newest" "$max_glibc" >&2
        grep "GLIBC_$newest" <<< "$symbols" | awk '{ print "  " $NF }' >&2
        status=1
    fi
    if grep -Eq 'GLIBCXX_|CXXABI_' <<< "$symbols"; then
        printf 'error: %s links libstdc++ dynamically (configure with -DOPENYAMM_STATIC_LIBSTDCXX=ON)\n' "$binary" >&2
        status=1
    fi
    printf '%s: needs %s, glibc %s\n' "$binary" "$(tr '\n' ' ' <<< "$needed")" "${newest:-none}"
done

exit "$status"
