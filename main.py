#!/usr/bin/env python3
import argparse, re
from multiprocessing import Pool
from pathlib import Path

import img2pdf

from enhance_image import enhance_image


def natural_filename_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path, help="folder of original PNGs")
    ap.add_argument(
        "out", type=Path, help="output folder (originals are never modified)"
    )
    ap.add_argument("--per-pdf", type=int, default=200, help="pages per PDF")
    ap.add_argument(
        "--gamma", type=float, default=1.6, help="higher = darker ink (try 1.2 to 2.5)"
    )
    ap.add_argument(
        "--format",
        choices=["png", "jpg"],
        default="jpg",
        help="format of enhanced pages",
    )
    ap.add_argument("--quality", type=int, default=88, help="JPEG quality")
    ap.add_argument(
        "--dpi",
        type=int,
        default=0,
        help="force page DPI in PDF (e.g. 300); 0 = use image metadata",
    )
    ap.add_argument(
        "--limit", type=int, default=0, help="process only first N files (for testing)"
    )
    ap.add_argument(
        "--no-pdf", action="store_true", help="enhance only, skip PDF assembly"
    )

    return ap.parse_args()


def main():

    args = parse_arguments()

    files = sorted(args.src.glob("*.png"), key=natural_filename_key) + sorted(
        args.src.glob("*.PNG"), key=natural_filename_key
    )
    if args.limit:
        files = files[: args.limit]
    img_dir = args.out / "enhanced"
    img_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg" if args.format == "jpg" else ".png"
    jobs = [(f, img_dir / (f.stem + ext), args.gamma, args.quality) for f in files]

    with Pool() as pool:
        results = []
        for i, r in enumerate(pool.imap(enhance_image, jobs, chunksize=4), 1):
            results.append(r)
            if i % 100 == 0:
                print(f"{i}/{len(jobs)} enhanced")
    done = [r for r in results if r]

    if args.no_pdf:
        return
    layout = (
        img2pdf.get_fixed_dpi_layout_fun((args.dpi, args.dpi)) if args.dpi else None
    )
    pdf_dir = args.out / "pdfs"
    pdf_dir.mkdir(exist_ok=True)
    for start in range(0, len(done), args.per_pdf):
        chunk = done[start : start + args.per_pdf]
        name = f"journal_{chunk[0].stem}__{chunk[-1].stem}.pdf"
        with open(pdf_dir / name, "wb") as fh:
            fh.write(img2pdf.convert([str(p) for p in chunk], layout_fun=layout))
        print(f"wrote {name} ({len(chunk)} pages)")


if __name__ == "__main__":
    main()
