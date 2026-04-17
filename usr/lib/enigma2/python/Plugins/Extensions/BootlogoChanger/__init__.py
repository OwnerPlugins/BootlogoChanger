#!/usr/bin/python3
# -*- coding: utf-8 -*-

from gettext import bindtextdomain, dgettext, gettext
from os.path import join

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/BootlogoChanger/")
__version__ = "1.0.6"
author = "thirsty73"
bootlogoChanger_date = "17.04.2026"
bootlogoChanger_icon = "/images/BootlogoChanger.png"
img_bootlogo_directory = "/usr/share/"
bootlogo_preview = "preview.jpg"
item_checked = "Extensions/BootlogoChanger/images/checked.png"
item_unchecked = "Extensions/BootlogoChanger/images/unchecked.png"
item_original = "Extensions/BootlogoChanger/images/original.png"
no_preview = "Extensions/BootlogoChanger/images/no_preview.jpg"
status_xml = "Extensions/BootlogoChanger/BootlogoChanger.xml"
ignore_xml = "Extensions/BootlogoChanger/IgnoreBootlogos.xml"

# edit by Lululla 20260417 - porting and fix for python3


def localeInit():
    bindtextdomain("BootlogoChanger", join(PLUGINPATH, "locale"))


def _(txt):
    t = dgettext("BootlogoChanger", txt)
    t = gettext(txt) if t == txt else t
    return t


localeInit()
language.addCallback(localeInit)
