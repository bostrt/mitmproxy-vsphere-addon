import unittest

import dump_permission_failure

NOT_XML = "lol"

OTHER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>ServerFaultCode</faultcode>
      <faultstring>The object &apos;vim.Task:task-190543&apos; has already been deleted or has not been completely created</faultstring>
      <detail>
        <ManagedObjectNotFoundFault xmlns="urn:vim25" xsi:type="ManagedObjectNotFound">
          <obj type="Task">task-190543</obj>
        </ManagedObjectNotFoundFault>
      </detail>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>"""

LEGIT_FAULT = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>ServerFaultCode</faultcode>
      <faultstring>Permission to perform this operation was denied.</faultstring>
      <detail>
        <NoPermissionFault xmlns="urn:vim25" xsi:type="NoPermission">
          <object type="Folder">group-v23485</object>
          <privilegeId>VirtualMachine.Interact.PowerOn</privilegeId>
        </NoPermissionFault>
      </detail>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>"""


class TestCases(unittest.TestCase):
    def test__check_fault__not_a_fault(self):
        self.assertFalse(dump_permission_failure._check_soap_permission_fault_body(OTHER_XML))

    def test__check_fault__legit_fault(self):
        self.assertTrue(dump_permission_failure._check_soap_permission_fault_body(LEGIT_FAULT))

    def test__check_fault__not_xml(self):
        self.assertFalse(dump_permission_failure._check_soap_permission_fault_body(NOT_XML))

    def test__get_fields__not_a_fault(self):
        self.assertIsNone(dump_permission_failure.get_csv_fields_from_response(OTHER_XML))

    def test__get_fields__legit_fault(self):
        fields = dump_permission_failure.get_csv_fields_from_response(LEGIT_FAULT)
        self.assertIsNotNone(fields)
        self.assertEqual("Folder", fields["ObjectType"])
        self.assertEqual("group-v23485", fields["ObjectName"])
        self.assertEqual("VirtualMachine.Interact.PowerOn", fields["PrivilegeMissing"])

    def test__get_fields__not_xml(self):
        self.assertIsNone(dump_permission_failure.get_csv_fields_from_response(NOT_XML))


if __name__ == '__main__':
    unittest.main()
