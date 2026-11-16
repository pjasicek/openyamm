/* Stands in for <math.h> when musl's sources are compiled: the declarations they need and nothing else, the same
 * on every target (glibc's own <math.h> declares __sin, __cos ... with other signatures). The functions declared
 * here and not compiled from src/ (sqrt, fabs, floor) are exact in every C library. Not part of musl. */
#ifndef OY_MUSL_MATH_H
#define OY_MUSL_MATH_H

typedef double double_t;
typedef float float_t;

#define INFINITY __builtin_inff()
#define NAN __builtin_nanf("")
#define HUGE_VAL __builtin_huge_val()
#define isnan(x) __builtin_isnan(x)
#define isinf(x) __builtin_isinf(x)
#define signbit(x) __builtin_signbit(x)

double sqrt(double);
double fabs(double);
double floor(double);

double sin(double);
double cos(double);
double tan(double);
double asin(double);
double acos(double);
double atan(double);
double atan2(double, double);
double hypot(double, double);
double cbrt(double);
double pow(double, double);
double scalbn(double, int);

#endif
