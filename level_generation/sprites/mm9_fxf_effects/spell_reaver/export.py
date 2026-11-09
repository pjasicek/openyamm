#!/usr/bin/env python3
"""Export reviewed imagegen sheets; never write engine assets or alter source evidence."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import yaml
from scipy.optimize import nnls


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[3]
SELECTED = {
    "bluering": "analytic_master.png",
    "flareparticle": "raw_02.png",
    "ringexplodeblue": "raw_02.png",
    "smokenoise": "raw_02.png",
}


def values(image):
    return np.asarray(image.convert("RGBA"), dtype=np.float64) / 255.0


def energy(pixels):
    return (pixels[:, :, :3] * pixels[:, :, 3:]).mean(axis=(0, 1))


def centroid(pixels):
    alpha = pixels[:, :, 3]
    y, x = np.indices(alpha.shape)
    return np.array([((x + 0.5) * alpha).sum() / alpha.sum() / alpha.shape[1],
                     ((y + 0.5) * alpha).sum() / alpha.sum() / alpha.shape[0]])


def fit_gamma(channels, target, weights=None):
    """One shared monotonic curve; retain black, white and phase-to-phase differences."""
    low, high = 0.05, 20.0
    if weights is None:
        weights = [np.ones_like(channel) for channel in channels]
    for _ in range(40):
        middle = (low + high) / 2
        mean = np.mean([(channel ** middle * weight).mean()
                        for channel, weight in zip(channels, weights)])
        if mean > target:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def reconstruct_ring(native):
    """Fit a continuous rounded-ring profile, as recommended for analytic FX by the guide."""
    pixels = values(native)
    target = np.concatenate((pixels[:, :, :3] * pixels[:, :, 3:], pixels[:, :, 3:]), axis=2)
    centers = np.linspace(0, 0.8, 21)
    native_y, native_x = np.indices((native.height, native.width))
    alpha_sum = pixels[:, :, 3].sum()
    center_x = ((native_x + 0.5) * pixels[:, :, 3]).sum() / alpha_sum / native.width
    center_y = ((native_y + 0.5) * pixels[:, :, 3]).sum() / alpha_sum / native.height

    def basis(width, height, exponent):
        x, y = np.meshgrid((np.arange(width) + 0.5) / width - center_x,
                           (np.arange(height) + 0.5) / height - center_y)
        radius = (abs(x) ** exponent + abs(y) ** exponent) ** (1 / exponent)
        return np.exp(-0.5 * ((radius.reshape(-1, 1) - centers) / 0.035) ** 2)

    best = None
    for exponent in np.linspace(1.4, 2.4, 51):
        design = basis(native.width, native.height, exponent)
        coefficients = np.stack([nnls(design, target[:, :, channel].ravel())[0]
                                 for channel in range(4)], axis=1)
        error = np.mean((design @ coefficients - target.reshape(-1, 4)) ** 2)
        if best is None or error < best[0]:
            best = error, exponent, coefficients
    error, exponent, coefficients = best
    fitted = (basis(1024, 1024, exponent) @ coefficients).reshape(1024, 1024, 4)
    alpha = np.clip(fitted[:, :, 3:], 0, 1)
    rgb = np.divide(fitted[:, :, :3], alpha, out=np.zeros_like(fitted[:, :, :3]), where=alpha > 0)
    output = np.concatenate((np.clip(rgb, 0, 1), alpha), axis=2)
    (ROOT / "bluering" / "analytic_fit.json").write_text(json.dumps({
        "method": "nonnegative radial Gaussian basis fit of native premultiplied RGB and alpha",
        "radius_exponent": float(exponent), "mean_squared_error": float(error),
        "native_alpha_center": [float(center_x), float(center_y)],
        "centers": centers.tolist(), "width": 0.035, "coefficients": coefficients.tolist(),
    }, indent=2) + "\n")
    return Image.fromarray(np.rint(output * 255).astype(np.uint8))


def resize(image, size):
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def proof(image, background):
    result = Image.new("RGBA", image.size, (*background, 255))
    result.alpha_composite(image)
    return result.convert("RGB")


def main():
    ledger = yaml.safe_load((ROOT / "ledger.yml").read_text())
    report = {"effect": ledger["effect"], "installed": False, "families": []}
    exports = []
    preview = []
    review_path = ROOT / "review.json"
    review = json.loads(review_path.read_text()) if review_path.exists() else {}
    reviewed_hashes = review.get("exports", {})
    for family in ledger["families"]:
        name = family["family"]
        directory = ROOT / name
        raw_path = directory / SELECTED[name]
        if name == "bluering":
            reconstruct_ring(Image.open(directory / "native/00.png")).save(raw_path)
        sheet = Image.open(raw_path).convert("RGBA")
        count = len(family["frames"])
        columns = 4 if count > 1 else 1
        native_images = []
        masters = []
        for index, frame in enumerate(family["frames"]):
            native = Image.open(directory / "native" / f"{index:02}.png").convert("RGBA")
            native_images.append(native)
            x, y = index % columns, index // columns
            box = (
                round(x * sheet.width / columns), round(y * sheet.height / columns),
                round((x + 1) * sheet.width / columns), round((y + 1) * sheet.height / columns),
            )
            master = sheet.crop(box)
            assert master.width >= 2 * native.width and master.height >= 2 * native.height
            masters.append(master)

        # One constant grade for the complete family, never normalize individual phases.
        native_alpha = np.mean([values(image)[:, :, 3].mean() for image in native_images])
        master_pixels = [values(image) for image in masters]
        if name == "smokenoise":
            # Native smoke is white RGB with structure in alpha. Convert generated neutral shading
            # into opacity without discarding its delivered soft alpha or introducing a hard mask.
            for pixels in master_pixels:
                pixels[:, :, 3] *= pixels[:, :, :3].mean(axis=2)
                pixels[:, :, :3] = 1
        alpha_gamma = fit_gamma([pixels[:, :, 3] for pixels in master_pixels], native_alpha)
        alpha_gain = native_alpha / np.mean([pixels[:, :, 3].mean() for pixels in master_pixels])
        native_energy = np.mean([energy(values(image)) for image in native_images], axis=0)
        graded = []
        for pixels in master_pixels:
            if name == "smokenoise":
                pixels[:, :, 3] = np.clip(pixels[:, :, 3] * alpha_gain, 0, 1)
            else:
                pixels[:, :, 3] = pixels[:, :, 3] ** alpha_gamma
            graded.append(pixels)
        rgb_gamma = np.array([fit_gamma([pixels[:, :, channel] for pixels in graded],
                                       native_energy[channel], [pixels[:, :, 3] for pixels in graded])
                              for channel in range(3)])
        if name == "smokenoise":
            rgb_gamma = np.ones(3)
        details = []
        for index, (frame, native, pixels) in enumerate(zip(family["frames"], native_images, graded)):
            pixels[:, :, :3] = pixels[:, :, :3] ** rgb_gamma
            master = Image.fromarray(np.rint(pixels * 255).astype(np.uint8))
            output = resize(master, (native.width * 2, native.height * 2))
            for folder in ("masters", "native", "export"):
                (directory / folder).mkdir(exist_ok=True)
            master.save(directory / "masters" / f"{index:02}.png")
            output_path = directory / "export" / f"{index:02}.png"
            output.save(output_path)
            native_pixels, output_pixels = values(native), values(output)
            details.append({
                "index": index, "resource": frame["resource"],
                "size": list(output.size), "master_size": list(master.size),
                "alpha_ratio": float(output_pixels[:, :, 3].mean() / native_pixels[:, :, 3].mean()),
                "energy_ratio": (energy(output_pixels) / energy(native_pixels)).tolist(),
                "alpha_centroid_shift_native_pixels": float(np.linalg.norm(
                    (centroid(output_pixels) - centroid(native_pixels)) * frame["size"])),
                "source_sha256": hashlib.sha256((directory / "native" / f"{index:02}.png").read_bytes()).hexdigest(),
                "export_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            })
            exports.append({
                "resource": frame["resource"], "asset": str(output_path.relative_to(REPOSITORY)),
                "native_asset": frame["native_png"], "logical_size": frame["size"],
                "scale": 2, "status": "discarded_archived" if review.get("status") == "discarded_archived"
                else "artwork_reviewed"
                if reviewed_hashes.get(frame["resource"]) == details[-1]["export_sha256"]
                else "pending_visual_review",
            })
        for label, background in (("dark", (24, 24, 24)), ("light", (232, 232, 232))):
            comparison = Image.new("RGB", (1024, count * 256), background)
            for index, native in enumerate(native_images):
                output = Image.open(directory / "export" / f"{index:02}.png")
                comparison.paste(proof(native.resize((256, 256), Image.Resampling.NEAREST), background),
                                 (0, index * 256))
                comparison.paste(proof(resize(output, (256, 256)), background), (256, index * 256))
                comparison.paste(proof(output, background), (544, index * 256 + 64))
            comparison.save(directory / f"comparison_{label}.png")
            comparison.crop((0, 0, 768, min(count, 2) * 256)).save(directory / f"first_two_{label}.png")
        preview.append({"name": name, "count": count, "fps": family["sprite"]["sprite"]["framesPerSecond"],
                        "width": family["sprite"]["sprite"]["logicalWidth"],
                        "height": family["sprite"]["sprite"]["logicalHeight"]})
        report["families"].append({
            "family": name, "selected": SELECTED[name],
            "alpha_gamma": float(alpha_gamma), "rgb_gamma": rgb_gamma.tolist(), "frames": details,
            "smoke_alpha_gain": float(alpha_gain) if name == "smokenoise" else None,
        })
    installed = all((REPOSITORY / entry["native_asset"]).read_bytes() == (REPOSITORY / entry["asset"]).read_bytes()
                    for entry in exports)
    report["installed"] = installed
    (ROOT / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "preview_data.js").write_text("const families = " + json.dumps(preview) + ";\n")
    (ROOT / "export_manifest.yml").write_text(yaml.safe_dump({
        "effect": ledger["effect"], "installed": installed, "textures": exports,
    }, sort_keys=False))
    for family in report["families"]:
        print(family["family"], "alpha gamma", round(family["alpha_gamma"], 3),
              "RGB gamma", [round(value, 3) for value in family["rgb_gamma"]])
        print("  frame alpha ratios", [round(frame["alpha_ratio"], 3) for frame in family["frames"]])
        print("  frame energy ratios", [[round(value, 3) for value in frame["energy_ratio"]]
                                         for frame in family["frames"]])


if __name__ == "__main__":
    main()
