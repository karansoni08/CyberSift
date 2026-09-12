"""extractors.network_extractor
Network and infrastructure artifacts describing an environment.
"""

from app.extractors.base import BaseExtractor


class NetworkExtractor(BaseExtractor):
    category_id = "network"
    label = "Network"
    subtypes = (
        "internal_ip",
        "public_ip",
        "cidr_range",
        "hostname",
        "port_service",
        "protocol",
        "mac_address",
        "asn",
        "dns_record",
        "vpn_endpoint",
    )
    guidance = """
Extract network and infrastructure artifacts that describe an environment's
layout: internal/RFC1918 addresses (internal_ip) vs routable addresses
(public_ip), CIDR ranges, hostnames and FQDNs of infrastructure (servers,
workstations, firewalls — as opposed to attacker domains, which belong to the
IOC category), open ports with their service (value like "3389/rdp" when the
document pairs them, else just the port), protocols in use, MAC addresses,
autonomous system numbers, DNS records described in the document, and VPN
endpoints. When the same address could be an IOC and a network artifact,
extract it here only if the document treats it as part of the environment
being described rather than as a hostile indicator.
"""
