"""
Скрипт проходить по заданих папках, читає файли з дозволеними розширеннями
та зберігає їхній вміст у один текстовий файл для подальшого використання.
"""

from pathlib import Path

# Налаштування
FOLDERS = [
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\views",
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\tests",
]

# Точкові файли, які треба включити (навіть якщо вони поза дозволеними папками)
EXPLICIT_FILES = [
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\ai_engine.py",
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\database.py",
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\main.py",
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\requirements.txt",
    r"D:\CourseWork3\CourseWork-1sem-3year-Runner\Program\requirements.desctop.bak",

]
ALLOWED_EXT = {".py", ".js", ".ts", ".dart", ".json", ".md", ".txt", "bak"}  # розширення
OUTPUT_FILE = Path("collected_code.txt")
MAX_FILE_BYTES = 2_000_000  # пропускати дуже великі файли (>2МБ)

def collect_files(folders: list[Path], direct_files: list[Path]) -> list[Path]:
    files: set[Path] = set()

    # Додати точкові файли, якщо існують
    for f in direct_files:
        if f.is_file() and f.suffix.lower() in ALLOWED_EXT and f.stat().st_size <= MAX_FILE_BYTES:
            files.add(f)

    # Обійти папки рекурсивно
    for folder in folders:
        if folder.is_file():
            # Якщо передали файл у FOLDERS — теж враховуємо
            if folder.suffix.lower() in ALLOWED_EXT and folder.stat().st_size <= MAX_FILE_BYTES:
                files.add(folder)
            continue

        if not folder.exists():
            continue

        for p in folder.rglob("*"):
            if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
                if p.stat().st_size <= MAX_FILE_BYTES:
                    files.add(p)

    return sorted(files)

def main() -> None:
    folders = [Path(p) for p in FOLDERS]
    explicit = [Path(p) for p in EXPLICIT_FILES]
    files = collect_files(folders, explicit)

    with OUTPUT_FILE.open("w", encoding="utf-8", errors="replace") as out:
        for f in files:
            rel = f
            out.write(f"===== {rel} =====\n")
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # фолбек якщо щось пішло не так
                out.write(f"[ERROR reading file: {exc}]\n\n")
                continue
            out.write(text)
            out.write("\n\n")

    print(f"Saved {len(files)} files to {OUTPUT_FILE.resolve()}")

if __name__ == "__main__":
    main()