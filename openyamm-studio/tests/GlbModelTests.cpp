// A Blender model as outdoor BModels (core/OutdoorGlb, `kind: model` with `from: {glb}`; DECISIONS.md H-44): triangles
// joined into convex faces where one picture runs on, slivers refused, and the box-with-an-arch fixture
// (tests/fixtures/glb/make_box_arch.py) built into a map with its textures, events and collision.
#include "core/OutdoorBuild.h"
#include "core/OutdoorGlb.h"
#include "core/Schema.h"

#include "game/FaceEnums.h"
#include "game/outdoor/OutdoorMapData.h"

#include <doctest/doctest.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Studio;

namespace
{
const std::filesystem::path GlbAssets = OPENYAMM_DEV_ASSETS_DIR;
const std::filesystem::path BoxArch = GlbAssets.parent_path() / "openyamm-studio" / "tests" / "fixtures" / "glb"
    / "box_arch.glb";

OutdoorGlbFace triangle(std::vector<std::array<double, 3>> points, std::vector<std::array<double, 2>> uvs,
    const std::string &material = "t14a01")
{
    OutdoorGlbFace face;
    face.points = points;
    face.exact = points;
    face.uvs = uvs;
    face.hasUvs = true;
    face.material = material;
    return face;
}

// A level square 0..256 split along its diagonal, its picture one texel to a unit on a 128 picture.
std::vector<OutdoorGlbFace> splitSquare(double shiftSecondU = 0.0)
{
    return {triangle({{0, 0, 0}, {256, 0, 0}, {256, 256, 0}}, {{0, 0}, {2, 0}, {2, -2}}),
        triangle({{0, 0, 0}, {256, 256, 0}, {0, 256, 0}}, {{0 + shiftSecondU, 0}, {2 + shiftSecondU, -2},
            {0 + shiftSecondU, -2}})};
}

std::vector<uint8_t> readFileBytes(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return std::vector<uint8_t>((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
}

Project gateProject(const std::filesystem::path &root, const std::string &structure)
{
    const std::vector<std::pair<std::string, std::string>> files = {
        {"project.yml", "format: 0\nid: glbtest\nname: GLB test\nworld: mm8\nkind: outdoor\nprofile: odm\n"
            "map_stats: {id: 9953, slots: []}\n"},
        {"plan.yml", "format: 0\nentrances:\n  - {id: entrance:start, space: zone:field, kind: arrival, facing: n}\n"
            "height_bands:\n  - {id: band:field, range: [576, 704]}\nspaces:\n  - {id: zone:field, kind: zone}\n"},
        {"sketch.yml", "format: 0\nheights:\n  bands:\n    - {band: band:field, polygon: [[0, 0], [128, 0], [128, "
            "128], [0, 128]]}\npoints:\n  - {id: entrance:start, at: [62, 66], facing: n}\nstructures:\n" + structure},
    };
    Project project;
    project.root = root;

    for (const auto &[name, text] : files)
    {
        ProjectFile file;
        file.name = name;
        file.text = text;
        file.document = YAML::Load(text);

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (file.name == kind.pName)
            {
                file.schema = kind.pSchema;
            }
        }

        project.files[file.name] = file;
    }

    return project;
}

std::filesystem::path freshFolder()
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_glb_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);
    std::filesystem::copy_file(BoxArch, root / "box_arch.glb");
    return root;
}
}

