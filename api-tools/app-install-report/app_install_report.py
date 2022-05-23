#!/usr/bin/env python3

"""app_install_report.py.

Return a report of all apps, app versions, number of installations, device name, and serial
numbers where the, app is installed from a specified Kandji instance.
"""

###################################################################################################
# Created by Matt Wilson | support@kandji.io | Kandji, Inc.
###################################################################################################
#
# Created:  2021.06.03
# Modified: 2022.05.12
#
###################################################################################################
# Software Information
###################################################################################################
#
# This python3 script leverages the Kandji API to generate a CSV report containing a list of every
# installed application recorded by the Kandji Web App. The information includes application name,
# the application version, the device name, and the device serial numbers.
#
###################################################################################################
# License Information
###################################################################################################
# Copyright 2022 Kandji, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###################################################################################################

__version__ = "1.2.0"


# Standard library
import argparse
import csv
import pathlib
import sys

from datetime import datetime

# 3rd party imports

# Try to import the module. If the module cannot be imported let the user know so that they can
# install it.
try:
    import requests
except ImportError as import_error:
    sys.exit(
        "Looks like you need to install the requests module. Open a Terminal and run python3 -m "
        "pip install requests."
    )

from requests.adapters import HTTPAdapter

###################################################################################################
######################### UPDATE VARIABLES BELOW ##################################################
###################################################################################################


# Initialize some variables
# Kandji API base URL
BASE_URL = "https://example.clients.us-1.kandji.io/api/v1/"
# Kandji Bearer Token
TOKEN = "your_api_key_here"


###################################################################################################
######################### DO NOT MODIFY BELOW THIS LINE ###########################################
###################################################################################################

TODAY = datetime.today().strftime("%Y%m%d")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json;charset=utf-8",
    "Cache-Control": "no-cache",
}


REPORT_NAME = f"app_install_report_{datetime.today().strftime('%Y%m%d')}.csv"

# Current working directory
HERE = pathlib.Path("__file__").parent


def program_arguments():
    """Return arguments."""
    parser = argparse.ArgumentParser(
        prog="device_library_items",
        description=(
            "Get a report containing information for a given library item or all library items "
            " leveraging the Kandji API.\n"
        ),
        allow_abbrev=False,
    )

    parser.add_argument(
        "--name",
        type=str,
        metavar='"Atom"',
        help="Enter a specific app name. This will limit the search results to only"
        " the specified app",
        required=False,
    )

    parser.version = __version__
    parser.add_argument("--version", action="version", help="Show this tool's version.")
    # parser.add_argument("-v", "--verbose", action="store", metavar="LEVEL")

    return parser.parse_args()


def error_handling(resp, err_msg):
    """Handle the HTTP errors."""
    # 400
    if resp == requests.codes["bad_request"]:
        print("This request does not look right...")
        print(f"\t{err_msg}")
    # 401
    elif resp == requests.codes["unauthorized"]:
        print("Make sure that you have the required permissions to access this data.")
        print("Depending on the API platform this could mean that access has just been blocked.")
        sys.exit(f"\t{err_msg}")
    # 403
    elif resp == requests.codes["forbidden"]:
        print("The api key may be invalid or missing.")
        sys.exit(f"\t{err_msg}")
    # 404
    elif resp == requests.codes["not_found"]:
        print("We cannot find the one that you are looking for ...")
        print("Move along ...")
        print(f"\t{err_msg}")
    # 429
    elif resp == requests.codes["too_many_requests"]:
        print("You have reached the rate limit ...")
        print("Try again later ...")
        sys.exit(f"\t{err_msg}")
    # 500
    elif resp == requests.codes["internal_server_error"]:
        print("The service is having a problem...")
        sys.exit(err_msg)
    # 503
    elif resp == requests.codes["service_unavailable"]:
        print("Unable to reach the service. Try again later...")
    else:
        print("Something really bad must have happened...")
        print(err_msg)
        sys.exit()


