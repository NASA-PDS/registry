"""Utility for create_titan_treks.py to build pds4 xml."""
import xml.etree.ElementTree as Et
from datetime import date

import requests
from bs4 import BeautifulSoup

#
# This code is very specific to Titan Treks (ie hardcoded urls),
# but should be able to be generalized easily to other Treks APIs.
# Currently just a proof of concept for a tool
#


def create_pds4_xml(data, save_xml=False, dest="xml_files", verbose=False):
    """Creates the pds4 xml labels for the given data.

    :param data: Titan json data from Treks api
    :param save_xml: True if files will be saved
    :param dest: directory path to save files in
    :param verbose: display tree when finished

    :return: pds4 xml populated with the given data
    """
    # get necessary subtrees
    identification_area, lidvid = create_identification_area(data, verbose)
    observation_area = create_observation_area(data, verbose)
    service = create_service(data, verbose)
    # TODO: add reference list?

    # create root
    root = Et.Element("Product_Service")

    # add attributes to the root
    xmlns = "http://pds.nasa.gov/pds4/pds/v1"
    xmlns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
    xsi_schema_location = "http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1M00.xsd"
    xmlns_cart = "http://pds.nasa.gov/pds4/cart/v1"

    root.set("xmlns", xmlns)
    root.set("xmlns:xsi", xmlns_xsi)
    root.set("xmlns:cart", xmlns_cart)
    root.set("xsi:schemaLocation", xsi_schema_location)

    # create full tree
    root.append(identification_area)
    root.append(observation_area)
    root.append(service)

    tree = Et.ElementTree(root)

    # make tree pretty
    Et.indent(tree, space="\t", level=0)
    name = data["productLabel"]

    if verbose:
        print("\n------------------------------------------------------------------------------")
        print("Created Tree:")
        print(Et.tostring(root))
        print("-----------------------------------------------------------------------------\n")

    if save_xml:
        tree.write(dest + f"/{name}_Product_Service.xml")

        if verbose:
            print(f"Successfully Saved File {name}_Product_Service.xml")

    return tree, lidvid


def create_identification_area(data, verbose=False):
    """Creates Identification_Area for pds4 label.

    :param data: Titan json data from Treks api
    :param verbose: display subtree when finished

    :return: Identification_Area section of pds4 xml, lidvid of file
    """
    identification_area = Et.Element("Identification_Area")

    # TODO: create bundleID and collectionID
    logical_identifier = "urn:nasa:pds:treks:titan_treks_layers:" + data["productLabel"].lower()
    version_id = str(1.0)
    lidvid = logical_identifier + "::" + version_id
    Et.SubElement(identification_area, "logical_identifier").text = logical_identifier  # productID needs to lowercase
    Et.SubElement(identification_area, "version_id").text = version_id  # TODO: increment version as needed
    Et.SubElement(identification_area, "title").text = data["title"]
    Et.SubElement(identification_area, "information_model_version").text = "1.22.0.0"
    Et.SubElement(identification_area, "product_class").text = "Product_Service"

    modification_history = Et.SubElement(identification_area, "Modification_History")
    modification_detail = Et.SubElement(modification_history, "Modification_Detail")

    Et.SubElement(modification_detail, "modification_date").text = str(date.today())
    Et.SubElement(modification_detail, "version_id").text = str(1.0)  # increment as needed
    Et.SubElement(modification_detail, "description").text = "Exposing GIS services in the PDS4 registry"

    if verbose:
        print("\n-----------------------------------------------------------------------------")
        print("Created Identifcation_Area Tag:")
        print(Et.tostring(identification_area))
        print("-----------------------------------------------------------------------------\n")

    return identification_area, lidvid


