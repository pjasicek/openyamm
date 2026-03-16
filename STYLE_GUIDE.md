
# Coding Style Guide

Max line length: 120 characters.

Indentation: 4 spaces.

Braces always appear on new lines.

Example:

if (value > 0)
{
    doSomething();
}

Naming:

Classes: CamelCase
Methods: camelCase
Variables: camelCase

Member variables:

m_variable

Pointers:

pPointer

Member pointers:

m_pPointer

Type declarations:

Prefer explicit types over `auto`.

Use `auto` only when it improves readability or avoids noisy type repetition.

Good examples:

auto it = items.begin();
auto result = visitor(node);

Do not use `[[nodiscard]]`.

Prefer unqualified standard integer and size types:

uint32_t
int16_t
size_t

Avoid:

std::uint32_t
std::int16_t
std::size_t

Use `static_cast` only when it is actually required for correctness.
Do not add it by default for routine arithmetic or obvious conversions.

Example:

class Monster
{
public:
    void attack();

private:
    int m_health;
    Weapon* m_pWeapon;
};
