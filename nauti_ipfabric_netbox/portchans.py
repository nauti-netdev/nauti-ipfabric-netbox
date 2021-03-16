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


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@Reconciler.register(origin="ipfabric", target="netbox", collection="portchans")
class ReconcileIPFabricNetboxPortChans(Reconciler):
    async def add_items(self):
        log = get_logger()

        def _report(item, res: Response):
            _key, _fields = item
            ident = f"{_fields['hostname']}, {_fields['interface']} -> {_fields['portchan']}"
            if res.is_error:
                log.error(f"CREATE:FAIL: {ident}, {res.text}.")
                return

            log.info(f"CREATE:OK: {ident}.")

        await self.target.add_items(self.diff_res.missing, callback=_report)

    async def update_items(self):
        nb_col = self.target
        log = get_logger()

        def _report(_item, res: Response):
            _key, _ch_fields = _item
            _fields = nb_col.items[_key]
            ident = f"{_fields['hostname']}, {_fields['interface']} -> {_ch_fields['portchan']}"
            if res.is_error:
                log.error(f"CHANGE:FAIL: {ident}, {res.text}")
                return

            log.info(f"CHANGE:OK: {ident}")

        await nb_col.update_items(self.diff_res.changes, callback=_report)

    async def delete_items(self):

        """
        Extras exist when an interface in Netbox is associated to a LAG, but that
        interface is not associated to the LAG in IPF.  In these cases we need
        to remove the relationship between the NB interface->LAG.
        """
        nb_col = self.target
        log = get_logger()

        def _report(_item, res: Response):
            _key, _ch_fields = _item
            _fields = nb_col.items[_key]
            ident = f"{_fields['hostname']}, {_fields['interface']} -x {_fields['portchan']}"
            if res.is_error:
                log.error(f"REMOVE:FAIL: {ident}, {res.text}.")
                return

            log.info(f"REMOVE:OK: {ident}.")

        await nb_col.delete_items(self.diff_res.extras, callback=_report)
