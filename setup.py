#  Copyright (C) 2020  Jeremy Schulman
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from setuptools import setup, find_packages

package_name = "nauti-ipfabric-netbox"
package_version = open("VERSION").read().strip()


def requirements(filename="requirements.txt"):
    return open(filename.strip()).readlines()


with open("README.md", "r") as fh:
    long_description = fh.read()


# -----------------------------------------------------------------------------
#
#                                 Main Setup
#
# -----------------------------------------------------------------------------

setup(
    name=package_name,
    version=package_version,
    description="Nauti integration IP Fabric <-> Netbox",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jeremy Schulman",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements(),
    entry_points={
        "nauti.plugins": [
            "devices = nauti_ipfabric_netbox.devices",
            "sites = nauti_ipfabric_netbox.sites",
            "interfaces = nauti_ipfabric_netbox.interfaces",
            "ipaddrs = nauti_ipfabric_netbox.ipaddrs",
            "portchans = nauti_ipfabric_netbox.portchans",
            "auditors = nauti_ipfabric_netbox.auditors",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
    ],
)
