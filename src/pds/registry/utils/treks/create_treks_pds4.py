"""Script to build pds4 xml for Treks OGC WMTS layers.

The layers are scraped using the Treks API.
"""
import argparse
import logging
from pathlib import Path

import requests
from pds.registry.utils.treks.product_collection_builder import create_collection_pds4
from pds.registry.utils.treks.product_service_builder import ProductServiceBuilder


def main():
    """Generate PDS4 XML labels for Treks OGC/WMTS GIS Service."""
    # valid targets for treks
    valid_targets = [
        # planets
        "mars",
        "mercury",
        "venus",
        # moons
        "moon",
        "phobos",
        "titan",
        # asteroids
        "ceres",
        "ryugu",
        "vesta",
        # run script on all targets
        "all"
    ]

    # set up command line args
    parser = argparse.ArgumentParser(description="Create and save pds4 xml labels created for Treks",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-s",
                        "--save-xml",
                        action="store_true",
                        help="True if you want the xml files to be saved",
                        default=True)
    parser.add_argument("-d",
                        "--destination-directory",
                        help="Directory to save pds4 xml files",
                        default="treks_xml")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Enable logging",
                        default=False)
    parser.add_argument("-t",
                        "--target",
                        help=f"Treks target to generate labels for: {valid_targets}",
                        default="titan")

    args = parser.parse_args()

    # parse args
    save_xml = args.save_xml
    dest = args.destination_directory
    verbose = args.verbose
    target = args.target.lower()

    # remove whitespace from target
    target = target.strip().replace(" ", "")

    selected_targets = []
    if target == 'all':
        selected_targets = valid_targets[:-1]
    else:
        selected_targets = [target]

    # initialize logger
    if verbose:
        logging.basicConfig(filename='create-treks-pds4-log.log', level=logging.WARNING)
        logging.warning("target,product_label,missing_data_location,tag")

    for target in selected_targets:
        target_dest = dest + "/" + target

        if save_xml:
            # create destination path if it does not exist
            Path(target_dest).mkdir(parents=True, exist_ok=True)

        # get json from url
        url = "https://trek.nasa.gov/" + target + "/TrekServices/ws/index/eq/" + \
            "listVisibleLayers?proj=urn:ogc:def:crs:EPSG::60620&start=0&rows=2147483647"
        response = requests.get(url, timeout=30)
        json_data = response.json()

        # get data from response
        start = json_data["response"]["start"]
        docs = json_data["response"]["docs"]

        # go through each doc and make pds4 xml
        inventory_entries = []
        for i in range(start, len(docs)):

            data = docs[i]

            psb = ProductServiceBuilder(data=data,
                                        target=target,
                                        save_xml=save_xml,
                                        dest=target_dest,
                                        verbose=verbose)

            service_pds4, lidvid = psb.create_pds4_xml()

            if save_xml:
                save_path = target_dest + "/" + data["productLabel"].lower() + ".xml"
                with open(save_path, "w") as f:
                    f.write(service_pds4)

            entry = "P," + lidvid + "\n"
            inventory_entries.append(entry)

        if save_xml:
            # create collection inventory file
            with open(target_dest + "/" + target + "_treks_layers_inventory.tab", "w") as f:
                for entry in inventory_entries:
                    f.write(entry)

            # create product collection file
            collection_pds4 = create_collection_pds4(target)
            with open(target_dest + "/" + target + "_treks_api_collection.xml", "w") as f:
                f.write(collection_pds4)


if __name__ == "__main__":
    main()
