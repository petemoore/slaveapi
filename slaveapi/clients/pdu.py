from subprocess import check_output, STDOUT
import time

import logging
log = logging.getLogger(__name__)

class PDU(object):
    # These are just magic numbers/words that are factored out to here.
    snmp_protocol_version = "1"
    snmp_community = "private"
    on_cmd = ["i", "1"]
    off_cmd = ["i", "2"]
    reboot_cmd = ["i", "3"]
    port_mappings = {"A": "1", "B": "2", "C": "3"}
    # I don't fully understand OID, this was cribbed from sut-lib code.
    # http://oid-info.com/get/1.3.6.1.4.1.1718.3.2.3.1.11 describes what
    # this means in a bit more detail. In any case, this is the base OID
    # for doing any reboots via our PDUs - at least until we buy
    # PDUs that are different.
    # The full OID has the tower, infeed, and outlet appended to it later.
    base_oid = "1.3.6.1.4.1.1718.3.2.3.1.11"
    def __init__(self, fqdn, port):
        self.fqdn = fqdn
        self.port = port
        self.tower, self.infeed, self.outlet = self._parse_port(port)

    def poweroff(self):
        self._run_cmd(self.off_cmd)

    def poweron(self):
        self._run_cmd(self.on_cmd)

    def powercycle(self, delay=5):
        log.info("Powercycling via PDU.")
        self.poweroff()
        log.debug("Power is off, waiting %d seconds before turning it back on.", delay)
        time.sleep(delay)
        self.poweron()
        log.info("Powercycle completed.")

    def _run_cmd(self, cmd):
        oid = "%s.%s.%s.%s" % (self.base_oid, self.tower, self.infeed, self.outlet)
        full_cmd = ["snmpset", "-v", self.snmp_protocol_version,
                    "-c", self.snmp_community, self.fqdn, oid]
        full_cmd += cmd
        return check_output(full_cmd, stderr=STDOUT)

    def _parse_port(self, port):
        try:
            tower, infeed, outlet = port[0], port[1], port[2:]
            for before, after in self.port_mappings.iteritems():
                tower = tower.replace(before, after)
                infeed = infeed.replace(before, after)
            return tower, infeed, outlet
        except IndexError:
            log.error("Couldn't parse port %s", port)
            raise
