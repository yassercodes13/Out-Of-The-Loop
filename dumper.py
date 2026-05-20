from pathlib import Path

# =========================
# SETTINGS
# =========================

PROJECT_ROOT = Path(__file__).parent

OUTPUT_BASENAME = "project_dump"
OUTPUT_EXTENSION = ".txt"

MAX_CHARS_PER_FILE = 1_500_000
# Split into multiple dump files if exceeded

INCLUDE_EXTENSIONS = {
  ".py",
  ".txt",
  ".md",
  ".json",
  ".yaml",
  ".yml",
  ".toml",
  ".ini",
  ".cfg",
  ".env",
}

IGNORE_FOLDERS = {
  "__pycache__",
  ".git",
  ".venv",
  "venv",
  "env",
  ".idea",
  ".vscode",
  "node_modules",
  "build",
  "dist",
  ".pytest_cache",
  ".mypy_cache",
}

IGNORE_FILES = {
  ".DS_Store",
  "project_dump.txt",
  "dumper.py",
}

PRIORITY_FILES = [
  "main.py",
  "bot.py",
  "config.py",
  "requirements.txt",
]

SEPARATOR_LENGTH = 100

SHOW_TREE = True
SHOW_FILE_COUNT = True
SHOW_CHAR_COUNT = True

# =========================


def should_ignore(path: Path) -> bool:
  for part in path.parts:
    if part in IGNORE_FOLDERS:
      return True

  if path.name in IGNORE_FILES:
    return True

  return False


def get_all_files(root: Path) -> list[Path]:
  files = []

  for path in root.rglob("*"):
    if should_ignore(path):
      continue

    if not path.is_file():
      continue

    if path.suffix not in INCLUDE_EXTENSIONS:
      continue

    files.append(path)

  return sort_files(files)


def sort_files(files: list[Path]) -> list[Path]:
  priority = []
  normal = []

  for file in files:
    if file.name in PRIORITY_FILES:
      priority.append(file)
    else:
      normal.append(file)

  priority.sort(
    key=lambda p: PRIORITY_FILES.index(p.name)
  )

  normal.sort()

  return priority + normal


def make_separator() -> str:
  return "=" * SEPARATOR_LENGTH


def make_header(relative_path: Path) -> str:
  separator = make_separator()

  return (
    f"\n{separator}\n"
    f"{relative_path.as_posix()}\n"
    f"{separator}\n"
  )


def read_file(path: Path) -> str:
  try:
    return path.read_text(encoding="utf-8")

  except UnicodeDecodeError:
    return "[BINARY OR NON-UTF8 FILE SKIPPED]"

  except Exception as e:
    return f"[ERROR READING FILE: {e}]"


def generate_tree(root: Path) -> str:
  lines = []

  def walk(folder: Path, prefix: str = ""):
    entries = sorted(
      [
        p for p in folder.iterdir()
        if not should_ignore(p)
      ],
      key=lambda p: (p.is_file(), p.name.lower())
    )

    for index, path in enumerate(entries):
      connector = "└── " if index == len(entries) - 1 else "├── "

      lines.append(prefix + connector + path.name)

      if path.is_dir():
        extension = "   " if index == len(entries) - 1 else "│   "
        walk(path, prefix + extension)

  lines.append(root.name)
  walk(root)

  return "\n".join(lines)


def build_output(files: list[Path]) -> str:
  parts = []

  if SHOW_TREE:
    parts.append(make_separator())
    parts.append("PROJECT TREE")
    parts.append(make_separator())
    parts.append(generate_tree(PROJECT_ROOT))
    parts.append("\n")

  for file_path in files:
    relative_path = file_path.relative_to(PROJECT_ROOT)

    parts.append(make_header(relative_path))
    parts.append(read_file(file_path))
    parts.append("\n")

  return "\n".join(parts)


def split_text(text: str, chunk_size: int) -> list[str]:
  chunks = []

  start = 0

  while start < len(text):
    end = start + chunk_size
    chunks.append(text[start:end])
    start = end

  return chunks


def save_output(text: str):
  chunks = split_text(text, MAX_CHARS_PER_FILE)

  if len(chunks) == 1:
    output_path = (
      PROJECT_ROOT /
      f"{OUTPUT_BASENAME}{OUTPUT_EXTENSION}"
    )

    output_path.write_text(
      chunks[0],
      encoding="utf-8"
    )

    print(f"Saved: {output_path.name}")

  else:
    for i, chunk in enumerate(chunks, start=1):
      output_path = (
        PROJECT_ROOT /
        f"{OUTPUT_BASENAME}_part{i}{OUTPUT_EXTENSION}"
      )

      output_path.write_text(
        chunk,
        encoding="utf-8"
      )

      print(f"Saved: {output_path.name}")


def main():
  files = get_all_files(PROJECT_ROOT)

  output_text = build_output(files)

  save_output(output_text)

  print("\nDone!")

  if SHOW_FILE_COUNT:
    print(f"Files included: {len(files)}")

  if SHOW_CHAR_COUNT:
    print(f"Total characters: {len(output_text):,}")

    estimated_tokens = len(output_text) // 4
    print(f"Estimated tokens: ~{estimated_tokens:,}")


if __name__ == "__main__":
  main()