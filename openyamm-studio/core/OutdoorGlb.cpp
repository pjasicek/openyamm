#include "core/OutdoorGlb.h"

#include "core/CoreMath.h"


#include <cgltf/cgltf.h>

#include <algorithm>
#include <cmath>
#include <map>
#include <memory>
#include <optional>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
using Point3 = std::array<double, 3>;
using Uv = std::array<double, 2>;

// Corners of a face: the format holds 20.
constexpr size_t MostCorners = 20;
// Two faces lie in one plane when their normals agree this well and every corner of one lies this near the other's
// plane (map units: the corners are whole units, so a large face's rounded corners stand off its plane by a little).
constexpr double SamePlaneDot = 0.9999;
constexpr double SamePlaneDistance = 1.0;
// One picture runs on across an edge when the UVs agree this well (a hundredth of a texel on a 1024 picture).
constexpr double SameUv = 1.0e-5;
// A corner predicted by the face's picture this near its own UV.
constexpr double PredictedUv = 1.0e-3;
// How many refused faces are named before the rest are counted.
constexpr size_t NamedRefusals = 8;
constexpr double Pi = 3.14159265358979323846;

Point3 minus(const Point3 &a, const Point3 &b)
{
    return {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
}

Point3 cross(const Point3 &a, const Point3 &b)
{
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}

double dot(const Point3 &a, const Point3 &b)
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

double length(const Point3 &a)
{
    return std::sqrt(dot(a, a));
}

// Newell's normal, its length twice the polygon's area.
Point3 areaNormal(const std::vector<Point3> &points)
{
    Point3 normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point3 &from = points[index];
        const Point3 &to = points[(index + 1) % points.size()];
        normal[0] += (from[1] - to[1]) * (from[2] + to[2]);
        normal[1] += (from[2] - to[2]) * (from[0] + to[0]);
        normal[2] += (from[0] - to[0]) * (from[1] + to[1]);
    }

    return normal;
}

double areaOf(const std::vector<Point3> &points)
{
    return length(areaNormal(points)) * 0.5;
}

Point3 unit(const Point3 &vector)
{
    const double size = length(vector);
    return size > 0.0 ? Point3{vector[0] / size, vector[1] / size, vector[2] / size} : Point3{0.0, 0.0, 0.0};
}

// Whether the polygon turns one way at every corner (a corner on a straight line allowed), seen along its normal.
bool convex(const std::vector<Point3> &points)
{
    const Point3 normal = unit(areaNormal(points));

    if (length(normal) == 0.0)
    {
        return false;
    }

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point3 &previous = points[(index + points.size() - 1) % points.size()];
        const Point3 &corner = points[index];
        const Point3 &next = points[(index + 1) % points.size()];
        const Point3 in = minus(corner, previous);
        const Point3 out = minus(next, corner);
        const double turn = dot(cross(in, out), normal);

        // A turn the other way by more than a hair (relative to the edges' lengths) makes it concave.
        if (turn < -1.0e-6 * length(in) * length(out))
        {
            return false;
        }
    }

    return true;
}

// The sharpest corner of a polygon, degrees (a corner on a straight line counts as 180).
double sharpestCorner(const std::vector<Point3> &points)
{
    double sharpest = 180.0;

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point3 toPrevious = minus(points[(index + points.size() - 1) % points.size()], points[index]);
        const Point3 toNext = minus(points[(index + 1) % points.size()], points[index]);
        const double lengths = length(toPrevious) * length(toNext);

        if (lengths <= 0.0)
        {
            return 0.0;
        }

        const double cosine = std::clamp(dot(toPrevious, toNext) / lengths, -1.0, 1.0);
        sharpest = std::min(sharpest, std::acos(cosine) * 180.0 / Pi);
    }

    return sharpest;
}

// The UV of a point in a face's plane by the affine map its corners' UVs make (from the three corners spanning the
// most area); nullopt when they span none.
struct UvMap
{
    Point3 origin = {};
    Point3 alongU = {};
    Point3 alongV = {};
    Uv originUv = {};
    std::array<double, 4> inverse = {};
    Uv du = {};
    Uv dv = {};
};

