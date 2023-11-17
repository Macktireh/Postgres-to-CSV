import base64
import csv
import os
from pathlib import Path
from typing import List, Tuple

import psycopg2
from dotenv import load_dotenv


class PostgreSQLConnection:
    def __init__(self) -> None:
        self.load_env()
        self.params = {
            "database": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "host": os.getenv("POSTGRES_HOST"),
            "port": os.getenv("POSTGRES_PORT"),
        }

    def load_env(self) -> None:
        BASE_DIR: Path = Path(__file__).resolve().parent
        load_dotenv(os.path.join(BASE_DIR, ".env"))

    def connect(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(**self.params)


class DataProcessor:
    def __init__(self, connection: PostgreSQLConnection) -> None:
        self.connection = connection

    def fetch_data(self) -> Tuple[List[Tuple], List[str]]:
        with self.connection.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM imgtest.data_passeport_client")
                return cur.fetchall()[:10], [col[0] for col in cur.description]

    def export_to_csv(self, col_names: List[str], record: List[Tuple]) -> None:
        if not os.path.exists("images"):
            os.makedirs("images")

        with open("output.csv", "w", newline="") as f:
            writer = csv.writer(f)
            col_names[-1] = "image_filename"
            writer.writerow(col_names)
            for row in record:
                row = list(row)
                filename = self.save_image(row[-1], row[0], row[1])
                row[-1] = filename
                writer.writerow(row)

    def save_image(self, base64_image: bytes, col1: str, col2: str) -> str:
        filename: str = f"images/{str(col1)}_{col2}".replace(" ", "_") + ".png"
        base64_img: bytes = base64.b64encode(base64_image)
        img_data: bytes = base64.b64decode(base64_img)
        with open(filename, "wb") as f:
            f.write(img_data)
        return filename


def main() -> None:
    postgres_connection: PostgreSQLConnection = PostgreSQLConnection()
    data_processor: DataProcessor = DataProcessor(postgres_connection)

    data, column_names = data_processor.fetch_data()
    data_processor.export_to_csv(column_names, data)


if __name__ == "__main__":
    main()