def kandji_api(method, endpoint, params=None, payload=None):
    """Make an API request and return data.

    Returns a JSON data object.
    """
    attom_adapter = HTTPAdapter(max_retries=3)
    session = requests.Session()
    session.mount(BASE_URL, attom_adapter)

    try:
        response = session.request(
            method,
            BASE_URL + endpoint,
            data=payload,
            headers=HEADERS,
            params=params,
            timeout=30,
        )

        # If a successful status code is returned (200 and 300 range)
        if response:
            data = response.json()
        # if the request is successful exeptions will not be raised
        response.raise_for_status()

    except requests.exceptions.RequestException as err:
        error_handling(resp=response.status_code, err_msg=err)
        data = "Not found"

    return data


def generate_report_payload(devices, args):
    """Create a JSON payload."""
    # list of apps
    data = []

    # Loop over all Mac computers in Kandji
    for device in devices:

        device_apps = kandji_api(method="GET", endpoint=f"devices/{device['device_id']}/apps")

        # Loop over each app in the Kandji "apps" list and append to data dict
        for app in device_apps["apps"]:

            if args.name:

                if args.name == app["app_name"]:

                    # Create a dictionary containing the application name, version, and
                    # associated serial number.
                    apps_dict = {
                        "serial_number": device["serial_number"].upper(),
                        "device_name": device["device_name"],
                        "os_version": device["os_version"],
                        "user": device["user"],
                        "platform": device["platform"],
                        "app_name": app["app_name"],
                        "version": app["version"],
                    }

                    data.append(apps_dict)

            else:
                # Create a dictionary containing the application name, version, and
                # associated serial number.
                apps_dict = {
                    "serial_number": device["serial_number"].upper(),
                    "device_name": device["device_name"],
                    "os_version": device["os_version"],
                    "user": device["user"],
                    "platform": device["platform"],
                    "app_name": app["app_name"],
                    "version": app["version"],
                }

                data.append(apps_dict)

    return data


def write_report(report_payload, report_name):
    """Write app report."""
    # write report to csv file
    with open(report_name, mode="w", encoding="utf-8") as report:

        out_fields = []

        # automatically loop over keys in the payload to pullout header fields
        for item in report_payload:
            for key in item.keys():
                if key not in out_fields:
                    out_fields.append(key)

        writer = csv.DictWriter(report, fieldnames=out_fields)

        # Write headers to CSV
        writer.writeheader()

        # Loop over the app list sorted by app_name
        for app in sorted(report_payload, key=lambda k: k["app_name"]):
            # if a user is assinged
            if app["user"]:
                # update user
                app["user"] = app["user"]["name"]
                # Write row to csv file
                writer.writerow(app)

            else:
                writer.writerow(app)


def main():
    """Run main logic."""
    # Return the arguments
    arguments = program_arguments()

    print(f"Version: {__version__}\n")
    print(f"Base URL: {BASE_URL}\n")

    if "example" in BASE_URL:
        print(f"\tThe subdomain in {BASE_URL} needs to be updated...\n")
        sys.exit()

    if "your_api_key_here" in TOKEN:
        print(f'\tThe TOKEN should not be "{TOKEN}"...\n')
        sys.exit()

    # Get all device inventory records
    print("Getting all device records from Kandji ...")

    # Get all device inventory records
    device_inventory = kandji_api(method="GET", endpoint="devices", params={"limit": "100000"})

    print(f"Total device records: {len(device_inventory)}")

    # Report name
    if arguments.name:
        report_name = f'{arguments.name.lower().replace(" ", "_")}_app_install_report_{TODAY}.csv'
        print(f"Looking for devices with {arguments.name} installed...")
    else:
        report_name = f"apps_install_report_{TODAY}.csv"

    # create the report payload
    report_payload = generate_report_payload(device_inventory, arguments)

    if len(report_payload) < 1:
        print(f"No devices found with {arguments.name} installed...")

    if arguments.name:
        print(f"Found {len(report_payload)} devices with {arguments.name} installed...")

    print("Generating Kandji app install report ...")
    write_report(report_payload, report_name)

    print("Kandji app report complete ...")
    print(f"Kandji app report at: {HERE.resolve()}/{report_name} ")


if __name__ == "__main__":
    main()
