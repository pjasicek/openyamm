
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

Example:

class Monster
{
public:
    void attack();

private:
    int m_health;
    Weapon* m_pWeapon;
};
