from pathlib import Path

INPUT_DIR = Path(__file__).resolve().parents[2] / "input"
class FileHelper:

    @staticmethod
    def readAllLines(filename: str) -> list[str]:
        with open(INPUT_DIR / filename, "r") as file:
            return [line.strip() for line in file if line.strip()]