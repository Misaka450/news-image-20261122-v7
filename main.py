import os
import shutil


def main() -> None:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    destination = os.path.join(output_dir, "entry.png")
    if not os.path.exists(source):
        raise FileNotFoundError(source)
    shutil.copy2(source, destination)
    print(destination)


if __name__ == "__main__":
    main()
