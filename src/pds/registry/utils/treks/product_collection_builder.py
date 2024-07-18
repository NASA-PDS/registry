"""Utility for creating Product_Collection PDS4 xml."""
from jinja2 import Environment
from jinja2 import FileSystemLoader


def create_collection_pds4(templates_path, template_name, target, verbose):
    """Create Product_Collection PDS4 xml for the layers.

    :return: Product_Collection PDS4 xml
    """
    # create env
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(template_name)

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