def create_observation_area(data, verbose=False):
    """Creates Observation_Area for pds4 label.

    :param data: Titan json data from Treks api
    :param verbose: display subtree when finished

    :return: Observation_Area section of pds4 xml
    """
    observation_area = Et.Element("Observation_Area")

    # Time_Coordinates subtree
    observation_area.append(create_time_coordinates(data, verbose))

    # Investigation_Area subtree
    investigation_area = Et.SubElement(observation_area, "Investigation_Area")

    Et.SubElement(investigation_area, "name").text = "Treks Open Geospatial Consortium Web Mapping Tile Service"
    Et.SubElement(investigation_area, "type").text = "OGC WMTS"

    internal_reference = Et.SubElement(investigation_area, "Internal_Reference")
    Et.SubElement(internal_reference, "lid_reference").text = "urn:nasa:pds:ogc:wmts"
    # TODO: add lidvid_reference ? it was not in Trent's xml but required by pds4 docs
    Et.SubElement(internal_reference, "reference_type").text = "lid_reference"

    # Observing_System subtree
    observing_system = Et.SubElement(observation_area, "Observing_System")

    # not all observations have "Spacecraft" key
    if "Spacecraft" in data:
        observing_system_component_spacecraft = Et.SubElement(observing_system, "Observing_System_Component")
        Et.SubElement(observing_system_component_spacecraft, "name").text = data["Spacecraft"]
        Et.SubElement(observing_system_component_spacecraft, "type").text = "Spacecraft"

    observing_system_component_instrument = Et.SubElement(observing_system, "Observing_System_Component")
    Et.SubElement(observing_system_component_instrument, "name").text = data["instrument"]
    Et.SubElement(observing_system_component_instrument, "type").text = "Instrument"

    # Data object was not in Trent's xml but required according to pds4 documentation
    # Et.SubElement(observing_system, "data_object").text = "Physical_Object"
    # Conceptual_Object mentions it's not digital, but Physical_Object does not mention anything

    # Target_Identification subtree
    target_identification = Et.SubElement(observation_area, "Target_Identification")

    Et.SubElement(target_identification, "name").text = "Titan"
    Et.SubElement(target_identification, "type").text = "Satellite"

    # Discipline_Area subtree
    observation_area.append(create_discipline_area(data, verbose))

    if verbose:
        print("\n------------------------------------------------------------------------------")
        print("Created Observation_Area Tag:")
        print(Et.tostring(observation_area))
        print("-----------------------------------------------------------------------------\n")

    return observation_area


def create_time_coordinates(data, verbose=False):
    """Creates Time_Coordinates association for Observation_Area.

    :param data: Titan json data from Treks api
    :param verbose: display subtree when finished

    :return: Time_Coordinates section of pds4 xml
    """
    time_coordinates = Et.Element("Time_Coordinates")

    # load in fgdc xml
    url = "https://trek.nasa.gov/titan/TrekWS/rest/cat/metadata/stream?label=" + data["productLabel"]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, features='xml')

    # get times from fgdc metadata
    start = soup.find("begdate")

    # ensure the metadata exists
    if start:
        start = start.contents[0]

        # format dates
        y_start = start[:4]
        m_start = start[4:6]
        d_start = start[6:]
        start = y_start + '-' + m_start + '-' + d_start

        # add in data
        Et.SubElement(time_coordinates, "start_date_time").text = start

    # repeat for stop time
    stop = soup.find("enddate")
    if stop:
        stop = stop.contents[0]

        y_stop = stop[:4]
        m_stop = stop[4:6]
        d_stop = stop[6:]
        stop = y_stop + '-' + m_stop + '-' + d_stop

        Et.SubElement(time_coordinates, "stop_date_time").text = stop

    if verbose:
        print("\n-----------------------------------------------------------------------------")
        print("Created Time_Coordinates Tag:")
        print(Et.tostring(time_coordinates))
        print("-----------------------------------------------------------------------------\n")

    return time_coordinates


