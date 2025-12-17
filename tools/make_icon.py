import os
import sys


def _die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    """
    Convert a PNG into a multi-size ICO suitable for Windows EXE/installer icons.

    Usage:
      python tools/make_icon.py Assets/logo.png build/logo.ico
    """
    if len(sys.argv) != 3:
        _die("Usage: python tools/make_icon.py <input.png> <output.ico>")

    src = sys.argv[1]
    dst = sys.argv[2]

    try:
        from PIL import Image  # type: ignore
    except Exception:
        _die("Missing dependency: Pillow. Install with: python -m pip install pillow")

    if not os.path.exists(src):
        _die(f"Input not found: {src}")

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)

    img = Image.open(src).convert("RGBA")
    # Standard icon sizes; Windows will pick the best match automatically.
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(dst, format="ICO", sizes=sizes)
    print(f"Wrote: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


