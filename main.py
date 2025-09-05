import re
import time
import json
import codecs
import asyncio
import httpx
from pathlib import Path
from loguru import logger
from pymupdf import open as pdf_open

from config import settings
from menu_schema import MenuSchema

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
    document = pdf_open(file_name)
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


def get_grouped_data_by_categories(file_data: tuple) -> dict[str:list]:
    grouped_data = {}
    new_category = None

    for item in file_data:
        if "served" in item or "Contains" in item:
            continue
        elif "ENERGY" in item or item.isupper() and "$" not in item:
            new_category = item
            grouped_data.update({item: []})
        else:
            grouped_data[new_category].append(item)
    logger.info(
        f"{get_grouped_data_by_categories.__name__} Successfully grouped data by categories"
    )
    return grouped_data


def get_jumbo_chicken(grouped_data: dict) -> dict[str:list]:
    """
    Function for split dishes in AIN’T NO THING BUT A CHICKEN…
    :param grouped_data: dict with category : dishes data
    :return: dict with current main category
    """
    full_category = "AIN’T NO THING BUT A CHICKEN…"
    sub_category = "JUMBO CHICKEN WINGS BREADED CHICKEN TENDERS"
    dishes_list = grouped_data.get(sub_category)
    split_sub_category = sub_category.split("WINGS")
    jumbo = split_sub_category[0].strip()
    breaded = split_sub_category[-1].strip()
    split_index = len(dishes_list) - 2
    jumbo_dishes = [f"{jumbo} {dish}" for dish in dishes_list[:split_index]]
    breaded_dishes = [f"{breaded} {dish}" for dish in dishes_list[:split_index]]
    logger.info(f"{get_jumbo_chicken.__name__} Successfully grouped chicken wings data")
    return {full_category: [*jumbo_dishes, *breaded_dishes]}


def clean_raw_text(raw_data: str) -> tuple:
    """
    Function for find lists in gpt response
    :param raw_data: text
    :return: tuple([dish1, dish2])
    """
    convert_str = []
    try:
        pattern = re.compile(r"\[.*?\]", re.DOTALL)
        matches_data = pattern.findall(raw_data)
        convert_str = [
            x.strip().replace("'", "") for x in matches_data[-1].strip("[]").split(",")
        ]
        logger.info(f"{clean_raw_text.__name__} Successfully find data in raw text.")

    except IndexError:
        logger.error(f"{clean_raw_text.__name__} The are not any elements in response.")
    return tuple(convert_str)


async def get_split_sauces_memu(grouped_data: dict) -> dict[str:list]:
    """
    Function for separate sauces in sauces menu.
    Make request to gpt for get elements list.
    :param grouped_data: dict {category: [dishes list]}
    :return: category: [dishes list]
    """
    categories = list(grouped_data.keys())
    sauces_data = [
        item
        for item in categories
        if "SIGNATURE SAUCES" in item or "BACON BOURBON" in item
    ]
    raw_sauces_data = await chat_gpt_request(data_set=sauces_data)
    try:
        cleaned_data = clean_raw_text(raw_data=raw_sauces_data)
        logger.info(f"{get_split_sauces_memu.__name__} Successfully split sauces.")
        return {cleaned_data[0]: cleaned_data[1:]}
    except IndexError:
        logger.error(f"{get_split_sauces_memu.__name__} The are not any sauces.")
        return {}


async def get_split_flights(grouped_data: dict) -> dict:
    """
    Function for separate amount of wings in element.
    Make request to gpt for separate data.
    :param grouped_data: dict {category: [dishes list]}
    :return: category: [dishes list]
    """
    flights_data = grouped_data.get("FLIGHTS")
    raw_wings_data = await chat_gpt_request(data_set=flights_data)
    cleaned_data = clean_raw_text(raw_data=raw_wings_data)
    logger.info(f"{get_split_flights.__name__} Successfully split dishes in FLIGHTS.")
    return {"FLIGHTS": cleaned_data}


def get_energy_drinks_menu(grouped_data: dict) -> dict:
    """
    Function for grouping energy drinks.
    Find category and group energy drinks
    :param grouped_data: dict {category: [dishes list]}
    :return: category: [dishes list]
    """
    keys_list = list(grouped_data.keys())
    index_energy = keys_list.index("ENERGY $X")
    energy_drinks_data = keys_list[index_energy:]
    category_name = energy_drinks_data.pop(0).replace(" $X", "")
    logger.info(
        f"{get_energy_drinks_menu.__name__} Successfully grouped {len(energy_drinks_data)} energy drinks."
    )
    return {category_name: energy_drinks_data}


def get_join_rows(grouped_data: dict, cat_name: str) -> dict:
    """
    Function for join description to dish name
    :param grouped_data: dict {category: [dishes list]}
    :param cat_name: Name of category need for get data by key
    :return: category: [dishes list]
    """
    cat_data = grouped_data.get(cat_name)
    joined_rows = [
        " ".join([cat_data[index], cat_data[index + 1]])
        for index in range(0, len(cat_data), 2)
    ]
    logger.info(f"{get_join_rows.__name__} Successfully joined data.")
    return {cat_name: joined_rows}


async def main() -> None:
    """
    Main function with algorithm of work with files
    :return: None
    """
    files_in_dir = get_list_files(file_format="pdf")

    for file in files_in_dir:
        file_data = get_data_from_file(file_name=file)
        raw_grouped_data_by_categories = get_grouped_data_by_categories(
            file_data=file_data
        )

        jumbo_chicken = get_jumbo_chicken(grouped_data=raw_grouped_data_by_categories)
        sauces = await get_split_sauces_memu(
            grouped_data=raw_grouped_data_by_categories
        )
        flights = await get_split_flights(grouped_data=raw_grouped_data_by_categories)
        cocktails_update = get_join_rows(
            grouped_data=raw_grouped_data_by_categories, cat_name="SIGNATURE COCKTAILS"
        )
        zero_proof_update = get_join_rows(
            grouped_data=raw_grouped_data_by_categories, cat_name="ZERO PROOF"
        )
        energy_drinks = get_energy_drinks_menu(
            grouped_data=raw_grouped_data_by_categories
        )
        grouped_data_without_empty_cat = {
            category: dishes
            for category, dishes in raw_grouped_data_by_categories.items()
            if dishes and "JUMBO CHICKEN" not in category
        }
        grouped_data_without_empty_cat.update(
            {
                **jumbo_chicken,
                **sauces,
                **flights,
                **cocktails_update,
                **zero_proof_update,
                **energy_drinks,
            }
        )
        transform_menu_data = [
            MenuSchema(category=category, dish=dish).split_dish_data
            for category, dishes in grouped_data_without_empty_cat.items()
            for dish in dishes
        ]
        file_name = file.name
        with open(
            f"complete_{file_name.split('.')[0]}_menu.json", "w", encoding="utf-8"
        ) as j_file:
            json.dump(transform_menu_data, j_file, ensure_ascii=False, indent=4)
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