std::optional<UvMap> uvMapOf(const OutdoorGlbFace &face)
{
    size_t best[3] = {0, 1, 2};
    double bestArea = 0.0;

    for (size_t b = 1; b < face.exact.size(); ++b)
    {
        for (size_t c = b + 1; c < face.exact.size(); ++c)
        {
            const double area = length(cross(minus(face.exact[b], face.exact[0]),
                minus(face.exact[c], face.exact[0])));

            if (area > bestArea)
            {
                bestArea = area;
                best[1] = b;
                best[2] = c;
            }
        }
    }

    if (bestArea <= 0.0)
    {
        return std::nullopt;
    }

    UvMap map;
    map.origin = face.exact[best[0]];
    map.originUv = face.uvs[best[0]];
    map.alongU = minus(face.exact[best[1]], map.origin);
    map.alongV = minus(face.exact[best[2]], map.origin);
    // Solve p - origin = s alongU + t alongV by the normal equations.
    const double a = dot(map.alongU, map.alongU);
    const double b = dot(map.alongU, map.alongV);
    const double d = dot(map.alongV, map.alongV);
    const double determinant = a * d - b * b;

    if (std::fabs(determinant) <= 1.0e-12)
    {
        return std::nullopt;
    }

    map.inverse = {d / determinant, -b / determinant, -b / determinant, a / determinant};
    map.du = {face.uvs[best[1]][0] - map.originUv[0], face.uvs[best[1]][1] - map.originUv[1]};
    map.dv = {face.uvs[best[2]][0] - map.originUv[0], face.uvs[best[2]][1] - map.originUv[1]};
    return map;
}

Uv predictedUv(const UvMap &map, const Point3 &point)
{
    const Point3 offset = minus(point, map.origin);
    const double alongU = dot(offset, map.alongU);
    const double alongV = dot(offset, map.alongV);
    const double s = map.inverse[0] * alongU + map.inverse[1] * alongV;
    const double t = map.inverse[2] * alongU + map.inverse[3] * alongV;
    return {map.originUv[0] + s * map.du[0] + t * map.dv[0], map.originUv[1] + s * map.du[1] + t * map.dv[1]};
}

bool sameUv(const Uv &a, const Uv &b, double tolerance)
{
    return std::fabs(a[0] - b[0]) <= tolerance && std::fabs(a[1] - b[1]) <= tolerance;
}

// `second` joined to `first` across the edge first[edge] -> first[edge + 1] (second's own edge the other way), or
// nullopt when the two do not make one face.
std::optional<OutdoorGlbFace> joined(const OutdoorGlbFace &first, size_t edge, const OutdoorGlbFace &second)
{
    if (first.material != second.material || first.hasUvs != second.hasUvs
        || first.points.size() + second.points.size() - 2 > MostCorners)
    {
        return std::nullopt;
    }

    const Point3 &a = first.points[edge];
    const Point3 &b = first.points[(edge + 1) % first.points.size()];
    size_t atA = second.points.size();

    for (size_t index = 0; index < second.points.size(); ++index)
    {
        if (second.points[index] == b && second.points[(index + 1) % second.points.size()] == a)
        {
            atA = (index + 1) % second.points.size();
        }
    }

    if (atA == second.points.size())
    {
        return std::nullopt;
    }

    const Point3 normal = unit(areaNormal(first.points));
    const Point3 otherNormal = unit(areaNormal(second.points));

    if (dot(normal, otherNormal) < SamePlaneDot)
    {
        return std::nullopt;
    }

    for (const Point3 &point : second.points)
    {
        if (std::fabs(dot(minus(point, a), normal)) > SamePlaneDistance)
        {
            return std::nullopt;
        }
    }

    const size_t atB = (atA + second.points.size() - 1) % second.points.size();

    if (first.hasUvs)
    {
        const std::optional<UvMap> map = uvMapOf(first);

        if (!map || !sameUv(second.uvs[atA], first.uvs[edge], SameUv)
            || !sameUv(second.uvs[atB], first.uvs[(edge + 1) % first.points.size()], SameUv))
        {
            return std::nullopt;
        }

        for (size_t index = 0; index < second.points.size(); ++index)
        {
            if (!sameUv(predictedUv(*map, second.exact[index]), second.uvs[index], PredictedUv))
            {
                return std::nullopt;
            }
        }
    }

    // First's corners up to a, then second's corners after a up to before b, then first's from b on.
    OutdoorGlbFace face;
    face.material = first.material;
    face.hasUvs = first.hasUvs;

    const auto take = [&face](const OutdoorGlbFace &from, size_t index)
    {
        face.points.push_back(from.points[index]);
        face.exact.push_back(from.exact[index]);
        face.uvs.push_back(from.uvs[index]);
    };

    for (size_t index = 0; index <= edge; ++index)
    {
        take(first, index);
    }

    for (size_t index = (atA + 1) % second.points.size(); index != atB; index = (index + 1) % second.points.size())
    {
        take(second, index);
    }

    for (size_t index = edge + 1; index < first.points.size(); ++index)
    {
        take(first, index);
    }

    if (!convex(face.points))
    {
        return std::nullopt;
    }

    return face;
}

