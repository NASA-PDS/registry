"""Script to build pds4 xml for Treks OGC WMTS layers.

The layers are scraped using the Treks API.
"""
import argparse
import logging
import time
from pathlib import Path

import requests

from .product_service_builder import ProductServiceBuilder
# import os
# import shutil


def main():
    """Generate PDS4 XML labels for Treks OGC/WMTS GIS Service."""
    # valid targets for treks
    valid_targets = [
        # planets
        "mars",
        "mercury",
        "venus",
        # moons (icy moons do not have listLayers json api)
        # "dione", DNE
        # "enceladus", DNE
        # "europa", DNE
        # "ganymede", dead link
        # "iapetus", DNE
        # "mimas", DNE
        "moon",
        "phobos",
        # "phoebe",
        # "rhea",
        # "tethys",
        "titan",
        # asteroids
        # "bennu", DNE
        "ceres",
        "ryugu",
        "vesta",
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
    target = target.strip()
    target = target.replace(" ", "")

    selected_targets = []
    if target == 'all':
        selected_targets = valid_targets[:-1]
    else:
        selected_targets = [target]

    # initialize logger
    logging.basicConfig(filename='create-treks-pds4-log.log', level=logging.ERROR)
    logging.error("target,product_label,missing_data_location,tag")

    for target in selected_targets:
        target_dest = dest + "/" + target
        # if verbose:
        print("Creating pds4 xml for target:", target)

        if save_xml:
            # create destination path if it does not exist
            Path(target_dest).mkdir(parents=True, exist_ok=True)

            # copy collection pds4 into the destination path
            # src = "titan-treks-api-collection.xml"
            # for root, _, files in os.walk("."):  # find path to src
            #     for name in files:
            #         if name == src:
            #             src = os.path.abspath(os.path.join(root, name))

            # if os.path.exists(src):
            #     # skip copy if file already exists
            #     if not os.path.exists(target_dest + "/titan-treks-api-collection.xml"):
            #         shutil.copy2(src, dest)

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
            if verbose:
                print("Creating pds4 xml for doc:", i)

            data = docs[i]
            label = data["productLabel"]
            print(f"[{i} / {len(docs) - 1}] | Creating PDS4 label for: {label}")
            psb = ProductServiceBuilder(data=data, target=target, save_xml=save_xml, dest=target_dest, verbose=verbose)
            _, lidvid = psb.create_pds4_xml()
            entry = "P," + lidvid + "\n"
            inventory_entries.append(entry)

        end_time = time.time()
        total = end_time - start_time
        print(f"Took {total} seconds to run")

        # create collection inventory file
        if save_xml:
            with open(target_dest + "/" + target + "_treks_layers_inventory.tab", "w") as f:
                for entry in inventory_entries:
                    f.write(entry)

            if verbose:
                print("Collection inventory saved")


if __name__ == "__main__":
    main()
