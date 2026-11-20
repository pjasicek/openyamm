/* Included before each of musl's sources (-include): every symbol they define gets an oy_musl_ name, so that they
 * link beside the C library's own math functions (glibc natively, Emscripten's musl in the wasm build) without a
 * clash. core/CoreMath.h calls them by these names. Not part of musl. */
#ifndef OY_MUSL_NAMES_H
#define OY_MUSL_NAMES_H

/* musl's internal features.h: symbols shared between musl's files only. */
#define hidden __attribute__((__visibility__("hidden")))

#define sin oy_musl_sin
#define cos oy_musl_cos
#define tan oy_musl_tan
#define asin oy_musl_asin
#define acos oy_musl_acos
#define atan oy_musl_atan
#define atan2 oy_musl_atan2
#define hypot oy_musl_hypot
#define cbrt oy_musl_cbrt
#define pow oy_musl_pow
#define scalbn oy_musl_scalbn

#define __sin oy_musl___sin
#define __cos oy_musl___cos
#define __tan oy_musl___tan
#define __rem_pio2 oy_musl___rem_pio2
#define __rem_pio2_large oy_musl___rem_pio2_large
#define __math_oflow oy_musl___math_oflow
#define __math_uflow oy_musl___math_uflow
#define __math_xflow oy_musl___math_xflow
#define __math_invalid oy_musl___math_invalid
#define __math_divzero oy_musl___math_divzero
#define __pow_log_data oy_musl___pow_log_data
#define __exp_data oy_musl___exp_data

#endif