std::string pointText(const Point3 &point)
{
    std::ostringstream text;
    text << "[" << std::lround(point[0]) << ", " << std::lround(point[1]) << ", " << std::lround(point[2]) << "]";
    return text.str();
}

Point3 middleOf(const std::vector<Point3> &points)
{
    Point3 middle = {0.0, 0.0, 0.0};

    for (const Point3 &point : points)
    {
        middle = {middle[0] + point[0], middle[1] + point[1], middle[2] + point[2]};
    }

    const double count = static_cast<double>(points.size());
    return {middle[0] / count, middle[1] / count, middle[2] / count};
}

const cgltf_accessor *attributeOf(const cgltf_primitive &primitive, cgltf_attribute_type type, int index)
{
    for (size_t attribute = 0; attribute < primitive.attributes_count; ++attribute)
    {
        if (primitive.attributes[attribute].type == type && primitive.attributes[attribute].index == index)
        {
            return primitive.attributes[attribute].data;
        }
    }

    return nullptr;
}

// One face from corners read from the file, rounded to whole map units; repeated corners after rounding go.
void addFace(OutdoorGlbMesh &mesh, const std::vector<Point3> &points, const std::vector<Uv> &uvs, bool hasUvs,
    const std::string &material)
{
    OutdoorGlbFace face;
    face.material = material;
    face.hasUvs = hasUvs;

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point3 rounded = {std::round(points[index][0]), std::round(points[index][1]),
            std::round(points[index][2])};

        if (!face.points.empty() && face.points.back() == rounded)
        {
            continue;
        }

        face.points.push_back(rounded);
        face.exact.push_back(points[index]);
        face.uvs.push_back(uvs[index]);
    }

    while (face.points.size() > 1 && face.points.front() == face.points.back())
    {
        face.points.pop_back();
        face.exact.pop_back();
        face.uvs.pop_back();
    }

    if (face.points.size() < 3 || areaOf(face.points) <= 0.0)
    {
        ++mesh.dropped;
        return;
    }

    mesh.faces.push_back(std::move(face));
}
}

void joinOutdoorGlbFaces(std::vector<OutdoorGlbFace> &faces)
{
    bool joinedAny = true;

    while (joinedAny)
    {
        joinedAny = false;
        // Every directed edge to the faces it starts in.
        std::map<std::pair<Point3, Point3>, std::vector<size_t>> edges;

        for (size_t index = 0; index < faces.size(); ++index)
        {
            const std::vector<Point3> &points = faces[index].points;

            for (size_t corner = 0; corner < points.size(); ++corner)
            {
                edges[{points[corner], points[(corner + 1) % points.size()]}].push_back(index);
            }
        }

        std::vector<bool> gone(faces.size(), false);

        for (size_t index = 0; index < faces.size(); ++index)
        {
            if (gone[index])
            {
                continue;
            }

            for (size_t edge = 0; edge < faces[index].points.size(); ++edge)
            {
                const std::vector<Point3> &points = faces[index].points;
                const auto other = edges.find({points[(edge + 1) % points.size()], points[edge]});

                if (other == edges.end())
                {
                    continue;
                }

                bool done = false;

                for (const size_t candidate : other->second)
                {
                    if (candidate == index || gone[candidate])
                    {
                        continue;
                    }

                    if (std::optional<OutdoorGlbFace> face = joined(faces[index], edge, faces[candidate]))
                    {
                        faces[index] = std::move(*face);
                        gone[candidate] = true;
                        joinedAny = true;
                        done = true;
                        break;
                    }
                }

                // The face changed: its edges are looked at again in the next pass.
                if (done)
                {
                    break;
                }
            }
        }

        std::vector<OutdoorGlbFace> kept;

        for (size_t index = 0; index < faces.size(); ++index)
        {
            if (!gone[index])
            {
                kept.push_back(std::move(faces[index]));
            }
        }

        faces = std::move(kept);
    }
}