TEST_CASE("GLB: two triangles of one picture become one quad; a picture that does not run on keeps them apart")
{
    std::vector<OutdoorGlbFace> faces = splitSquare();
    joinOutdoorGlbFaces(faces);
    REQUIRE(faces.size() == 1);
    CHECK(faces[0].points.size() == 4);

    std::vector<OutdoorGlbFace> torn = splitSquare(0.5);
    joinOutdoorGlbFaces(torn);
    CHECK(torn.size() == 2);

    // Another material, another plane: not joined.
    std::vector<OutdoorGlbFace> other = splitSquare();
    other[1].material = "t06b01";
    joinOutdoorGlbFaces(other);
    CHECK(other.size() == 2);
    std::vector<OutdoorGlbFace> folded = splitSquare();
    folded[1].points[2] = {0, 256, 64};
    folded[1].exact[2] = folded[1].points[2];
    joinOutdoorGlbFaces(folded);
    CHECK(folded.size() == 2);

    // An L of three squares (six triangles) joins only as far as it stays convex.
    std::vector<OutdoorGlbFace> ell;

    for (const std::array<double, 2> &corner : std::vector<std::array<double, 2>>{{0, 0}, {256, 0}, {0, 256}})
    {
        const double x = corner[0];
        const double y = corner[1];
        ell.push_back(triangle({{x, y, 0}, {x + 256, y, 0}, {x + 256, y + 256, 0}},
            {{x / 128, -y / 128}, {(x + 256) / 128, -y / 128}, {(x + 256) / 128, -(y + 256) / 128}}));
        ell.push_back(triangle({{x, y, 0}, {x + 256, y + 256, 0}, {x, y + 256, 0}},
            {{x / 128, -y / 128}, {(x + 256) / 128, -(y + 256) / 128}, {x / 128, -(y + 256) / 128}}));
    }

    joinOutdoorGlbFaces(ell);
    CHECK(ell.size() >= 2);
    CHECK(ell.size() <= 3);
}

TEST_CASE("GLB: the box-with-an-arch fixture reads as two meshes of convex faces; slivers and tiny faces are refused")
{
    REQUIRE(std::filesystem::is_regular_file(BoxArch));
    std::vector<OutdoorGlbMesh> meshes;
    std::vector<std::string> errors;
    REQUIRE(readOutdoorGlb(BoxArch, OutdoorGlbOptions(), meshes, errors));
    REQUIRE(meshes.size() == 2);
    const auto gate = std::find_if(meshes.begin(), meshes.end(), [](const OutdoorGlbMesh &mesh)
    {
        return mesh.name == "Gate";
    });
    REQUIRE(gate != meshes.end());
    // 64 triangles from Blender's export; joined, fewer faces than triangles, quads and larger.
    CHECK(gate->faces.size() < gate->triangles);
    CHECK(std::any_of(gate->faces.begin(), gate->faces.end(), [](const OutdoorGlbFace &face)
    {
        return face.points.size() >= 4;
    }));

    // Blender's +Y up: the gate stands 768 high on the map's z, 128 thick along the map's y.
    double lowZ = 1.0e9;
    double highZ = -1.0e9;
    double lowY = 1.0e9;
    double highY = -1.0e9;

    for (const OutdoorGlbFace &face : gate->faces)
    {
        for (const std::array<double, 3> &point : face.points)
        {
            lowZ = std::min(lowZ, point[2]);
            highZ = std::max(highZ, point[2]);
            lowY = std::min(lowY, point[1]);
            highY = std::max(highY, point[1]);
        }
    }

    CHECK(lowZ == 0.0);
    CHECK(highZ == 768.0);
    CHECK(highY - lowY == 128.0);

    // With a least area over every face's, each is refused (eight named, the rest counted); with a sharpest corner
    // of 60 degrees, the arch's faces (corners of about 22 and 45 degrees round the arc) are slivers.
    OutdoorGlbOptions large;
    large.minArea = 1.0e7;
    errors.clear();
    CHECK_FALSE(readOutdoorGlb(BoxArch, large, meshes, errors));
    CHECK(std::any_of(errors.begin(), errors.end(), [](const std::string &error)
    {
        return error.find("under the least") != std::string::npos;
    }));
    CHECK(std::any_of(errors.begin(), errors.end(), [](const std::string &error)
    {
        return error.find("more faces refused") != std::string::npos;
    }));

    OutdoorGlbOptions sharp;
    sharp.minAngleDegrees = 60.0;
    errors.clear();
    CHECK_FALSE(readOutdoorGlb(BoxArch, sharp, meshes, errors));
    CHECK(std::any_of(errors.begin(), errors.end(), [](const std::string &error)
    {
        return error.find("is a sliver") != std::string::npos;
    }));

    // The defaults take the fixture as it is.
    errors.clear();
    CHECK(readOutdoorGlb(BoxArch, OutdoorGlbOptions(), meshes, errors));

    OutdoorGlbOptions budget;
    budget.faceBudget = 4;
    errors.clear();
    CHECK_FALSE(readOutdoorGlb(BoxArch, budget, meshes, errors));
    CHECK(std::any_of(errors.begin(), errors.end(), [](const std::string &error)
    {
        return error.find("over the budget of 4") != std::string::npos;
    }));
}

