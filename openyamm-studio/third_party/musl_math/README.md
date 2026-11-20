# musl's math functions

The double-precision functions the studio's core calls whose results the C libraries do not agree on (glibc and
Emscripten's musl differ by an ulp on a few percent of inputs), compiled into the core on every target so that the
native and the WebAssembly core compute the same bits (S5-0 spike 6). `core/CoreMath.h` calls them as `oy::sin`,
`oy::cos` and so on.

- From musl 1.2.5 as Emscripten 4.0.10 ships it (`emsdk/upstream/emscripten/system/lib/libc/musl`): `src/` holds
  `src/math/*.c` and `*.h`, `src/internal/libm.h` and `arch/generic/fp_arch.h`, unchanged.
- Licence: MIT, `COPYRIGHT` (musl's).
- `include/` is ours: a `<math.h>` with only what the sources need, and `oy_musl_names.h`, included before each
  source, which gives every symbol an `oy_musl_` name so that they link beside the C library's own.
- Compiled with `-fno-builtin -ffp-contract=off` and without `__FP_FAST_FMA` (pow would use fused multiply-adds on
  a target that has them).
- To add a function: copy its source and those it calls from the same musl, add its names to `oy_musl_names.h`
  and `include/math.h`, the file to `CMakeLists.txt` (`OYMAP_MUSL_MATH_FILES`), and a wrapper to `core/CoreMath.h`.
