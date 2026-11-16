#pragma once

#include <cmath>

// The core's math functions whose results the C libraries do not agree on. The native core (glibc) and the
// WebAssembly core (Emscripten's musl) must write the same bytes (PLAN.md section 3), and glibc and musl differ by
// an ulp on a few percent of inputs to hypot, sin, cos, tan, atan2 and cbrt (S5-0 spike 6): the core calls musl's
// own sources, compiled into it on every target (third_party/musl_math), through these names. Lowering code uses
// oy::sin and the rest, never std::sin. Exact functions stay std:: (sqrt, floor, ceil, round, lround, fmod,
// remainder, abs): IEEE fixes their results. These take and give doubles only; the compiler does not fold them
// into constants either (it folds std::sin(constant) with its own library).

extern "C"
{
double oy_musl_sin(double x);
double oy_musl_cos(double x);
double oy_musl_tan(double x);
double oy_musl_asin(double x);
double oy_musl_acos(double x);
double oy_musl_atan(double x);
double oy_musl_atan2(double y, double x);
double oy_musl_hypot(double x, double y);
double oy_musl_cbrt(double x);
double oy_musl_pow(double x, double y);
}

namespace oy
{
inline double sin(double x)
{
    return oy_musl_sin(x);
}

inline double cos(double x)
{
    return oy_musl_cos(x);
}

inline double tan(double x)
{
    return oy_musl_tan(x);
}

inline double asin(double x)
{
    return oy_musl_asin(x);
}

inline double acos(double x)
{
    return oy_musl_acos(x);
}

inline double atan(double x)
{
    return oy_musl_atan(x);
}

inline double atan2(double y, double x)
{
    return oy_musl_atan2(y, x);
}

inline double hypot(double x, double y)
{
    return oy_musl_hypot(x, y);
}

// The length of (x, y, z). The standard libraries compute std::hypot of three differently (libstdc++ divides by the
// largest, libc++ scales only near overflow); this is libstdc++'s formula, which the native core used before.
inline double hypot(double x, double y, double z)
{
    x = std::fabs(x);
    y = std::fabs(y);
    z = std::fabs(z);
    const double largest = x < y ? (y < z ? z : y) : (x < z ? z : x);

    if (largest == 0.0)
    {
        return 0.0;
    }

    const double a = x / largest;
    const double b = y / largest;
    const double c = z / largest;
    return largest * std::sqrt(a * a + b * b + c * c);
}

inline double cbrt(double x)
{
    return oy_musl_cbrt(x);
}

inline double pow(double x, double y)
{
    return oy_musl_pow(x, y);
}
}
