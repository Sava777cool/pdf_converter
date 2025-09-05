import re
import httpx
import codecs
import time
import json
import asyncio
from pathlib import Path
from loguru import logger
from pymupdf import open as pdf_open

from config import settings

BASE_DIR = Path(__file__).parent


async def chat_gpt_request(data_set: list):
    """
    Coroutine for work with chat_gpt, send data set and wait split data set
    :param data_set: [menu items]
    :return: str"content with split data [split items]"
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"It's part of menu split please by items {data_set} and return only list with split items"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant for working with python I give to you data and you need to split it into elements.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]


def get_list_files(file_format: str) -> tuple:
    all_files = list(BASE_DIR.glob(f"*.{file_format}"))
    logger.info(
        f"{get_list_files.__name__}: Find {len(all_files)} {file_format.upper()} files."
    )
    return tuple(all_files)


def get_data_from_file(file_name: str) -> tuple:
    """
    Function open file by name get data for all pages and return tuple with elements
    :param file_name: str(*.pdf)
    :return: tuple([element1...])
    """
    full_file_data = []
    document = pdf_open("espn_bet.pdf")
    for page in document:
        page_data = page.get_text("blocks")
        for block in page_data:
            for element in block:
                if isinstance(element, str):
                    decoded_uni = codecs.decode(element, "unicode_escape")
                    decoded_utf = decoded_uni.encode("latin1").decode("utf-8")
                    cleaned_utf = re.sub(
                        r"[\u0000-\u001F\u007F\u00A0]", " ", decoded_utf
                    )
                    strip_data = re.sub(r"\s+", " ", cleaned_utf).strip()
                    full_file_data.append(strip_data)
    logger.info(
        f"{get_data_from_file.__name__}: Find {len(full_file_data)} elements in file."
    )
    return tuple(full_file_data)


async def main() -> None:
    """
    Main function with algorithm of work with files
    :return: None
    """
    files_in_dir = get_list_files(file_format="pdf")

    for file in files_in_dir:
        file_data = get_data_from_file(file_name=file)

        file_name = file.name
        with open(
            f"complete_{file_name.split('.')[0]}_menu.json", "w", encoding="utf-8"
        ) as j_file:
            json.dump(file_data, j_file, ensure_ascii=False, indent=4)
            logger.info(
                f"Successfully saved complete_{file_name.split('.')[0]}_menu.json file to {BASE_DIR}"
            )


if __name__ == "__main__":
    start_point = time.perf_counter()
    logger.debug("Start script")

    asyncio.run(main())

    end_point = time.perf_counter()
    lead_time = end_point - start_point
    logger.debug(f"Finish script. Lead time: {lead_time}")
