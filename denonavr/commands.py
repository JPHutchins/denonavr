#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains instances of the XmlCommand class that are representations
of the Denon AVR 2016 XML command structure.  Refer to ./XML_data_dump.txt for
more information or to find out how to sniff commands on your own AVR.
"""
from .helpers import XmlCommand1, XmlCommand3

SET_DYNAMIC_VOL = XmlCommand3(
    "Dynamic Volume", "SetAudyssey",
    (0, 3), param="dynamicvol",
    values=[
        "Off",
        "Light",
        "Medium",
        "Heavy"
    ]
)

SET_LOUDNESS_MANAGEMENT = XmlCommand3(
    "Loudness Management", "SetSurroundParameter",
    (0, 1), param="loudness"
)

SET_DYNAMIC_COMP = XmlCommand3(
    "Dynamic Compression", "SetSurroundParameter",
    (0, 3), param="dyncomp",
    values=[
        "Off",
        "Low"
        "Mid"
        "High"
    ]
)

SET_LFE = XmlCommand3(
    "LFE Level", "SetSurroundParameter",
    (0, -10), param="lfe"
)

SET_CENTER_SPREAD = XmlCommand3(
    "Center Spread", "SetSurroundParameter",
    (0, 1), param="cspread"
)

SET_DYNAMIC_EQ = XmlCommand3(
    "Dynamic EQ", "SetAudyssey",
    (0, 1), param="dynamiceq"
)

SET_REF_LEVEL_OFFSET = XmlCommand3(
    "Reference Level Offset", "SetAudyssey",
    (0, 3), param="reflevoffset",
    values=[
        "0dB",
        "5dB",
        "10dB",
        "15dB"
    ]
)

SET_MULTEQ = XmlCommand3(
    "MultEQ", "SetAudyssey",
    (0, 3), param="multeq",
    values=[
        "Audyssey",
        "Audyssey Flat",
        "Audyssey Bypass L/R",
        "Manual"
    ]
)

SET_DIALOG = XmlCommand1(
    "Dialog Level", "SetDialogLevel",
    (0, 48)
)

QUICK_SELECT = XmlCommand1(
    "Quick Select", "SetQuickSelect",
    (1, 4)
)

#SetSoundMode and SetSoundModeList need more attention.
