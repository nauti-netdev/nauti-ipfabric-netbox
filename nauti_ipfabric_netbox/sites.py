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

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response
from nauti.tasks.reconile import Reconciler
from nauti.log import get_logger


@Reconciler.register(origin="ipfabric", target="netbox", collection="sites")
class IPFabricNetboxSitesReconciler(Reconciler):

    # -------------------------------------------------------------------------
    #
    #                       Add New Items to Netbox
    #
    # -------------------------------------------------------------------------

    async def add_items(self):
        log = get_logger()
        nb_col = self.target
        missing = self.diff_res.missing

        def _report(item, res: Response):
            _key, _fields = item
            ident = f"site {_fields['name']}"
            if res.is_error:
                log.error(f"CREATE {ident}: FAIL: {res.text}")
                return
            log.info(f"CREATE {ident}: OK")

        log.info("CREATE:BEGIN: Netbox sites ...")
        await nb_col.add_items(missing, callback=_report)
        log.info("CREATE:DONE: Netbox sites ...")

    # -------------------------------------------------------------------------
    #
    #                        Update Existing Items in Netbox
    #
    # -------------------------------------------------------------------------

    async def update_items(self):
        get_logger().warning("Site changes not supported at this time.")

    # -------------------------------------------------------------------------
    #
    #                       Delete Existing Items from Netbox
    #
    # -------------------------------------------------------------------------

    async def delete_items(self):
        get_logger().warning("Site removal not supported at this time.")
