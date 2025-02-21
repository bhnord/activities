import itertools
from io import TextIOWrapper
from bs4.element import Tag
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re

## todo: get dynamically from https://www.thebostoncalendar.com/
url = "https://www.thebostoncalendar.com/events/80-free-things-to-do-in-boston-this-week-feb-18-23-2025"


def getDescriptionText(bitly_link: str) -> str:
    content = requests.get(bitly_link).text
    soup = BeautifulSoup(content, "lxml")
    text = soup.find(id="event_description")
    return text.getText() if text is not None else ""


def addToFile(item: Tag, file: TextIOWrapper):
    if re.match(r"[0-9]+\)*", item.text):
        text = item.text
        event_name = re.search(r"[0-9]+\)\s+(.+)\s+", text).group(1).strip()
        link = str(item.find("a").get("href"))
        match = re.match(r"^[^.!?]*[.!?]", getDescriptionText(link))
        description = match.group(0).strip() if match else ""

        event = (
            "### "
            + event_name
            + "\n"
            + description
            + "  \n"
            + "[info link]("
            + link
            + ")\n"
        )
        file.write(event)


if __name__ == "__main__":
    content = requests.get(url).text
    soup = BeautifulSoup(content, "lxml")

    header = soup.find("h1").text.strip()
    filename = datetime.now().strftime("%m-%d-%Y")

    events = []
    items = soup.find(id="event_description")
    with open(filename + ".md", "w") as file:
        file.write("# " + header + "\n")

        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(addToFile, items.findChildren(), itertools.repeat(file))
            #    for item in items.findChildren():
            #        addToFile(item, file)
