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
# System Imports
# -----------------------------------------------------------------------------

from operator import itemgetter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response
from nauti.tasks.reconile import Reconciler
from nauti.log import get_logger


@Reconciler.register(origin="ipfabric", target="netbox", collection="interfaces")
class IPFabricNetboxInterfaceReconciler(Reconciler):

    # -------------------------------------------------------------------------
    #
    #                       Add New Items to Netbox
    #
    # -------------------------------------------------------------------------

    async def add_items(self):
        nb_col = self.diff_res.target
        missing = self.diff_res.missing
        log = get_logger()
        fields_fn = itemgetter("hostname", "interface")

        def _done(_item, _res: Response):
            _key, _fields = _item
            _res.raise_for_status()
            _hostname, _if_name = fields_fn(_fields)
            log.info(f"CREATE:OK: interface {_hostname}, {_if_name}")

        log.info("CREATE:BEGIN: Netbox interfaces ...")
        await nb_col.add_items(items=missing, callback=_done)
        log.info("CREATE:DONE: Netbox interfaces.")

    async def update_items(self):
        nb_col = self.diff_res.target
        changes = self.diff_res.changes
        fields_fn = itemgetter("hostname", "interface")

        log = get_logger()

        def _done(_item, _res: Response):
            _key, _ch_fields = _item
            _fields = nb_col.items[_key]
            _hostname, _ifname = fields_fn(_fields)
            _res.raise_for_status()
            log.info(f"CHANGE:OK: interface {_hostname}, {_ifname}")

        log.info("CHANGE:BEGIN: Netbox interfaces ...")
        await nb_col.update_items(items=changes, callback=_done)
        log.info("CHANGE:DONE: Netbox interfaces.")
