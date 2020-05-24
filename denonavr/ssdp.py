#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
import socket
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests
import ifaddr

_LOGGER = logging.getLogger('DenonSSDP')

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 2
SSDP_TARGET = (SSDP_ADDR, SSDP_PORT)
SSDP_ST_1 = "ssdp:all"
SSDP_ST_2 = "upnp:rootdevice"
SSDP_ST_3 = "urn:schemas-upnp-org:device:MediaRenderer:1"

SSDP_ST_LIST = (SSDP_ST_1, SSDP_ST_2, SSDP_ST_3)

SCPD_XMLNS = "{urn:schemas-upnp-org:device-1-0}"
SCPD_DEVICE = "{xmlns}device".format(xmlns=SCPD_XMLNS)
SCPD_DEVICETYPE = "{xmlns}deviceType".format(xmlns=SCPD_XMLNS)
SCPD_MANUFACTURER = "{xmlns}manufacturer".format(xmlns=SCPD_XMLNS)
SCPD_MODELNAME = "{xmlns}modelName".format(xmlns=SCPD_XMLNS)
SCPD_SERIALNUMBER = "{xmlns}serialNumber".format(xmlns=SCPD_XMLNS)
SCPD_FRIENDLYNAME = "{xmlns}friendlyName".format(xmlns=SCPD_XMLNS)
SCPD_PRESENTATIONURL = "{xmlns}presentationURL".format(xmlns=SCPD_XMLNS)

DEVICETYPE_DENON = "urn:schemas-upnp-org:device:MediaRenderer:1"

SUPPORTED_MANUFACTURERS = ["Denon", "DENON", "Marantz"]


def ssdp_request(ssdp_st, ssdp_mx=SSDP_MX):
    """Return request bytes for given st and mx."""
    return "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'ST: {}'.format(ssdp_st),
        'MX: {:d}'.format(ssdp_mx),
        'MAN: "ssdp:discover"',
        'HOST: {}:{}'.format(*SSDP_TARGET),
        '', '']).encode('utf-8')


def get_local_ips():
    """Get IPs of local network adapters."""
    adapters = ifaddr.get_adapters()
    ips = []
    for adapter in adapters:
        # pylint: disable=invalid-name
        for ip in adapter.ips:
            if isinstance(ip.ip, str):
                ips.append(ip.ip)
    return ips


def identify_denonavr_receivers():
    """
    Identify DenonAVR using SSDP and SCPD queries.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    """
    # Sending SSDP broadcast message to get resource urls from devices
    urls = send_ssdp_broadcast()

    # Check which responding device is a DenonAVR device and prepare output
    receivers = []
    for url in urls:
        try:
            receiver = evaluate_scpd_xml(url)
        except requests.exceptions.RequestException:
            continue
        if receiver:
            receivers.append(receiver)

    return receivers


def send_ssdp_broadcast():
    """
    Send SSDP broadcast message to discover UPnP devices.

    Returns a set of SCPD XML resource urls for all discovered devices.
    """
    # Send up to three different broadcast messages
    ips = get_local_ips()
    res = []
    # pylint: disable=invalid-name
    for ip in ips:
        # Ignore 169.254.0.0/16 adresses
        if re.search("169.254.*.*", ip):
            continue
        for i, ssdp_st in enumerate(SSDP_ST_LIST):
            # Prepare SSDP broadcast message
            sock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(SSDP_MX)
            sock.bind((ip, 0))
            sock.sendto(ssdp_request(ssdp_st), (SSDP_ADDR, SSDP_PORT))

            # Collect all responses within the timeout period
            try:
                while True:
                    res.append(sock.recvfrom(10240))
            except socket.timeout:
                sock.close()

            if res:
                _LOGGER.debug(
                    "Got results after %s SSDP queries using ip %s", i + 1, ip)
                sock.close()
                break
        if res:
            break

    # Prepare output of responding devices
    urls = set()

    for entry in res:
        # Some string operations to get the receivers URL
        # which could be found between LOCATION and end of line of the response
        entry_text = entry[0].decode("utf-8")
        match = re.search('(?<=LOCATION:\s).+?(?=\\r)', entry_text)
        if match:
            urls.add(match.group(0))

    _LOGGER.debug("Following devices found: %s", urls)
    return urls


def evaluate_scpd_xml(url):
    """
    Get and evaluate SCPD XML to identified URLs.

    Returns dictionary with keys "host", "modelName", "friendlyName" and
    "presentationURL" if a Denon AVR device was found and "False" if not.
    """
    # Get SCPD XML via HTTP GET
    try:
        res = requests.get(url, timeout=2)
    except requests.exceptions.ConnectTimeout:
        raise
    except requests.exceptions.RequestException as err:
        _LOGGER.error(
            "During DenonAVR device identification, when trying to request %s "
            "the following error occurred: %s", url, err)
        raise

    if res.status_code == 200:
        try:
            root = ET.fromstring(res.text)
            # Look for manufacturer "Denon" in response.
            # Using "try" in case tags are not available in XML
            device = {}
            device["manufacturer"] = (
                root.find(SCPD_DEVICE).find(SCPD_MANUFACTURER).text)

            _LOGGER.debug("Device %s has manufacturer %s", url,
                          device["manufacturer"])
            if (device["manufacturer"] in SUPPORTED_MANUFACTURERS and
                    root.find(SCPD_DEVICE).find(
                        SCPD_DEVICETYPE).text == DEVICETYPE_DENON):
                device["host"] = urlparse(
                    root.find(SCPD_DEVICE).find(
                        SCPD_PRESENTATIONURL).text).hostname
                device["presentationURL"] = (
                    root.find(SCPD_DEVICE).find(SCPD_PRESENTATIONURL).text)
                device["modelName"] = (
                    root.find(SCPD_DEVICE).find(SCPD_MODELNAME).text)
                device["serialNumber"] = (
                    root.find(SCPD_DEVICE).find(SCPD_SERIALNUMBER).text)
                device["friendlyName"] = (
                    root.find(SCPD_DEVICE).find(SCPD_FRIENDLYNAME).text)
                return device
            else:
                return False
        except (AttributeError, ValueError, ET.ParseError) as err:
            _LOGGER.error(
                "Error occurred during evaluation of SCPD XML: %s", err)
            return False
    else:
        _LOGGER.debug("Host returned HTTP status %s when connecting to %s",
                      res.status_code, url)
        return False
