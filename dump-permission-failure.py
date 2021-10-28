#!/usr/bin/env python3
"""
Capture and log flows for vSphere permission failures.

Options (see how to use them below) will allow saving an MITMProxy dump format
file, a human readable flat file (structure defined below), option to only
save unique permission failures per User Agent, and finally an option to
include a periodic summary.

Flat file structure:

  TODO

Run with:
  $ mitmproxy -s ./dump-permission-failure.py <dump-file>
       [--set vs_dump_flows=FILE]
       [--set vs_dump_flat=FILE]
       [--set vs_unique=true|false]
"""
import csv

from mitmproxy import ctx, io, http, addonmanager
import typing  # noqa

from xml.etree import ElementTree


# Script options
VS_DUMP_FLOWS_OPT = 'vs_dump_flows'
VS_DUMP_CSV_OPT = 'vs_dump_csv'
VS_UNIQUE_OPT = 'vs_unique'

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
        try:
            dom = ElementTree.fromstring(response.data.content)
            found = dom.find('./soapenv:Body/soapenv:Fault/detail/vim25:NoPermissionFault', namespaces=namespaces)
            if found is None:
                return False
            else:
                return True
        except ElementTree.ParseError:
            return False


class Writer:
    dump_file: typing.IO[bytes]
    flow_writer: io.FlowWriter
    csv_file: typing.IO[bytes]
    csv_writer: csv.DictWriter
    only_unique: bool

    def running(self) -> None:
        try:
            if ctx.options.vs_dump_flows != "":
                self.dump_file = open(ctx.options.vs_dump_flows, "wb")
                self.flow_writer = io.FlowWriter(self.dump_file)
            if ctx.options.vs_dump_csv != "":
                self.csv_file = open(ctx.options.vs_dump_csv, "wb")
                field_names = ["UserAgent", "ObjectType", "ObjectName", "PrivilegeMissing"]
                self.csv_writer = csv.DictWriter(self.csv_file, field_names)
            ctx.log.debug("dump-permission-failure.py running")
        except:  # noqa
            # TODO Log exception!
            ctx.master.shutdown()

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
            name=VS_UNIQUE_OPT,
            typespec=bool,
            help="Only keep unique responses based on User Agent and permission name",
            default=False,
        )

        ctx.log.debug("dump-permission-failure.py loaded")

    def response(self, flow: http.HTTPFlow) -> None:
        is_fault = check_soap_permission_fault(flow.response)
        if is_fault:
            self.flow_writer.add(flow)

    def _log_flow(self, flow: http.HTTPFlow) -> None:
        if self.only_unique:
            if not self._check_unique(flow):
                return
        if self.flow_writer is not None:
            self._write_flow(flow)
        if self.csv_writer is not None:
            self._write_csv(flow)

    def _check_unique(self, flow: http.HTTPFlow) -> bool:
        return True

    def _write_flow(self, flow: http.HTTPFlow) -> None:
        pass

    def _write_csv(self, flow: http.HTTPFlow) -> None:
        pass

    def done(self):
        self.dump_file.close()


addons = [
    Writer()
]
