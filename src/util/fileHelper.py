class FileHelper:

    @staticmethod
    def readAllLines(filename: str) -> list[str]:
        directory = "../input/"
        with open(directory+filename, "r") as file:
            return [line.strip() for line in file if line.strip()]