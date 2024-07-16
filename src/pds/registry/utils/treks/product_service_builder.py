"""Utility for create_treks_pds4.py to build pds4 xml."""
import logging
import xml.etree.ElementTree as Et
from datetime import date

import requests


class ProductServiceBuilder:
    """Builder class for pds4 xml files."""
    def __init__(self, data, target, save_xml=False, dest="xml_files", verbose=False):
        """Constructor for ProductServiceBuilder.

        :param data: json data from Treks api
        :param target: Treks target of the data
        :param save_xml: True if files will be saved
        :param dest: directory path to save files in
        :param verbose: display tree when finished
        """
        # initialized params
        self.data = data
        self.target = target
        self.save_xml = save_xml
        self.dest = dest
        self.verbose = verbose

        # load in fgdc
        self.fgdc_root = self.get_fgdc()

        # initialize logger
        logging.basicConfig(filename='myapp.log', level=logging.ERROR)

    def create_pds4_xml(self):
        """Creates the pds4 xml labels for the given data.

        :return: pds4 xml populated with the given data, lidvid
        """
        # get necessary subtrees
        identification_area, lidvid = self.create_identification_area(self.data, self.target, self.verbose)
        observation_area = self.create_observation_area(self.data, self.target, self.verbose)
        service = self.create_service(self.data, self.target, self.verbose)
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
        name = self.data["productLabel"]

        if self.verbose:
            print("\n------------------------------------------------------------------------------")
            print("Created Tree:")
            print(Et.tostring(root))
            print("-----------------------------------------------------------------------------\n")

        if self.save_xml:
            tree.write(self.dest + f"/{name}_Product_Service.xml")

            if self.verbose:
                print(f"Successfully Saved File {name}_Product_Service.xml")

        return tree, lidvid

    def create_identification_area(self):
        """Creates Identification_Area for pds4 label.

        :return: Identification_Area section of pds4 xml, lidvid
        """
        identification_area = Et.Element("Identification_Area")

        # TODO: create bundleID and collectionID
        logical_identifier = "urn:nasa:pds:treks:" + self.target + "_treks_layers:" + self.data["productLabel"].lower()
        version_id = str(1.0)
        lidvid = logical_identifier + "::" + version_id
        Et.SubElement(identification_area, "logical_identifier").text = logical_identifier  # productID needs to lowercase
        Et.SubElement(identification_area, "version_id").text = version_id  # TODO: increment version as needed
        Et.SubElement(identification_area, "title").text = self.data["title"]
        Et.SubElement(identification_area, "information_model_version").text = "1.22.0.0"
        Et.SubElement(identification_area, "product_class").text = "Product_Service"

        modification_history = Et.SubElement(identification_area, "Modification_History")
        modification_detail = Et.SubElement(modification_history, "Modification_Detail")

        Et.SubElement(modification_detail, "modification_date").text = str(date.today())
        Et.SubElement(modification_detail, "version_id").text = str(1.0)  # increment as needed
        Et.SubElement(modification_detail, "description").text = "Exposing GIS services in the PDS4 registry"

        if self.verbose:
            print("\n-----------------------------------------------------------------------------")
            print("Created Identifcation_Area Tag:")
            print(Et.tostring(identification_area))
            print("-----------------------------------------------------------------------------\n")

        return identification_area, lidvid

    def create_observation_area(self):
        """Creates Observation_Area for pds4 label.

        :return: Observation_Area section of pds4 xml
        """
        observation_area = Et.Element("Observation_Area")

        # Time_Coordinates subtree
        observation_area.append(self.create_time_coordinates())

        # Investigation_Area subtree
        investigation_area = Et.SubElement(observation_area, "Investigation_Area")

        # TODO: ADD MISSION DATA HERE OR REFER TO TREKS??
        Et.SubElement(investigation_area, "name").text = "Treks Open Geospatial Consortium Web Mapping Tile Service"
        Et.SubElement(investigation_area, "type").text = "OGC WMTS"

        internal_reference = Et.SubElement(investigation_area, "Internal_Reference")
        Et.SubElement(internal_reference, "lid_reference").text = "urn:nasa:pds:ogc:wmts"
        # TODO: add lidvid_reference ? it was not in Trent's xml but required by pds4 docs
        Et.SubElement(internal_reference, "reference_type").text = "lid_reference"

        # Observing_System subtree
        observing_system = Et.SubElement(observation_area, "Observing_System")

        if "Spacecraft" in self.data:
            observing_system_component_spacecraft = Et.SubElement(observing_system, "Observing_System_Component")
            Et.SubElement(observing_system_component_spacecraft, "name").text = self.data["Spacecraft"]
            Et.SubElement(observing_system_component_spacecraft, "type").text = "Spacecraft"
        else:
            label = self.data["productLabel"]
            logging.error(f"Spacecraft not found in json for product label {label} of target {self.target}")

        if "instrument" in self.data:
            observing_system_component_instrument = Et.SubElement(observing_system, "Observing_System_Component")
            Et.SubElement(observing_system_component_instrument, "name").text = self.data["instrument"]
            Et.SubElement(observing_system_component_instrument, "type").text = "Instrument"
        else:
            label = self.data["productLabel"]
            logging.error(f"instrument not found in json for product label {label} of target {self.target}")

        # Data object was not in Trent's xml but required according to pds4 documentation
        # Et.SubElement(observing_system, "data_object").text = "Physical_Object"
        # Conceptual_Object mentions it's not digital, but Physical_Object does not mention anything

        # Target_Identification subtree
        target_identification = Et.SubElement(observation_area, "Target_Identification")

        # TODO: GENERELAIZE THIS FIND IT IN THE FGDC OR IN THE JSON
        Et.SubElement(target_identification, "name").text = self.target.capitalize()
        # Et.SubElement(target_identification, "type").text = "Satellite"
        label = self.data["productLabel"]
        logging.error(f"Target identification type not found for product label {label} of target {self.target}")

        # Discipline_Area subtree
        observation_area.append(self.create_discipline_area())

        if self.verbose:
            print("\n------------------------------------------------------------------------------")
            print("Created Observation_Area Tag:")
            print(Et.tostring(observation_area))
            print("-----------------------------------------------------------------------------\n")

        return observation_area

    def create_time_coordinates(self):
        """Creates Time_Coordinates association for Observation_Area.

        :return: Time_Coordinates section of pds4 xml
        """
        time_coordinates = Et.Element("Time_Coordinates")

        # get times from fgdc metadata
        start = self.fgdc_root.find(".//begdate")

        # ensure the metadata exists
        if start is not None:
            start = start.text

            # ensure text exists
            if start is not None:
                # format dates
                y_start = start[:4]
                m_start = start[4:6]
                d_start = start[6:]
                start = y_start + '-' + m_start + '-' + d_start

                # add in data
                Et.SubElement(time_coordinates, "start_date_time").text = start

            else:
                label = self.data["productLabel"]
                logging.error(f"begdate tag empty in fgdc for product label {label} of target {self.target}")
        else:
            label = self.data["productLabel"]
            logging.error(f"begdate tag not found in fgdc for product label {label} of target {self.target}")

        # repeat for stop time
        stop = self.fgdc_root.find(".//enddate")
        if stop is not None:
            stop = stop.text

            if stop is not None:
                y_stop = stop[:4]
                m_stop = stop[4:6]
                d_stop = stop[6:]
                stop = y_stop + '-' + m_stop + '-' + d_stop

                Et.SubElement(time_coordinates, "stop_date_time").text = stop

            else:
                label = self.data["productLabel"]
                logging.error(f"enddate tag not found in fgdc for product label {label} of target {self.target}")
        else:
            label = self.data["productLabel"]
            logging.error(f"enddate tag not found in fgdc for product label {label} of target {self.target}")

        # check for single data
        if start is None and stop is None:
            sngdate = self.fgdc_root.find(".//sngdate")

            if sngdate is not None:
                caldate = sngdate.find(".//caldate")

                if caldate is not None and caldate.text is not None:
                    date = caldate.text

                    if date is not None:
                        year = date[:4]
                        month = date[4:6]
                        day = date[6:]
                        date = year + '-' + month + '-' + day

                        Et.SubElement(time_coordinates, "start_date_time").text = date
                        Et.SubElement(time_coordinates, "stop_date_time").text = date

                    else:
                        label = self.data["productLabel"]
                        logging.error(f"caldate tag empty in fgdc for product label {label} of target {self.target}")
                else:
                    label = self.data["productLabel"]
                    logging.error(f"caldate tag not found in fgdc for product label {label} of target {self.target}")
            else:
                label = self.data["productLabel"]
                logging.error(f"sngdate tag not found in fgdc for product label {label} of target {self.target}")

        if self.verbose:
            print("\n-----------------------------------------------------------------------------")
            print("Created Time_Coordinates Tag:")
            print(Et.tostring(time_coordinates))
            print("-----------------------------------------------------------------------------\n")

        return time_coordinates

    def create_discipline_area(self):
        """Creates Discipline_Area association for Observation_Area.

        :return: Discipline_Area section of pds4 xml
        """
        # many attributes/ associations missing in data that pds4 spec has a cardinality requirement for
        discipline_area = Et.Element("Discipline_Area")
        cartography = Et.SubElement(discipline_area, "cart:Cartography")

        lir = Et.SubElement(cartography, "Local_Internal_Reference")
        Et.SubElement(lir, "local_identifier_reference").text = self.data["productLabel"].lower()
        Et.SubElement(lir, "local_reference_type").text = "cartography_parameters_to_service"

        spatial_domain = Et.SubElement(cartography, "cart:Spatial_Domain")
        bounding_coordinates = Et.SubElement(spatial_domain, "cart:Bounding_Coordinates")

        bbox = self.data["bbox"].split(',')  # west, south, east, north
        Et.SubElement(bounding_coordinates, "cart:west_bounding_coordinate", unit="deg").text = bbox[0]
        Et.SubElement(bounding_coordinates, "cart:south_bounding_coordinate", unit="deg").text = bbox[1]
        Et.SubElement(bounding_coordinates, "cart:east_bounding_coordinate", unit="deg").text = bbox[2]
        Et.SubElement(bounding_coordinates, "cart:north_bounding_coordinate", unit="deg").text = bbox[3]

        sri = Et.SubElement(cartography, "cart:Spatial_Reference_Information")
        hcsd = Et.SubElement(sri, "cart:Horizontal_Coordinate_System_Definition")

        geographic = Et.SubElement(hcsd, "cart:Geographic")

        # get resolution from fgdc
        lat_res = self.fgdc_root.find(".//latres")
        lon_res = self.fgdc_root.find(".//longres")
        unit = self.fgdc_root.find(".//geogunit")

        # get units in pds4 format
        if unit is not None:
            pds4_unit_map = {
                "Decimal degrees": "deg",
                "Decimal seconds": "arcsec"
            }
            unit = pds4_unit_map[unit.text]

            # ensure resolutions exist
            if lat_res is not None:
                Et.SubElement(geographic, "cart:latitude_resolution", unit=unit).text = lat_res.text
            else:
                label = self.data["productLabel"]
                logging.error(f"latres tag not found in fgdc for product label {label} of target {self.target}")

            if lon_res is not None:
                Et.SubElement(geographic, "cart:longitude_resolution", unit=unit).text = lon_res.text
            else:
                label = self.data["productLabel"]
                logging.error(f"longres tag not found in fgdc for product label {label} of target {self.target}")
        else:
            label = self.data["productLabel"]
            logging.error(f"geounit tag not found in fgdc for product label {label} of target {self.target}")

        geodetic_model = geographic = Et.SubElement(hcsd, "cart:Geodetic_Model")

        # get geodetic model infro from fgdc
        geodetic = self.fgdc_root.find(".//geodetic")

        # ensure geodertic info exists
        if geodetic is not None:
            # get name
            ellips = geodetic.find(".//ellips")

            if ellips is not None:
                Et.SubElement(geodetic_model, "cart:spheroid_name").text = ellips.text
            else:
                label = self.data["productLabel"]
                logging.error(f"ellips tag not found in fgdc for product label {label} of target {self.target}")

            # TODO: FIND LATITUDE TYPE
            # Et.SubElement(geodetic_model, "cart:latitude_type").text = "Planetocentric"
            label = self.data["productLabel"]
            logging.error(f"Latitude type not found for product label {label} of target {self.target}")

            # get axis info
            semiaxis = geodetic.find(".//semiaxis")

            if semiaxis is not None:
                Et.SubElement(geodetic_model, "cart:a_axis_radius", unit="m").text = semiaxis.text
                Et.SubElement(geodetic_model, "cart:b_axis_radius", unit="m").text = semiaxis.text
                Et.SubElement(geodetic_model, "cart:c_axis_radius", unit="m").text = semiaxis.text
                # Do I need denominator of flattening ratio?
            else:
                label = self.data["productLabel"]
                logging.error(f"semiaxis/ axis radius not found in fgdc for product label {label} of target {self.target}")

            # TODO: FIND longitude direction (default positive east?)
            # Et.SubElement(geodetic_model, "cart:longitude_direction").text = "Positive East"
            label = self.data["productLabel"]
            logging.error(f"Longitude direction not found for product label {label} of target {self.target}")

        if self.verbose:
            print("\n------------------------------------------------------------------------------")
            print("Created Discipline_Area Tag:")
            print(Et.tostring(discipline_area))
            print("-----------------------------------------------------------------------------\n")

        return discipline_area

    def create_service(self):
        """Creates Service for pds4 label.

        :return: Service section of pds4 xml
        """
        service = Et.Element("Service")

        Et.SubElement(service, "name").text = self.data["title"]

        # get description from fgdc
        abstract = self.fgdc_root.find(".//abstract")

        # ensure abstract exists
        if abstract is not None:
            Et.SubElement(service, "abstract_desc").text = abstract.text
        elif "description" in self.data:
            Et.SubElement(service, "abstract_desc").text = self.data["description"]
        else:
            label = self.data["productLabel"]
            logging.error(f"Missing description in fgdc and json for product label {label} of target {self.target}")

        treks_url = "https://trek.nasa.gov/" + self.target + \
            "/#v=0.1&x=0&y=0&z=1&p=urn%3Aogc%3Adef%3Acrs%3AIAU2000%3A%3A60600&d=&l=" + \
            self.data["productLabel"] + "%2Ctrue%2C1"

        # capabilities url uses a capital first letter
        capabilities_url = "https://trek.nasa.gov/tiles/" + self.target.capitalize() + "/EQ/" + \
            self.data["productLabel"] + "/1.0.0/WMTSCapabilities.xml"

        # urls: wmts capabilities, fgdc, treks product
        urls = [
            capabilities_url,
            "https://trek.nasa.gov/" + self.target + "/TrekWS/rest/cat/metadata/stream?label=" + self.data["productLabel"],
            treks_url
        ]
        for url in urls:
            Et.SubElement(service, "url").text = url

        Et.SubElement(service, "release_date").text = self.data["data_created_date"][:10]
        Et.SubElement(service, "service_type").text = "OGC WMTS"
        Et.SubElement(service, "category").text = "Visualization"

        if self.verbose:
            print("\n------------------------------------------------------------------------------")
            print("Created Service Tag:")
            print(Et.tostring(service))
            print("-----------------------------------------------------------------------------\n")

        return service

    def get_fgdc(self):
        """Utility function to get fgdc metadata xml.

        Fgdc metadata does not always exist

        :return: fgdc xml if it exists, empty element tree otherwise
        """
        url = "https://trek.nasa.gov/" + self.target + \
            "/TrekWS/rest/cat/metadata/stream?label=" + self.data["productLabel"]
        try:
            response = requests.get(url, timeout=30)
            return Et.fromstring(response.content)

        except Exception:
            logging.error(f"Missing or broken fgdc metadata at: {url}")
            return Et.Element("")
