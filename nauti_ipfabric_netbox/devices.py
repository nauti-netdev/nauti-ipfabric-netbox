"""
This file contains the Reconciler code for IP Fabric Device collection -> Netbox
Device collection.
"""
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


from httpx import Response

from nauti.tasks.reconile import Reconciler
from nauti.log import get_logger
from nauti.collection import get_collection
from nauti.diff import diff
from nauti.igather import iawait


@Reconciler.register(origin="ipfabric", target="netbox", collection="devices")
class IPFabricNetboxDeviceCollectionReconciler(Reconciler):
    """
    This class defines the reconcile methods to sync the differences between the
    IP Fabric and the Netbox systems for the "devices" collection.
    """

    # -------------------------------------------------------------------------
    #
    #                           Add New Items
    #
    # -------------------------------------------------------------------------

    async def add_items(self):

        # -------------------------------------------------------------------------
        # Now create each of the device records.  Once the device records are
        # created, then go back and add the primary interface and ipaddress values
        # using the other collections.
        # -------------------------------------------------------------------------

        ipf_col = self.origin
        nb_col = self.target
        missing = self.diff_res.missing

        log = get_logger()

        def _report_device(update, _res: Response):
            key, item = update
            if _res.is_error:
                log.error(f"FAIL: create device {item['hostname']}: {_res.text}")
                return

            log.info(
                f"CREATE:OK: device {item['hostname']} ... creating primary IP ... "
            )
            nb_col.source_records.append(_res.json())

        await nb_col.add_items(items=missing, callback=_report_device)
        await self._ensure_primary_ipaddrs(missing=missing)

        # -------------------------------------------------------------------------
        # for each of the missing device records perform a "change request" on the
        # 'ipaddr' field. so that the primary IP will be assigned.
        # -------------------------------------------------------------------------

        ipaddr_changes = {
            key: {"ipaddr": ipf_col.items[key]["ipaddr"]} for key in missing.keys()
        }

        def _report_primary(item, _res):  # noqa
            key, fields = item
            rec = nb_col.items[key]
            ident = f"device {rec['hostname']} assigned primary-ip4"
            if _res.is_error:
                log.error(f"CREATE:FAIL: {ident}: {_res.text}")
                return

            log.info(f"CREATE:OK: {ident}.")

        await nb_col.update_items(items=ipaddr_changes, callback=_report_primary)

    # -------------------------------------------------------------------------
    #
    #                           Update Existing Items
    #
    # -------------------------------------------------------------------------

    async def update_items(self):

        # TODO: need to test out update to device items
        # ipf_col = self.origin

        nb_col = self.target
        changes = self.diff_res.changes
        log = get_logger()

        def _report(change, res: Response):
            ch_key, ch_fields = change
            ch_rec = nb_col.items[ch_key]
            ident = f"device {ch_rec['hostname']}"
            if res.is_error:
                log.error(f"CHANGE:FAIL: {ident}, {res.text}")
                return

            log.info(f"CHANGE:OK: {ident}")

        actual_changes = dict()
        missing_pri_ip = dict()

        update_primary_ip = nb_col.config.options.get("update_primary_ip", False)

        for key, key_change in changes.items():
            rec = nb_col.items[key]
            if (ipaddr := key_change.pop("ipaddr", None)) is not None:
                if any(
                    (rec["ipaddr"] == "", (ipaddr and (update_primary_ip is True)),)
                ):
                    key_change["ipaddr"] = ipaddr
                    missing_pri_ip[key] = key_change

            if len(key_change):
                actual_changes[key] = key_change

        if missing_pri_ip:
            await self._ensure_primary_ipaddrs(missing=missing_pri_ip)

        if not actual_changes:
            log.info("No required changes.")
            return

        log.info("Processing changes ... ")
        await nb_col.update_items(changes, callback=_report)
        log.info("Done.")

    # -------------------------------------------------------------------------
    #
    #                           Private Methods
    #
    # -------------------------------------------------------------------------

    async def _ensure_primary_ipaddrs(self, missing: dict):
        log = get_logger()

        ipf_col = self.origin

        ipf_col_ipaddrs = get_collection(source=ipf_col.source, name="ipaddrs")
        ipf_col_ifaces = get_collection(source=ipf_col.source, name="interfaces")

        # -------------------------------------------------------------------------
        # we need to fetch all of the IPF ipaddr records so that we can bind the
        # management IP address to the Netbox device record.  We use the **IPF**
        # collection as the basis for the missing records so that the filter values
        # match.  This is done to avoid any mapping changes that happended via the
        # collection intake process.  This code is a bit of 'leaky-abstration',
        # so TODO: cleanup.
        # -------------------------------------------------------------------------

        log.info("Fetching IP Fabric IP records ...")
        tasks = [
            ipf_col_ipaddrs.fetch(
                filters=f"and(hostname = {_item['hostname']}, ip = '{_item['loginIp']}')"
            )
            for _item in [ipf_col.source_record_keys[key] for key in missing.keys()]
        ]

        await iawait(tasks, limit=50)
        ipf_col_ipaddrs.make_keys()

        # -------------------------------------------------------------------------
        # now we need to gather the IPF interface records so we have any _fields that
        # need to be stored into Netbox (e.g. description)
        # -------------------------------------------------------------------------

        log.info("Fetching IP Fabric interface records ...")

        tasks = [
            ipf_col_ifaces.fetch(
                filters=f"and(hostname = {_item['hostname']}, intName = {_item['intName']})"
            )
            for _item in ipf_col_ipaddrs.source_record_keys.values()
        ]

        await iawait(tasks, limit=50)
        ipf_col_ifaces.make_keys()

        # -------------------------------------------------------------------------
        # At this point we have the IPF collections for the needed 'interfaces' and
        # 'ipaddrs'.  We need to ensure these same entities exist in the Netbox
        # collections.  We will first attempt to find all the existing records in
        # Netbox using the `fetch_keys` method.
        # -------------------------------------------------------------------------

        nb_col = self.target

        nb_col_ifaces = get_collection(source=nb_col.source, name="interfaces")
        nb_col_ipaddrs = get_collection(source=nb_col.source, name="ipaddrs")

        await nb_col_ifaces.fetch_items(items=ipf_col_ifaces.items)
        await nb_col_ipaddrs.fetch_items(items=ipf_col_ipaddrs.items)

        nb_col_ipaddrs.make_keys()
        nb_col_ifaces.make_keys()

        diff_ifaces = diff(origin=ipf_col_ifaces, target=nb_col_ifaces)
        diff_ipaddrs = diff(origin=ipf_col_ipaddrs, target=nb_col_ipaddrs)

        def _report_iface(item, _res: Response):
            _key, _fields = item
            hname, iname = _fields["hostname"], _fields["interface"]
            if _res.is_error:
                log.error(f"CREATE:FAIL: interface {hname}, {iname}: {_res.text}")
                return

            print(f"CREATE:OK: interface {hname}, {iname}.")
            nb_col_ifaces.source_records.append(_res.json())

        if diff_ifaces.missing:
            await nb_col_ifaces.add_items(
                items=diff_ifaces.missing, callback=_report_iface
            )

        def _report_ipaddr(item, _res: Response):
            _key, _fields = item
            hname, iname, ipaddr = (
                _fields["hostname"],
                _fields["interface"],
                _fields["ipaddr"],
            )
            ident = f"ipaddr {hname}, {iname}, {ipaddr}"

            if _res.is_error:
                log.error(f"CREATE:FAIL: {ident}: {_res.text}")
                return

            nb_col_ipaddrs.source_records.append(_res.json())
            log.info(f"CREATE:OK: {ident}.")

        if diff_ipaddrs.missing:
            await nb_col_ipaddrs.add_items(
                items=diff_ipaddrs.missing, callback=_report_ipaddr
            )

        nb_col.make_keys()
        nb_col_ifaces.make_keys()
        nb_col_ipaddrs.make_keys()

        # TODO: Note that I am passing the cached collections of interfaces and ipaddress
        #       To the device collection to avoid duplicate lookups for record
        #       indexes. Will give this approach some more thought.

        nb_col.cache["interfaces"] = nb_col_ifaces
        nb_col.cache["ipaddrs"] = nb_col_ipaddrs
