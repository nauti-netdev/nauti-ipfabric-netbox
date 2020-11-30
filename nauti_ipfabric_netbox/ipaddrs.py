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


@Reconciler.register(origin="ipfabric", target="netbox", collection="ipaddrs")
class ReconcileIPFabricNetboxIPaddrs(Reconciler):
    async def add_items(self):
        nb_col = self.target
        log = get_logger()

        def _done(_item, _res: Response):
            _key, _fields = _item
            _res.raise_for_status()
            ident = f"ipaddr {_fields['hostname']}, {_fields['interface']}, {_fields['ipaddr']}"
            log.info(f"CREATE:OK: {ident}")

        await nb_col.add_items(self.diff_res.missing, callback=_done)

    async def update_items(self):
        nb_col = self.target
        changes = self.diff_res.changes

        def _done(_item, res: Response):
            _key, _changes = _item
            _hostname, _ifname = _key
            res.raise_for_status()
            print(f"UPDATE:OK: ipaddr {_hostname}, {_ifname}", flush=True)

        await nb_col.update_items(changes, callback=_done)

    async def delete_items(self):
        raise NotImplementedError()