def create_discipline_area(data, verbose=False):
    """Creates Discipline_Area association for Observation_Area.

    :param data: Titan json data from Treks api
    :param verbose: display subtree when finished

    :return: Discipline_Area section of pds4 xml
    """
    # many attributes/ associations missing in data that pds4 spec has a cardinality requirement for
    discipline_area = Et.Element("Discipline_Area")
    cartography = Et.SubElement(discipline_area, "cart:Cartography")

    lir = Et.SubElement(cartography, "Local_Internal_Reference")
    Et.SubElement(lir, "local_identifier_reference").text = data["productLabel"].lower()
    Et.SubElement(lir, "local_reference_type").text = "cartography_parameters_to_service"

    spatial_domain = Et.SubElement(cartography, "cart:Spatial_Domain")
    bounding_coordinates = Et.SubElement(spatial_domain, "cart:Bounding_Coordinates")
    trek_bbox = data["trekBbox"].split(',')  # west, south, east, north

    Et.SubElement(bounding_coordinates, "cart:west_bounding_coordinate", unit="deg").text = trek_bbox[0]
    Et.SubElement(bounding_coordinates, "cart:south_bounding_coordinate", unit="deg").text = trek_bbox[1]
    Et.SubElement(bounding_coordinates, "cart:east_bounding_coordinate", unit="deg").text = trek_bbox[2]
    Et.SubElement(bounding_coordinates, "cart:north_bounding_coordinate", unit="deg").text = trek_bbox[3]

    sri = Et.SubElement(cartography, "cart:Spatial_Reference_Information")
    hcsd = Et.SubElement(sri, "cart:Horizontal_Coordinate_System_Definition")

    geographic = Et.SubElement(hcsd, "cart:Geographic")
    Et.SubElement(geographic, "cart:latitude_resolution", unit="arcsec").text = str(data["resolution"])
    Et.SubElement(geographic, "cart:longitude_resolution", unit="arcsec").text = str(data["resolution"])

    geodetic_model = geographic = Et.SubElement(hcsd, "cart:Geodetic_Model")
    Et.SubElement(geodetic_model, "cart:latitude_type").text = "Planetocentric"
    Et.SubElement(geodetic_model, "cart:spheroid_name").text = "Titan (2015) - Sphere"

    # hacky but works well to find radius, could use wkt parser
    projection = data["projection"]
    spheroid_i = projection.find("SPHEROID")                    # get spheroid projection header in ogc wmts data
    spheroid = projection[spheroid_i:]
    comma1 = spheroid.find(',')                                 # find value of spheroid header
    comma2 = spheroid[comma1 + 1:].find(',')
    axis_radius = spheroid[comma1 + 1:comma1 + comma2 + 1]            # get value of sphereoid header
    float_i = axis_radius.find('.')                             # standardize data type, not all values are float
    if float_i != -1:
        axis_radius = axis_radius[:float_i]

    axis_radius = int(axis_radius)                              # use int since it's the lowest precision used

    Et.SubElement(geodetic_model, "cart:a_axis_radius", unit="m").text = str(axis_radius)
    Et.SubElement(geodetic_model, "cart:b_axis_radius", unit="m").text = str(axis_radius)
    Et.SubElement(geodetic_model, "cart:c_axis_radius", unit="m").text = str(axis_radius)
    Et.SubElement(geodetic_model, "cart:longitude_direction").text = "Positive East"

    if verbose:
        print("\n------------------------------------------------------------------------------")
        print("Created Discipline_Area Tag:")
        print(Et.tostring(discipline_area))
        print("-----------------------------------------------------------------------------\n")

    return discipline_area


def create_service(data, verbose=False):
    """Creates Service for pds4 label.

    :param data: Titan json data from Treks api
    :param verbose: display subtree when finished

    :return: Service section of pds4 xml
    """
    service = Et.Element("Service")

    Et.SubElement(service, "name").text = data["title"]
    Et.SubElement(service, "abstract_desc").text = data["description"]

    # urls: wmts capabilities, fgdc, treks product
    # & are not escaping and the encoding breaks the link for treks
    treks_url = "https://trek.nasa.gov/titan/#v=0.1&x=0&y=0&z=1&p=urn%3Aogc%3Adef%3Acrs%3AIAU2000%3A%3A60600&d=&l=" + \
        data["productLabel"] + "%2Ctrue%2C1"
    urls = [
        "https://trek.nasa.gov/tiles/Titan/EQ/" + data["productLabel"] + "/1.0.0/WMTSCapabilities.xml",
        "https://trek.nasa.gov/titan/TrekWS/rest/cat/metadata/stream?label=" + data["productLabel"],
        treks_url
    ]
    for url in urls:
        Et.SubElement(service, "url").text = url

    Et.SubElement(service, "release_date").text = data["data_created_date"][:10]
    Et.SubElement(service, "service_type").text = "OGC WMTS"
    Et.SubElement(service, "category").text = "Visualization"

    if verbose:
        print("\n------------------------------------------------------------------------------")
        print("Created Service Tag:")
        print(Et.tostring(service))
        print("-----------------------------------------------------------------------------\n")

    return service
