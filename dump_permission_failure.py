"""
Capture and log flows for vSphere permission failures.

Options (see how to use them below) will allow saving an MITMProxy dump format
file, a human readable flat file (structure defined below), and an option to
show duplicate types of failures per user.

Flat file structure:

  TODO

Run with:
  $ mitmproxy -s ./dump_permission_failure.py <dump-file>
       [--set vs_dump_flows=FILE]
       [--set vs_dump_csv=FILE]
       [--set vs_duplicates=true|false]


Testing?
 - Read flows from file: --rfile/-r <file>
 - Probably use: --no-server
 - Increase event log verbosity using: --set console_eventlog_verbosity=debug
 - See mitmproxy's event log using: Shift+E
"""
import csv

from mitmproxy import ctx, io, http, addonmanager
import typing  # noqa

from xml.etree import ElementTree


# Script options
VS_DUMP_FLOWS_OPT = 'vs_dump_flows'
VS_DUMP_CSV_OPT = 'vs_dump_csv'
VS_DUP_OPT = 'vs_duplicates'

# XML
namespaces = {
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'vim25': 'urn:vim25',
}


def check_soap_permission_fault(response: typing.Optional[http.Response]) -> bool:
    """
    Checks if the given HTTP Response is for a vSphere NoPermissionFault (SOAP) response.
    :param response: An MITMProxy Response to check
    :return: True if the given response object contains NoPermissionFault or False otherwise.
    """
    if response.status_code != 200:
        return _check_soap_permission_fault_body(response.data.content)
    else:
        return False


# Added for unit tests. See check_soap_permission_fault for doc.
def _check_soap_permission_fault_body(response_body: str) -> bool:
    try:
        dom = ElementTree.fromstring(response_body)
        found = dom.find('./soapenv:Body/soapenv:Fault/detail/vim25:NoPermissionFault', namespaces=namespaces)
        if found is None:
            return False
        else:
            return True
    except ElementTree.ParseError:
        return False


def get_csv_fields_from_response(response_body: str) -> dict:
    """
    Assumes a privilege failure response is given as parameter. Extracts the fields from
    a response required for the CSV writer.
    :param response_body: Must be an HTTP response body containing a vSphere privilege failure.
    :return: A dictionary of CSV field names to values or None upon error.
    """
    try:
        dom = ElementTree.fromstring(response_body)
        fault_object = dom.find('./soapenv:Body/soapenv:Fault/detail/vim25:NoPermissionFault/vim25:object', namespaces=namespaces)
        privilege_missing = dom.find('./soapenv:Body/soapenv:Fault/detail/vim25:NoPermissionFault/vim25:privilegeId', namespaces=namespaces)
        if fault_object is None or privilege_missing is None:
            return None

        result = dict()
        result["ObjectType"] = fault_object.get("type")
        result["ObjectName"] = fault_object.text
        result["PrivilegeMissing"] = privilege_missing.text
        return result
    except ElementTree.ParseError:
        return None


class Writer:
    dump_file: typing.IO[bytes] = None
    flow_writer: io.FlowWriter = None
    csv_file: typing.IO[bytes] = None
    csv_writer: csv.DictWriter = None
    show_dup: bool = False
    seen_cache: set = set()

    # https://docs.mitmproxy.org/stable/api/events.html#LifecycleEvents.running
    def running(self) -> None:
        try:
            if ctx.options.vs_dump_flows != "":
                self.dump_file = open(ctx.options.vs_dump_flows, "wb")
                self.flow_writer = io.FlowWriter(self.dump_file)
            if ctx.options.vs_dump_csv != "":
                self.csv_file = open(ctx.options.vs_dump_csv, "w")
                field_names = ["UserAgent", "ObjectType", "ObjectName", "PrivilegeMissing"]
                self.csv_writer = csv.DictWriter(self.csv_file, field_names)
            self.show_dup = ctx.options.vs_duplicates

            ctx.log.debug("dump_permission_failure.py running")
        except:  # noqa
            # TODO Log exception?
            ctx.master.shutdown()

    # https://docs.mitmproxy.org/stable/api/events.html#LifecycleEvents.load
    @staticmethod
    def load(loader: addonmanager.Loader) -> None:
        loader.add_option(
            name=VS_DUMP_FLOWS_OPT,
            typespec=str,
            help="Set the MITMProxy dump output file",
            default="",
        )

        loader.add_option(
            name=VS_DUMP_CSV_OPT,
            typespec=str,
            help="Set the CSV output file",
            default="",
        )

        loader.add_option(
            name=VS_DUP_OPT,
            typespec=bool,
            help="Show duplicate failures based on User Agent and permission name",
            default=False,
        )

        ctx.log.debug("dump_permission_failure.py loaded")

    # https://docs.mitmproxy.org/stable/api/events.html#HTTPEvents.response
    def response(self, flow: http.HTTPFlow) -> None:
        is_fault = check_soap_permission_fault(flow.response)
        if is_fault:
            # Only logging permission faults
            self._log_flow(flow)

    def _log_flow(self, flow: http.HTTPFlow) -> None:
        fields = get_csv_fields_from_response(flow.response.data.content)
        if fields is None:
            return

        user_agent = flow.request.headers['user-agent']
        fields["UserAgent"] = user_agent

        if not self.show_dup:
            # Don't show duplicates
            if self._cache_check(fields):
                return

        # Write flow to output file[s] and flush
        if self.flow_writer is not None:
            self.flow_writer.add(flow)
            self.dump_file.flush()
        if self.csv_writer is not None:
            self.csv_writer.writerow(fields)
            self.csv_file.flush()

        # Add to cache
        self._cache_save(fields)

    def _cache_save(self, hashed: dict):
        # Save the hash to cache
        entry = str(hashed)
        self.seen_cache.add(entry)

    def _cache_check(self, hashed: dict) -> bool:
        # Does hash existing in the cache already
        entry = str(hashed)
        return entry in self.seen_cache

    # https://docs.mitmproxy.org/stable/api/events.html#LifecycleEvents.done
    def done(self):
        # Add-on cleanup
        self.dump_file.close()
        self.csv_file.close()


# Configure Writer in addons for mitmproxy to import
addons = [
    Writer()
]
