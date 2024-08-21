"""Utility for create_treks_pds4.py to build pds4 xml."""
import importlib
import logging
import xml.etree.ElementTree as Et
from datetime import date

import requests
from jinja2 import Environment
from pds.registry.utils.treks import templates


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
        self.context = {}

        # load in fgdc
        self.fgdc_root = self.get_fgdc()

        # get target info
        self.target_type = None
        self.target_lid = None
        try:
            name = self.target.capitalize()
            pds_query_url = \
                f"https://pds.nasa.gov/api/search/1/products?q=(pds:Target.pds:name%20eq%20%22{name}%22)"
            response = requests.get(pds_query_url, timeout=30)
            # search type of first hit
            self.target_type = response.json()["data"][0]["properties"]["pds:Target.pds:type"][0]
            self.target_lid = response.json()["data"][0]["properties"]["lid"][0]

        except Exception:
            if self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},target or pds:Target.pds:type not found in pds,Observing_System_Component")

    def create_pds4_xml(self):
        """Creates the pds4 xml labels for the given data.

        :return: pds4 xml populated with the given data, lidvid
        """
        # fill out context
        lidvid = self.create_identification_area()
        self.create_observation_area()
        self.create_service()
        self.create_reference_list()

        # create env
        env = Environment()

        # get template
        with importlib.resources.open_text(templates, "product-service-template.xml") as io:
            template_text = io.read()
            template = env.from_string(template_text)

            # create pds4
            return template.render(self.context), lidvid

    def create_identification_area(self):
        """Creates Identification_Area for pds4 label.

        :return: lidvid
        """
        # TODO: create bundleID and collectionID
        logical_identifier = "urn:nasa:pds:treks:" + self.target + "_treks_layers:" + self.data["productLabel"].lower()
        version_id = str(1.0)
        lidvid = logical_identifier + "::" + version_id
        self.context["lid"] = logical_identifier  # productID needs to lowercase
        self.context["vid"] = version_id  # TODO: increment version as needed
        self.context["title"] = self.data["title"]

        self.context["modification_date"] = str(date.today())

        return lidvid

    def create_observation_area(self):
        """Creates Observation_Area for pds4 label."""
        # Time_Coordinates subtree
        self.create_time_coordinates()

        # Observing_System subtree
        observing_system_components = []
        if "Spacecraft" in self.data:
            component = []
            component.append(self.data["Spacecraft"])
            component.append("Spacecraft")
            observing_system_components.append(component)

        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},Spacecraft not found in json,Observing_System_Component")

        if "instrument" in self.data:
            component = []
            component.append(self.data["instrument"])
            component.append("Instrument")
            observing_system_components.append(component)

        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},instrument not found in json,Observing_System_Component")

        self.context["observing_system_components"] = observing_system_components

        # Target_Identification subtree
        self.context["target"] = self.target.capitalize()
        self.context["target_type"] = self.target_type

        # Discipline_Area subtree
        self.create_discipline_area()

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

                # add in context
                self.context["start_time"] = start

            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},begdate tag empty in fgdc,start_date_time")
        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},begdate tag not found in fgdc,start_date_time")

        # repeat for stop time
        stop = self.fgdc_root.find(".//enddate")
        if stop is not None:
            stop = stop.text

            if stop is not None:
                y_stop = stop[:4]
                m_stop = stop[4:6]
                d_stop = stop[6:]
                stop = y_stop + '-' + m_stop + '-' + d_stop

                self.context["stop_time"] = stop

            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},enddate tag empty in fgdc,stop_date_time")
        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},enddate tag not found in fgdc,stop_date_time")

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

                        self.context["start_time"] = date
                        self.context["stop_time"] = date

                    elif self.verbose:
                        label = self.data["productLabel"]
                        logging.warning(f"{self.target},{label},caldate tag empty in fgdc,Time_Coordinates")
                elif self.verbose:
                    label = self.data["productLabel"]
                    logging.warning(f"{self.target},{label},caldate tag not found in fgdc,Time_Coordinates")
            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},sngdate tag not found in fgdc,Time_Coordinates")

        return time_coordinates

    def create_discipline_area(self):
        """Creates Discipline_Area association for Observation_Area."""
        # many attributes/ associations missing in data that pds4 spec has a cardinality requirement for
        self.context["lid_ref"] = self.data["productLabel"].lower()

        bbox = self.data["bbox"].split(',')  # west, south, east, north
        self.context["bbox_west"] = bbox[0]
        self.context["bbox_south"] = bbox[1]
        self.context["bbox_east"] = bbox[2]
        self.context["bbox_north"] = bbox[3]

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
            self.context["unit"] = unit

            # ensure resolutions exist
            if lat_res is not None:
                self.context["lat_res"] = lat_res.text
            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},latres tag not found in fgdc,cart:latitude_resolution")

            if lon_res is not None:
                self.context["lon_res"] = lon_res.text
            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},longres tag not found in fgdc,cart:longitude_resolution")
        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},geounit tag not found in fgdc,resolution units")

        # get geodetic model infro from fgdc
        geodetic = self.fgdc_root.find(".//geodetic")

        # ensure geodertic info exists
        if geodetic is not None:
            # get name
            ellips = geodetic.find(".//ellips")

            if ellips is not None:
                self.context["spheroid_name"] = ellips.text
            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},ellips tag not found in fgdc,cart:spheroid_name")

            # get axis info
            semiaxis = geodetic.find(".//semiaxis")

            if semiaxis is not None:
                self.context["axis_radius"] = semiaxis.text
                # Do I need denominator of flattening ratio?
            elif self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},semiaxis tag not found in fgdc,cart:a/b/c_axis_radius")

            if self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},longitude direction not found,cart:longitude_direction")

    def create_service(self):
        """Creates Service for pds4 label."""
        self.context["name"] = self.data["title"]

        # get description from fgdc
        abstract = self.fgdc_root.find(".//abstract")

        # ensure abstract exists
        if abstract is not None:
            self.context["abstract"] = abstract.text
        elif "description" in self.data:
            self.context["abstract"] = self.data["description"]
        elif self.verbose:
            label = self.data["productLabel"]
            logging.warning(f"{self.target},{label},description not found,abstract_desc")

        # capabilities url uses a capital first letter
        capabilities_url = "https://trek.nasa.gov/tiles/" + self.target.capitalize() + "/EQ/" + \
            self.data["productLabel"] + "/1.0.0/WMTSCapabilities.xml"

        fgdc_url = "https://trek.nasa.gov/" + self.target + "/TrekWS/rest/cat/metadata/stream?label=" + self.data["productLabel"]

        gui_url = "https://trek.nasa.gov/" + self.target + \
            "/#v=0.1&x=0&y=0&z=1&p=urn%3Aogc%3Adef%3Acrs%3AIAU2000%3A%3A60600&d=&l=" + \
            self.data["productLabel"] + "%2Ctrue%2C1"

        self.context["capabilities_url"] = capabilities_url
        self.context["fgdc_url"] = fgdc_url
        self.context["gui_url"] = gui_url

        self.context["release_date"] = self.data["data_created_date"][:10]

    def create_reference_list(self):
        """Creates Reference_Area for pds4 labeel."""
        self.context["target_lid"] = self.target_lid

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
            if self.verbose:
                label = self.data["productLabel"]
                logging.warning(f"{self.target},{label},broken fgdc link or xml {url},fgdc")
            return Et.Element("")
