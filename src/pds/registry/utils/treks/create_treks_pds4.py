"""Script to build pds4 xml for Treks OGC WMTS layers.

The layers are scraped using the Treks API.
"""
import argparse
import logging
import os
import time
from pathlib import Path

import requests

from .product_collection_builder import create_collection_pds4
from .product_service_builder import ProductServiceBuilder


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
                        help="Verbosity of file creation",
                        default=False)
    parser.add_argument("-l",
                        "--save-logs",
                        action="store_true",
                        help="Save logs of run",
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
    save_logs = args.save_logs
    target = args.target.lower()

    # remove whitespace from target
    target = target.strip()
    target = target.replace(" ", "")

    selected_targets = []
    if target == 'all':
        selected_targets = valid_targets[:-1]
    else:
        selected_targets = [target]

    # initialize logger
    if save_logs:
        logging.basicConfig(filename='create-treks-pds4-log.log', level=logging.WARNING)
        logging.warning("target,product_label,missing_data_location,tag")

    total_start = time.time()
    for target in selected_targets:
        target_dest = dest + "/" + target

        if verbose:
            print("Creating pds4 xml for target:", target)

        if save_xml:
            # create destination path if it does not exist
            Path(target_dest).mkdir(parents=True, exist_ok=True)

        # get json from url
        url = "https://trek.nasa.gov/" + target + "/TrekServices/ws/index/eq/" + \
            "listVisibleLayers?proj=urn:ogc:def:crs:EPSG::60620&start=0&rows=2147483647"
        response = requests.get(url, timeout=30)
        json_data = response.json()

        # get data from response
        # num_found = json_data["response"]["numFound"]
        start = json_data["response"]["start"]
        docs = json_data["response"]["docs"]

        # go through each doc and make pds4 xml
        inventory_entries = []
        start_time = time.time()
        for i in range(start, len(docs)):

            data = docs[i]

            # if verbose:
            label = data["productLabel"]
            print(f"[{i} / {len(docs) - 1}] | Creating PDS4 label for: {label}")

            psb = ProductServiceBuilder(data=data,
                                        target=target,
                                        save_xml=save_xml,
                                        dest=target_dest,
                                        verbose=verbose,
                                        save_logs=save_logs)

            _, lidvid = psb.create_pds4_xml()
            entry = "P," + lidvid + "\n"
            inventory_entries.append(entry)

        if verbose:
            end_time = time.time()
            total = end_time - start_time
            print(f"{target.capitalize()} layers took {total:.3f} seconds to build")

        if save_xml:
            # create collection inventory file
            with open(target_dest + "/" + target + "_treks_layers_inventory.tab", "w") as f:
                for entry in inventory_entries:
                    f.write(entry)

            if verbose:
                print(f"Collection inventory saved for {target}")

            # create product collection file
            template_path = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(template_path, 'templates')
            template_name = "product-collection-template.xml"

            collection_pds4 = create_collection_pds4(template_path, template_name, target, verbose)
            with open(target_dest + "/" + target + "_treks_api_collection.xml", "w") as f:
                f.write(collection_pds4)

            if verbose:
                print(f"Product_Collection PDS4 saved for {target}")

    total_end = time.time()
    if args.target.lower() == "all" and verbose:
        total_time = total_end - total_start
        print(f"All layers took {total_time:.3f} seconds to build")


if __name__ == "__main__":
    main()
