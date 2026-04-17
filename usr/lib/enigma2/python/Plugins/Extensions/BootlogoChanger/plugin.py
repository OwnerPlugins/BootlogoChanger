#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from os import listdir, remove
from os.path import exists, isfile, join
from random import randint
from xml.dom import minidom
from importlib import reload

from Components.config import config
from Tools.Directories import SCOPE_PLUGINS, copyfile, resolveFilename

from . import (
    _,
    PLUGINPATH,
    bootlogoChanger_version,
    img_bootlogo_directory,
    status_xml,
)

from . import BootlogoChanger


def main(session, **kwargs):
    reload(BootlogoChanger)

    try:
        session.open(BootlogoChanger.BootlogoChangerMain)
    except:
        import traceback
        traceback.print_exc()


def autostart(reason, **kwargs):
    if reason == 1:
        if config.BootlogoChanger.randomization.value:
            bootlogo_directory = config.BootlogoChanger.bootlogo_directory.value
            debug = config.BootlogoChanger.debug.value
            delete_old_files = config.BootlogoChanger.delete_mvi_before_copy.value
            print(_("[BootlogoChanger] randomization of bootlogos activated"))
            xml_file = resolveFilename(SCOPE_PLUGINS, status_xml)
            if isfile(xml_file):
                xml_bootlogos = minidom.parse(xml_file)

                item_list = []
                for bootlogo in xml_bootlogos.firstChild.childNodes:
                    if bootlogo.nodeType == bootlogo.ELEMENT_NODE and bootlogo.localName == "bootlogo":
                        name = str(bootlogo.getAttribute("name"))
                        status = str(bootlogo.getAttribute("status"))
                        if status == "checked":
                            item_list.append(name)
                            if debug:
                                print(_("[BootlogoChanger] randomization: bootlogo found") + ": " + name)

                items_count = len(item_list)
                if debug:
                    print("[BootlogoChanger] randomization: items_count: " + str(items_count))
                if items_count != 0:
                    copyfiles = True
                    new_logo_index = randint(0, items_count - 1)
                    if debug:
                        print("[BootlogoChanger] randomization: new_logo_index: " + str(new_logo_index))
                    selected_bootlogo = bootlogo_directory + item_list[new_logo_index] + "/"
                    if debug:
                        print("[BootlogoChanger] randomization: selected_bootlogo: " + selected_bootlogo)

                    filelist = [x for x in listdir(selected_bootlogo) if x.endswith(".mvi")]
                    if not filelist == []:
                        if delete_old_files:
                            oldfilelist = [x for x in listdir(img_bootlogo_directory) if
                                           (x.endswith(".mvi") and not (x == "backdrop.mvi"))]
                            if not oldfilelist == []:
                                for file in oldfilelist:
                                    if isfile(bootlogo_directory + file):
                                        remove(bootlogo_directory + file)
                                    if debug:
                                        print(_(
                                            "[BootlogoChanger] deleting old bootlogo files") + ": " + bootlogo_directory + file + "\n")
                        for file in filelist:
                            if (copyfile(selected_bootlogo + file, bootlogo_directory)) != 0:
                                copyfiles = False

                                print(_(
                                    "[BootlogoChanger] copy failed") + ": " + selected_bootlogo + file + " nach " + bootlogo_directory + "\n")
                                break
                        if copyfiles:
                            print(
                                _("[BootlogoChanger] activated new bootlogo") + ": " + item_list[new_logo_index] + "\n")
                        else:
                            print(_("[BootlogoChanger] activating new bootlogo failed") + ": " + item_list[
                                new_logo_index] + "\n")
                    else:
                        print(_("[BootlogoChanger] no bootlogos for randomization selected") + "!\n")
        else:
            print(_("[BootlogoChanger] randomization of bootlogos deactivated"))


def Plugins(**kwargs):
    from Plugins.Plugin import PluginDescriptor
    pname = "BootlogoChanger"
    pdesc = _("Easily switch between different bootlogos")
    return [
        PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
        PluginDescriptor(
            name=pname,
            description=pdesc + " (" + bootlogoChanger_version + ")",
            where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU],
            fnc=main,
            needsRestart=False,
            icon='plugin.png')
    ]
