"""Script to build pds4 xml for Titan Treks OGC WMTS layers.

The layers are scraped using the Titan Treks API.
"""
import argparse
from pathlib import Path

import requests

from . import product_service_builder as psb


def main():
    """Main function of script."""
    # set up command line args
    parser = argparse.ArgumentParser(description="Customize save pds4 xml labels created for Titan Treks",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-s",
                        "--save-xml",
                        action="store_true",
                        help="True if you want the xml files to be saved",
                        default=True)
    parser.add_argument("-d",
                        "--destination-directory",
                        help="Directory to save pds4 xml files",
                        default="xml_files/product_service")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Verbosity of file creation",
                        default=False)

    args = parser.parse_args()
    config = vars(args)

    # parse args
    save_xml = config['save_xml']
    dest = config['destination_directory']
    verbose = config['verbose']

    # create destination path if it does not exist
    if save_xml:
        Path(dest).mkdir(parents=True, exist_ok=True)

    # get json from url
    url = "https://trek.nasa.gov/titan/TrekServices/ws/index/eq/" + \
        "listVisibleLayers?proj=urn:ogc:def:crs:EPSG::60620&start=0&rows=2147483647"
    response = requests.get(url)
    json_data = response.json()

    # get data from response
    num_found = json_data["response"]["numFound"]
    start = json_data["response"]["start"]
    docs = json_data["response"]["docs"]

    # go through each doc and make pds4 xml
    inventory_entries = []
    for i in range(start, num_found):
        if verbose:
            print("Creating pds4 xml for doc:", i)

        data = docs[i]
        _, lidvid = psb.create_pds4_xml(data=data, save_xml=save_xml, dest=dest, verbose=verbose)
        entry = "P," + lidvid + "\n"
        inventory_entries.append(entry)

    # create collection inventory file
    if save_xml:
        with open(dest + "/titan_treks_layers_inventory.tab", "w") as f:
            for entry in inventory_entries:
                f.write(entry)

        if verbose:
            print("Collection inventory saved")


if __name__ == "__main__":
    main()
