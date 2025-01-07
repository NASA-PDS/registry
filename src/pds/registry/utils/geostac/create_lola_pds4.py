"""Script to scrape GeoSTAC for Lola point clouds and make pds4 xml."""
import argparse
import importlib
import logging
from datetime import date
from pathlib import Path

import requests
from jinja2 import Environment
from jinja2 import select_autoescape
from pds.registry.utils.geostac import templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_for_overlap(bbox1, bbox2):
    """Checks if bounding boxes overlap anywhere.

    :param item: item to fill out pds4 xml information with

    :return: reference list
    """
    # unpack bounding boxes
    b1_west, b1_south, b1_east, b1_north = bbox1
    b2_west, b2_south, b2_east, b2_north = bbox2

    # check lat overlap
    lat_overlap = False
    if b1_east >= b2_west and b2_east >= b1_west:
        lat_overlap = True

    # check lon overlap
    lon_overlap = False
    if b1_north >= b2_south and b2_north >= b1_south:
        lon_overlap = True

    if lat_overlap and lon_overlap:
        return True

    return False


def create_reference_list(item):
    """Finds relevant references for given item.

    :param item: item to fill out pds4 xml information with

    :return: reference list
    """
    reference_list = []

    bb_west = float(item["bbox"][0])
    bb_south = float(item["bbox"][1])
    bb_east = float(item["bbox"][2])
    bb_north = float(item["bbox"][3])

    bbox1 = [bb_west, bb_south, bb_east, bb_north]

    # needs to be updated with the collection we want to check for overlapping bounding boxes with
    url = "http://pds.nasa.gov/api/search/1/products/urn:nasa:pds:lro_lola_rdr:data_gridded::1.0/members"
    response = requests.get(url, timeout=30)
    json_data = response.json()

    for gdr in json_data["data"]:

        gdr_lid = gdr["properties"]["lid"][0]
        gdr_bb_west = float(gdr["properties"]["cart:Bounding_Coordinates.cart:west_bounding_coordinate"][0])
        gdr_bb_south = float(gdr["properties"]["cart:Bounding_Coordinates.cart:south_bounding_coordinate"][0])
        gdr_bb_east = float(gdr["properties"]["cart:Bounding_Coordinates.cart:east_bounding_coordinate"][0])
        gdr_bb_north = float(gdr["properties"]["cart:Bounding_Coordinates.cart:north_bounding_coordinate"][0])

        bbox2 = [gdr_bb_west, gdr_bb_south, gdr_bb_east, gdr_bb_north]

        if check_for_overlap(bbox1, bbox2):
            reference_list.append(gdr_lid)

    return reference_list


def create_product_external(item):
    """Creates Product_External for given item.

    :param item: item to fill out pds4 xml information with

    :return: pds4 xml
    """
    # create env
    env = Environment(autoescape=select_autoescape(['html', 'xml']))
    with importlib.resources.open_text(templates, "product-external-template.xml") as io:
        template_text = io.read()
        template = env.from_string(template_text)

        item_title = item["assets"]["data"]["title"]

        last_slash_i = item["assets"]["data"]["href"].rfind("/")
        file = "data/" + item["assets"]["data"]["href"][last_slash_i + 1:]
        logger.info(f'file is on {item["assets"]["data"]["href"]},fake file is on {file}')
        open("lola_xml/product_external/" + file, 'a').close()

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
        reference_list = create_reference_list(item)

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
            "encoding_standard": encoding_standard,
            "reference_list": reference_list
        }

        return template.render(context)


def create_product_browse(item):
    """Creates Product_Browse for given item.

    :param item: item to fill out pds4 xml information with

    :return: pds4 xml
    """
    # create env
    env = Environment(autoescape=select_autoescape(['html', 'xml']))

    with importlib.resources.open_text(templates, "product-browse-template.xml") as io:
        template_text = io.read()
        template = env.from_string(template_text)

        item_title = item["assets"]["data"]["title"]

        last_slash_i = item["assets"]["thumbnail"]["href"].rfind("/")
        file = "data/" + item["assets"]["thumbnail"]["href"][last_slash_i + 1:]
        logger.info(f'file is on {item["assets"]["thumbnail"]["href"]},fake file is on {file}')
        open("lola_xml/product_browse/" + file, 'a').close()

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

    if save_xml:
        # create destination directoru if they don't exist
        Path(dest + "/product_external").mkdir(parents=True, exist_ok=True)
        Path(dest + "/product_external/data").mkdir(parents=True, exist_ok=True)
        Path(dest + "/product_browse").mkdir(parents=True, exist_ok=True)
        Path(dest + "/product_browse/data").mkdir(parents=True, exist_ok=True)

    for item in features:
        external_pds4 = create_product_external(item)
        browse_pds4 = create_product_browse(item)

        if save_xml:
            ex_path = dest + "/product_external/" + item["assets"]["data"]["title"] + "_product_external.xml"
            with open(ex_path, "w") as f:
                f.write(external_pds4)

            br_path = dest + "/product_browse/" + item["assets"]["data"]["title"] + "_product_browse.xml"
            with open(br_path, "w") as f:
                f.write(browse_pds4)


if __name__ == "__main__":
    main()
