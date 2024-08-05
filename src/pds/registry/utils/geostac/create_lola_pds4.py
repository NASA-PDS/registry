"""Script to scrape GeoSTAC for Lola point clouds and make pds4 xml."""
import argparse
import importlib
from datetime import date
from pathlib import Path

import requests
from jinja2 import Environment
from pds.registry.utils.geostac import templates


def create_product_external(item):
    """Creates Product_External for given item.

    :param item: item to fill out pds4 xml information with

    :return: pds4 xml
    """
    # create env
    env = Environment()

    with importlib.resources.open_text(templates, "product-external-template.xml") as io:
        template_text = io.read()
        template = env.from_string(template_text)

        item_title = item["assets"]["data"]["title"]

        last_slash_i = item["assets"]["data"]["href"].rfind("/")
        file = item["assets"]["data"]["href"][last_slash_i + 1:]

        # fill out template params
        lid = "urn:nasa:pds:geostac:external:" + item_title.lower()
        title = item_title
        modification_date = str(date.today())
        lid_ref = item_title.lower()
        bb_west = item["bbox"][0]
        bb_south = item["bbox"][1]
        bb_east = item["bbox"][2]
        bb_north = item["bbox"][3]
        file_name = file
        lid_file = item_title.lower()
        file_date = item["properties"]["datetime"][:10]
        file_url = item["assets"]["data"]["href"]
        # file_size not in api, but also not required by pds
        encoding_standard = item["properties"]["pc:encoding"]

        context = {
            "lid": lid,
            "title": title,
            "modification_date": modification_date,
            "lid_ref": lid_ref,
            "bb_west": bb_west,
            "bb_east": bb_east,
            "bb_north": bb_north,
            "bb_south": bb_south,
            "file_name": file_name,
            "lid_file": lid_file,
            "file_date": file_date,
            "file_url": file_url,
            # file_size
            "encoding_standard": encoding_standard
        }

        return template.render(context)


def create_product_browse(item):
    """Creates Product_Browse for given item.

    :param item: item to fill out pds4 xml information with

    :return: pds4 xml
    """
    # create env
    env = Environment()

    with importlib.resources.open_text(templates, "product-browse-template.xml") as io:
        template_text = io.read()
        template = env.from_string(template_text)

        item_title = item["assets"]["data"]["title"]

        last_slash_i = item["assets"]["thumbnail"]["href"].rfind("/")
        file = item["assets"]["thumbnail"]["href"][last_slash_i + 1:]
        data_type = item["assets"]["thumbnail"]["type"]
        encoding_map = {"image/jpeg": "JPEG"}

        # fill out template params
        lid = "urn:nasa:pds:geostac:browse:" + item_title.lower() + "_browse"
        title = item_title
        lid_ref = item_title.lower() + "_browse"
        file_name = file
        file_date = item["properties"]["datetime"][:10]
        file_url = item["assets"]["thumbnail"]["href"]
        encoding_standard = encoding_map[data_type]

        context = {
            "lid": lid,
            "title": title,
            "lid_ref": lid_ref,
            "file_name": file_name,
            "file_date": file_date,
            "file_url": file_url,
            "encoding_standard": encoding_standard
        }

        return template.render(context)


def parse_args():
    """Parses arguments of command.

    :return: args dictionary
    """
    # set up command line args
    parser = argparse.ArgumentParser(description="Create and save pds4 xml labels created for Lola point clouds in GeoSTAC",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-s",
                        "--save-xml",
                        action="store_true",
                        help="True if you want the xml files to be saved",
                        default=True)
    parser.add_argument("-d",
                        "--destination-directory",
                        help="Directory to save pds4 xml files",
                        default="lola_xml")

    args = parser.parse_args()

    return args


def main():
    """Main function of script."""
    # parse args
    args = parse_args()
    dest = args.destination_directory
    save_xml = args.save_xml

    # get json from url
    url = "https://stac.astrogeology.usgs.gov/api//collections/lunar_orbiter_laser_altimeter/items?limit=100000"
    response = requests.get(url, timeout=30)
    json_data = response.json()
    features = json_data["features"]

    for item in features:
        external_pds4 = create_product_external(item)
        browse_pds4 = create_product_browse(item)

        if save_xml:
            # create destination directoru if they don't exist
            Path(dest + "/product_external").mkdir(parents=True, exist_ok=True)
            Path(dest + "/product_browse").mkdir(parents=True, exist_ok=True)

            ex_path = dest + "/product_external/" + item["assets"]["data"]["title"] + "_product_external.xml"
            with open(ex_path, "w") as f:
                f.write(external_pds4)

            br_path = dest + "/product_browse/" + item["assets"]["data"]["title"] + "_product_browse.xml"
            with open(br_path, "w") as f:
                f.write(browse_pds4)


if __name__ == "__main__":
    main()