bool readOutdoorGlb(const std::filesystem::path &path, const OutdoorGlbOptions &options,
    std::vector<OutdoorGlbMesh> &meshes, std::vector<std::string> &errors)
{
    meshes.clear();
    cgltf_options parseOptions = {};
    cgltf_data *pData = nullptr;
    const std::string file = path.string();

    if (cgltf_parse_file(&parseOptions, file.c_str(), &pData) != cgltf_result_success)
    {
        errors.push_back("could not read " + file + " as glTF (.glb or .gltf)");
        return false;
    }

    const std::unique_ptr<cgltf_data, decltype(&cgltf_free)> owned(pData, &cgltf_free);

    if (cgltf_load_buffers(&parseOptions, pData, file.c_str()) != cgltf_result_success)
    {
        errors.push_back("could not load the buffers of " + file);
        return false;
    }

    const size_t errorsBefore = errors.size();
    size_t refused = 0;
    const auto refuse = [&errors, &refused](const std::string &sentence)
    {
        if (refused++ < NamedRefusals)
        {
            errors.push_back(sentence);
        }
    };

    for (size_t nodeIndex = 0; nodeIndex < pData->nodes_count; ++nodeIndex)
    {
        const cgltf_node &node = pData->nodes[nodeIndex];

        if (node.mesh == nullptr || node.skin != nullptr)
        {
            continue;
        }

        OutdoorGlbMesh mesh;
        mesh.name = node.name != nullptr && node.name[0] != '\0' ? node.name
            : (node.mesh->name != nullptr && node.mesh->name[0] != '\0' ? node.mesh->name
                : "mesh" + std::to_string(meshes.size()));
        float matrix[16];
        cgltf_node_transform_world(&node, matrix);
        const auto toMap = [&matrix, &options](const float *local)
        {
            const double x = matrix[0] * local[0] + matrix[4] * local[1] + matrix[8] * local[2] + matrix[12];
            const double y = matrix[1] * local[0] + matrix[5] * local[1] + matrix[9] * local[2] + matrix[13];
            const double z = matrix[2] * local[0] + matrix[6] * local[1] + matrix[10] * local[2] + matrix[14];
            const Point3 axes = options.zUp ? Point3{x * options.scale, y * options.scale, z * options.scale}
                                            : Point3{x * options.scale, -z * options.scale, y * options.scale};
            const double angle = -options.turnDegrees * Pi / 180.0;
            const double east = axes[0] - options.pivot[0];
            const double north = axes[1] - options.pivot[1];
            return Point3{options.pivot[0] + east * oy::cos(angle) - north * oy::sin(angle) + options.move[0],
                options.pivot[1] + east * oy::sin(angle) + north * oy::cos(angle) + options.move[1],
                axes[2] + options.move[2]};
        };

        for (size_t primitiveIndex = 0; primitiveIndex < node.mesh->primitives_count; ++primitiveIndex)
        {
            const cgltf_primitive &primitive = node.mesh->primitives[primitiveIndex];
            const cgltf_accessor *pPositions = attributeOf(primitive, cgltf_attribute_type_position, 0);
            const cgltf_accessor *pUvs = attributeOf(primitive, cgltf_attribute_type_texcoord, 0);
            const std::string material = primitive.material != nullptr && primitive.material->name != nullptr
                ? primitive.material->name : std::string();

            if (pPositions == nullptr || (primitive.type != cgltf_primitive_type_triangles
                    && primitive.type != cgltf_primitive_type_triangle_strip
                    && primitive.type != cgltf_primitive_type_triangle_fan))
            {
                continue;
            }

            std::vector<Point3> points(pPositions->count);
            std::vector<Uv> uvs(pPositions->count, Uv{0.0, 0.0});

            for (size_t vertex = 0; vertex < pPositions->count; ++vertex)
            {
                float local[3] = {0.0f, 0.0f, 0.0f};
                cgltf_accessor_read_float(pPositions, vertex, local, 3);
                points[vertex] = toMap(local);

                if (pUvs != nullptr && vertex < pUvs->count)
                {
                    float uv[2] = {0.0f, 0.0f};
                    cgltf_accessor_read_float(pUvs, vertex, uv, 2);
                    uvs[vertex] = {uv[0], uv[1]};
                }
            }

            const size_t count = primitive.indices != nullptr ? primitive.indices->count : points.size();
            const auto corner = [&primitive](size_t at)
            {
                return primitive.indices != nullptr ? static_cast<size_t>(cgltf_accessor_read_index(
                    primitive.indices, at)) : at;
            };
            const auto take = [&](const std::vector<size_t> &corners)
            {
                std::vector<Point3> facePoints;
                std::vector<Uv> faceUvs;

                for (const size_t index : corners)
                {
                    if (index >= points.size())
                    {
                        return;
                    }

                    facePoints.push_back(points[index]);
                    faceUvs.push_back(uvs[index]);
                }

                addFace(mesh, facePoints, faceUvs, pUvs != nullptr, material);
            };

            if (primitive.type == cgltf_primitive_type_triangle_fan)
            {
                // A fan is one polygon (a Blender n-gon kept whole).
                std::vector<size_t> corners;

                for (size_t at = 0; at < count; ++at)
                {
                    corners.push_back(corner(at));
                }

                mesh.triangles += count >= 3 ? count - 2 : 0;
                take(corners);
            }
            else if (primitive.type == cgltf_primitive_type_triangle_strip)
            {
                for (size_t at = 0; at + 2 < count; ++at)
                {
                    ++mesh.triangles;
                    take(at % 2 == 0 ? std::vector<size_t>{corner(at), corner(at + 1), corner(at + 2)}
                                     : std::vector<size_t>{corner(at + 1), corner(at), corner(at + 2)});
                }
            }
            else
            {
                for (size_t at = 0; at + 2 < count; at += 3)
                {
                    ++mesh.triangles;
                    take({corner(at), corner(at + 1), corner(at + 2)});
                }
            }
        }

        joinOutdoorGlbFaces(mesh.faces);
        size_t corners = 0;

        for (const OutdoorGlbFace &face : mesh.faces)
        {
            const std::string where = "mesh `" + mesh.name + "`: a face of `" + face.material + "` at "
                + pointText(middleOf(face.points));
            corners += face.points.size();

            if (face.points.size() > MostCorners)
            {
                refuse(where + " has " + std::to_string(face.points.size()) + " corners; a BModel face has at most "
                    "20: cut it in Blender");
            }
            else if (!convex(face.points))
            {
                refuse(where + " is not convex; a BModel face is: cut it into convex faces in Blender "
                    "(Triangulate, or Split Concave Faces)");
            }
            else if (areaOf(face.points) < options.minArea)
            {
                refuse(where + " is " + std::to_string(static_cast<int>(std::lround(areaOf(face.points))))
                    + " square units, under the least (" + std::to_string(static_cast<int>(options.minArea))
                    + ", `min_area`): a face that small flickers and catches the party; join it to its neighbour or "
                    "remove it");
            }
            else if (sharpestCorner(face.points) < options.minAngleDegrees)
            {
                std::ostringstream angle;
                angle.precision(2);
                angle << std::fixed << sharpestCorner(face.points);
                refuse(where + " is a sliver: its sharpest corner is " + angle.str() + " degrees, under "
                    + std::to_string(options.minAngleDegrees).substr(0, 4) + " (`min_angle`); a sliver of a "
                    "picture that does not run on from its neighbour cannot be joined to it: give the two one "
                    "UV island, or move the corner");
            }
        }

        if (mesh.faces.size() > options.faceBudget)
        {
            errors.push_back("mesh `" + mesh.name + "` has " + std::to_string(mesh.faces.size()) + " faces after "
                "joining, over the budget of " + std::to_string(options.faceBudget) + " a BModel (`face_budget`): "
                "split it into several meshes or simplify it (the shipped maps' largest models have a few hundred)");
        }

        if (corners > 65535)
        {
            errors.push_back("mesh `" + mesh.name + "` has more than 65535 corners: split it into several meshes");
        }

        if (!mesh.faces.empty())
        {
            meshes.push_back(std::move(mesh));
        }
    }

    if (refused > NamedRefusals)
    {
        errors.push_back("... and " + std::to_string(refused - NamedRefusals) + " more faces refused");
    }

    if (meshes.empty() && errors.size() == errorsBefore)
    {
        errors.push_back(file + " has no mesh with faces");
    }

    return errors.size() == errorsBefore;
}
}
