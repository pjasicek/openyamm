#pragma once

#include "core/Project.h"

#include <vector>

namespace OpenYAMM::Studio
{
// Words on the wrong kind (S5_BROWSER_EDITOR.md 2.4.2 and 3.8): an object whose schema names its kind word
// (`x-discriminator: {property, default}`) and whose properties say the kinds they apply to (`x-kinds: [...]`) is
// checked as the form reads it: a word written on an object of a kind it does not apply to is silently unused by the
// lowering, so it is reported as a warning ("word X does not apply to kind Y"), code `kind`. Warnings never stop a
// build. The same annotations drive the inspector, so the kind table is checked by every validation.
void checkWordKinds(const ProjectFile &file, std::vector<ProjectIssue> &issues);
}