TEST_CASE("GLB: kind model from a glb builds its meshes as BModels with the world's textures, events and collision")
{
    if (!std::filesystem::is_directory(GlbAssets / "engine"))
    {
        MESSAGE("no asset root: skipped");
        return;
    }

    const std::filesystem::path root = freshFolder();
    const Project project = gateProject(root, "  - id: thing:gate\n    kind: model\n    from: {glb: box_arch.glb}\n"
        "    at: [64, 60]\n    title: The Gate\n    click: [Gate]\n    hint: A box\n"
        "    textures:\n      blocker: {texture: t14a01, invisible: true}\n");
    BuildOptions options;
    options.outputDirectory = root / "build";
    options.assetRoot = GlbAssets;
    BuildResult result;
    const bool built = buildOutdoorProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built);
    const std::optional<Game::OutdoorMapData> map =
        Game::OutdoorMapDataLoader().loadFromBytes(readFileBytes(root / "build" / "glbtest.odm"));
    REQUIRE(map.has_value());
    std::vector<const Game::OutdoorBModel *> models;

    for (const Game::OutdoorBModel &model : map->bmodels)
    {
        if (model.name == "thing:gate")
        {
            models.push_back(&model);
        }
    }

    // One BModel per mesh, both named after the structure, the mesh in the second name.
    REQUIRE(models.size() == 2);
    const auto byMesh = [&models](const char *pMesh)
    {
        return *std::find_if(models.begin(), models.end(), [pMesh](const Game::OutdoorBModel *pModel)
        {
            return pModel->secondaryName == pMesh;
        });
    };
    const Game::OutdoorBModel &gate = *byMesh("Gate");
    const Game::OutdoorBModel &box = *byMesh("Box");
    const uint32_t invisible = Game::faceAttributeBit(Game::FaceAttribute::Invisible);
    const uint32_t untouchable = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    const uint32_t clickable = Game::faceAttributeBit(Game::FaceAttribute::Clickable);
    std::set<std::string> textures;

    for (const Game::OutdoorBModelFace &face : gate.faces)
    {
        textures.insert(face.textureName);
        // Convex polygons of up to 20 corners, solid, the click's event.
        CHECK(face.vertexIndices.size() >= 3);
        CHECK(face.vertexIndices.size() <= 20);
        CHECK((face.attributes & untouchable) == 0);
        CHECK((face.attributes & invisible) == 0);
        CHECK((face.attributes & clickable) != 0);
    }

    CHECK(textures == std::set<std::string>{"t14a01", "t06b01"});
    CHECK(std::any_of(gate.faces.begin(), gate.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.vertexIndices.size() >= 4;
    }));
    // The gate stands with its foot on the land at 640, 768 high; its middle at cell (64, 60) with the box's: the
    // two meshes' middle is at (0, 2048).
    CHECK(gate.minZ == 640);
    CHECK(gate.maxZ == 640 + 768);

    // The box: `t14a01.001` is t14a01; its top (material `blocker`) is not drawn and stays solid; it says the hint.
    size_t hidden = 0;

    for (const Game::OutdoorBModelFace &face : box.faces)
    {
        CHECK(face.textureName == "t14a01");
        CHECK((face.attributes & untouchable) == 0);
        hidden += (face.attributes & invisible) != 0 ? 1 : 0;
        CHECK(face.cogTriggeredNumber != gate.faces.front().cogTriggeredNumber);
        CHECK(face.cogTriggeredNumber != 0);
    }

    CHECK(hidden == 1);

    // Texels: inside the format, on the picture's own grid (the fixture lays 128 units a picture).
    for (const Game::OutdoorBModelFace &face : gate.faces)
    {
        for (const int16_t texel : face.textureUs)
        {
            CHECK(texel > -32768);
            CHECK(texel < 32767);
        }
    }

    // A material the world has no texture for is refused by the build.
    const Project wrong = gateProject(root, "  - id: thing:gate\n    kind: model\n    from: {glb: box_arch.glb}\n"
        "    at: [64, 60]\n");
    BuildResult refused;
    CHECK_FALSE(buildOutdoorProject(wrong, options, refused));
    CHECK(std::any_of(refused.issues.begin(), refused.issues.end(), [](const ProjectIssue &issue)
    {
        return issue.message.find("blocker") != std::string::npos;
    }));
    std::filesystem::remove_all(root);
}
