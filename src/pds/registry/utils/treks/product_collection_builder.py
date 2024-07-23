"""Utility for creating Product_Collection PDS4 xml."""
import importlib.resources

from jinja2 import Environment
from pds.registry.utils.treks import templates


def create_collection_pds4(target):
    """Create Product_Collection PDS4 xml for the layers.

    :param target: target to create collection for

    :return: Product_Collection PDS4 xml
    """
    # create env
    env = Environment()

    with importlib.resources.open_text(templates, "product-collection-template.xml") as io:
        template_text = io.read()
        template = env.from_string(template_text)

        # fill out template params
        lid = f"urn:nasa:pds:context_pds3:{target}_trek_api"
        api_title = f"{target.capitalize()} Treks API"
        inventory_file_name = f"{target}_treks_layers_inventory.tab"

        context = {
            "lid": lid,
            "api_title": api_title,
            "inventory_file_name": inventory_file_name
        }

        return template.render(context)
