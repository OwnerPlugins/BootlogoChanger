#!/usr/bin/python3
# -*- coding: utf-8 -*-

from os import listdir, remove
from os.path import exists, isfile, isdir
from re import sub
from subprocess import PIPE, Popen
from xml.dom import minidom
from xml.dom.minidom import Document
from enigma import ePicLoad, eTimer, getDesktop
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import (
    ConfigDirectory,
    ConfigInteger,
    ConfigOnOff,
    ConfigSelection,
    ConfigSubList,
    ConfigSubsection,
    ConfigYesNo,
    config,
    configfile,
    getConfigListEntry,
)
from Screens.HelpMenu import HelpableScreen
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import SCOPE_PLUGINS, copyfile, resolveFilename

from . import (
    _,
    __version__,
    author,
    bootlogoChanger_date,
    bootlogoChanger_icon,
    bootlogo_preview,
    ignore_xml,
    img_bootlogo_directory,
    item_checked,
    item_original,
    item_unchecked,
    no_preview,
    status_xml,
)

current_bootlogo = _("Current bootlogo")

# TRANSLATORS: keep it short, this is a button
randomization_status = _("Random mode") + ": " + _("off")
mviFiles = ["bootlogo.mvi", "bootlogo_wait.mvi", "reboot.mvi", "shutdown.mvi", "update_in_progress.mvi",
            "radio.mvi", "backdrop.mvi"]
jpgFiles = ["bootlogo.jpg", "bootlogo_wait.jpg", "reboot.jpg", "shutdown.jpg", "update_in_progress.jpg",
            "radio.jpg", "backdrop.jpg"]
size_status_png = 40

config.BootlogoChanger = ConfigSubsection()
config.BootlogoChanger.randomization = ConfigOnOff(default=False)
config.BootlogoChanger.ignore_empty_folder = ConfigYesNo(default=True)
config.BootlogoChanger.delete_mvi_before_copy = ConfigYesNo(default=False)
config.BootlogoChanger.ffmpeg = ConfigSelection(default="0", choices=[
    ("0", _("install")),
    ("1", _("deinstall"))])
config.BootlogoChanger.preview_picture = ConfigSelection(default="0", choices=[
    ("0", "bootlogo"),
    ("1", "bootlogo_wait"),
    ("2", "reboot"),
    ("3", "shutdown"),
    ("4", "update_in_progress"),
    ("5", "radio"),
    ("6", "backdrop")])
config.BootlogoChanger.bootlogo_directory = ConfigDirectory(default=img_bootlogo_directory, visible_width=30)

config.BootlogoChanger.status_text_time = ConfigInteger(default=5, limits=(1, 60))
config.BootlogoChanger.debug = ConfigOnOff(default=False)


def getPic(x_size, y_size, filename):
    if exists(filename):
        picon = ePicLoad()
        scale = AVSwitch().getFramebufferScale()
        picon.setPara([x_size, y_size, scale[0], scale[1], 0, 1, '#00000000'])
        if exists("/var/lib/dpkg/status"):
            picon.startDecode(filename, False)
        else:
            picon.startDecode(filename, 0, 0, False)
        return picon.getData()


def safe_quote(s):
    """Simula l'effetto di shlex.quote() per evitare problemi di injection."""
    return "'" + sub(r"([^a-zA-Z0-9_])", r"\\\1", s) + "'"


def execute_command(cmd):
    try:
        output, error = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True).communicate()
        return output.decode('utf-8', errors='ignore'), error.decode('utf-8', errors='ignore')
    except OSError:
        import traceback
        traceback.print_exc()
        return "", "Error"


def install_ffmpeg():
    cmd = "opkg install 'ffmpeg'"
    output, error = execute_command(cmd)
    if error == "":
        return True
    else:
        return False


def remove_ffmpeg():
    cmd = "opkg remove 'ffmpeg'"
    output, error = execute_command(cmd)
    if error == "":
        return True
    else:
        return False


def is_ffmpeg_installed():
    cmd = "opkg list-installed 'ffmpeg'"
    output, error = execute_command(cmd)
    if output != "":
        print(_("[BootlogoChanger] found ffmpeg") + "\n")
        return True
    else:
        print(_("[BootlogoChanger] ffmpeg not found") + "\n")
        return False


class BootlogoChangerMain(Screen, HelpableScreen):
    skin = """
        <screen title="BootlogoChanger" position="center,center" size="1280,720">
            <widget name="titleBootlogos" position="20,20" size="610,50" valign="center" halign="center" font="Regular;32" foregroundColor="#FFFF00"/>
            <widget source="bootlogo_menu" render="Listbox" position="20,80" size="610,510" scrollbarMode="showOnDemand" transparent="1">
                <convert type="TemplatedMultiContent">
                    {"template": [
                     MultiContentEntryPixmapAlphaBlend(pos = (0, 0), size = (40, 40), backcolor=None, backcolor_sel=None, png = 0),
                     MultiContentEntryText(pos = (60, 0), size = (550, 50), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1),
                    ],
                    "fonts": [gFont("Regular", 32)],
                    "itemHeight": 60
                    }
                </convert>
            </widget>

            <widget name="titlePreview" position="650,20" size="610,50" valign="center" halign="center" font="Regular;32" foregroundColor="#FFFF00"/>
            <widget name="preview" position="650,80" size="610,300" zPosition="1" alphatest="on"/>

            <widget name="titleScreens"           position="650,390" size="610,50" font="Regular;32" foregroundColor="#FFFF00" valign="center" halign="center"/>
            <eLabel text="bootlogo.mvi"           position="740,450" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="bootlogo_wai.mvi"       position="740,480" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="reboot.mvi"             position="740,510" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="shutdown.mvi"           position="740,540" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="update_in_progress.mvi" position="740,570" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="radio.mvi"              position="740,600" size="300,30" font="Regular;24" foregroundColor="white"/>
            <eLabel text="backdrop.mvi"           position="740,630" size="300,30" font="Regular;24" foregroundColor="white"/>

            <widget name="mviGefunden1" position="1035,450" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden2" position="1035,480" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden3" position="1035,510" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden4" position="1035,540" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden5" position="1035,570" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden6" position="1035,600" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>
            <widget name="mviGefunden7" position="1035,630" size="125,30" foregroundColor="green" font="Regular;24" halign="center"/>

            <widget name="mviFehlt1" position="1035,450" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt2" position="1035,480" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt3" position="1035,510" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt4" position="1035,540" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt5" position="1035,570" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt6" position="1035,600" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>
            <widget name="mviFehlt7" position="1035,630" size="125,30" foregroundColor="red" font="Regular;24" halign="center"/>

            <widget name="status_text_info"  position="20,600" size="710,80" foregroundColor="green" font="Regular;24" halign="left" valign="center"/>
            <widget name="status_text_error" position="20,600" size="710,80" foregroundColor="red" font="Regular;24" halign="left" valign="center"/>

            <widget name="key_red" position="10,680" size="253,36" backgroundColor="red" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="key_green" position="273,680" size="253,36" backgroundColor="green" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="key_yellow" position="536,680" size="253,36" backgroundColor="yellow" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <widget name="key_blue" position="799,680" size="253,36" backgroundColor="blue" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
            <eLabel name="button OK" position="1063,686" size="60,30" text="OK" font="Regular; 17" halign="center" valign="center" foregroundColor="white" backgroundColor="black" zPosition="1"/>
            <eLabel name="button OK bg" position="1062,685" size="62,32" backgroundColor="white" zPosition="0"/>
            <eLabel name="button menu" position="1135,686" size="60,30" text="Menü" font="Regular; 17" halign="center" valign="center" foregroundColor="white" backgroundColor="black" zPosition="1"/>
            <eLabel name="button menu bg" position="1134,685" size="62,32" backgroundColor="white" zPosition="0"/>
            <eLabel name="button help" position="1207,686" size="60,30" text="Hilfe" font="Regular; 17" halign="center" valign="center" foregroundColor="white" backgroundColor="black" zPosition="1"/>
            <eLabel name="button help bg" position="1206,685" size="62,32" backgroundColor="white" zPosition="0"/>
        </screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)

        self.setTitle("BootlogoChanger v" + __version__)
        self["myActionMap"] = ActionMap(
            [
                "BootlogoChangerActions"
            ],
            {
                "ok": self.showFullsize,
                 "cancel": self.close,
                 "moveUp": self.goUp,
                 "moveDown": self.goDown,
                 "movePageUp": self.goPageUp,
                 "movePageDown": self.goPageDown,
                 "red": self.close,
                 "green": self.save,
                 "yellow": self.randomization,
                 "blue": self.changeItemRandomizationStatus,
                 "menu": self.menu
            }, -1
        )

        self["titleBootlogos"] = Label(_("Found bootlogos"))
        self["titlePreview"] = Label(_("Preview picture"))
        self["titleScreens"] = Label(_("Included Screens"))
        for i in range(len(mviFiles)):
            self["mviGefunden" + str(i + 1)] = Label()
            self["mviGefunden" + str(i + 1)].setText(_("found"))
            self["mviGefunden" + str(i + 1)].hide()
            self["mviFehlt" + str(i + 1)] = Label()
            self["mviFehlt" + str(i + 1)].setText(_("missing"))
            self["mviFehlt" + str(i + 1)].hide()

        self.debug = config.BootlogoChanger.debug.value
        self.previewPicture = config.BootlogoChanger.preview_picture.getText()
        self.bootlogo_directory = config.BootlogoChanger.bootlogo_directory.value
        self.delete_old_files = config.BootlogoChanger.delete_mvi_before_copy.value

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_yellow"] = Label(randomization_status)
        self["key_blue"] = Label("include/exclude")
        self["key_blue"].hide()
        self["status_text_info"] = Label("")
        self["status_text_info"].hide()
        self["status_text_error"] = Label("")
        self["status_text_error"].hide()
        self.textTimer = eTimer()
        self.textTimer.callback.append(self.hideText)
        self["preview"] = Pixmap()
        self.bootlogo_menu_backup = []
        self.all_bootlogos_list = []
        self.ignore_list = []
        self["bootlogo_menu"] = List()
        self.bootlogos_list = []
        self.selectedBootlogo = ""
        self.selectedBootlogoPreviewPic = ""
        self.index = ""
        self.status_pic = ""
        self.bootlogoName = ""
        self.mviFile = ""
        self.Scale = AVSwitch().getFramebufferScale()

        self.helpList.append(
            (self["myActionMap"], "BootlogoChangerActions", [("ok", _("Full screen view the selected bootlogo"))]))
        self.helpList.append((self["myActionMap"], "BootlogoChangerActions", [("menu", _("Open settings"))]))
        self.helpList.append(
            (self["myActionMap"], "BootlogoChangerActions", [("cancel", _("Exit plugin without saving"))]))
        self.helpList.append(
            (self["myActionMap"], "BootlogoChangerActions", [("red", _("Exit plugin without saving"))]))
        self.helpList.append(
            (self["myActionMap"], "BootlogoChangerActions", [("green", _("Save Changes and exit plugin"))]))
        self.helpList.append((self["myActionMap"], "BootlogoChangerActions",
                              [("yellow", _("Choose random bootlogo at the start of the box"))]))
        self.helpList.append(
            (self["myActionMap"], "BootlogoChangerActions", [("blue", _("Include or exlude logo in random choice"))]))

        self.png_checked = getPic(size_status_png, size_status_png, resolveFilename(SCOPE_PLUGINS, item_checked))
        self.png_unchecked = getPic(size_status_png, size_status_png, resolveFilename(SCOPE_PLUGINS, item_unchecked))
        self.png_original = getPic(size_status_png, size_status_png, resolveFilename(SCOPE_PLUGINS, item_original))

        if isfile(self.bootlogo_directory + bootlogo_preview):
            remove(self.bootlogo_directory + bootlogo_preview)
        if not is_ffmpeg_installed():
            self.showText(_(
                "FFmpeg ist missing, no preview pictures available - there is an option to install it in the stettings"),
                "error")
        self.onLayoutFinish.append(self.init_menu)

    def init_menu(self):
        self.createAllBootlogosList()
        self.createIgnoreList()
        self.createBootlogoMenu()
        self.updateRandomizationSettings()
        self.loadPreview()

    def goUp(self):
        self["bootlogo_menu"].up()
        self.loadPreview()

    def goDown(self):
        self["bootlogo_menu"].down()
        self.loadPreview()

    def goPageUp(self):
        self["bootlogo_menu"].pageUp()
        self.loadPreview()

    def goPageDown(self):
        self["bootlogo_menu"].pageDown()
        self.loadPreview()

    def menu(self):
        configfile.save()
        self.saveRandomizationStatus()
        self.session.openWithCallback(self.setConf, BLCSetup, self.all_bootlogos_list, self.ignore_list)

    def setConf(self):
        self.setTitle("BootlogoChanger v" + __version__)
        if config.BootlogoChanger.ffmpeg.value == "0" and not is_ffmpeg_installed():
            if install_ffmpeg():
                self.showText(_("FFmpeg successfully installed"), "info")
            else:
                self.showText(_("Installation of FFmpeg failed") + "!", "error")
        if config.BootlogoChanger.ffmpeg.value == "1" and is_ffmpeg_installed():
            if remove_ffmpeg():
                self.showText(_("FFmpeg removed successfully"), "info")
            else:
                self.showText(_("Deinstallation of FFmpeg failed") + "!", "error")

        if config.BootlogoChanger.preview_picture.getText() != self.previewPicture:
            if self.debug:
                print(_("[BootlogoChanger] previewPicture changed") + "!\n")
            if config.BootlogoChanger.preview_picture.getText() == "Ausschalten":
                self.previewPicture = "shutdown"
            else:
                self.previewPicture = config.BootlogoChanger.preview_picture.getText()
            self.deletePreviewPictures()
        self.bootlogo_directory = config.BootlogoChanger.bootlogo_directory.value
        self.debug = config.BootlogoChanger.debug.value
        self.delete_old_files = config.BootlogoChanger.delete_mvi_before_copy.value
        configfile.save()
        self.init_menu()

    def deletePreviewPictures(self):
        for x in range(len(self.bootlogos_list)):
            if self.bootlogos_list[x][1] == current_bootlogo:
                previewPicture = img_bootlogo_directory + bootlogo_preview
            else:
                previewPicture = self.bootlogo_directory + self.bootlogos_list[x][1] + "/" + bootlogo_preview
            if self.debug:
                print(_("[BootlogoChanger] deleting previewPicture") + ": " + str(previewPicture) + "\n")
            if isfile(previewPicture):
                remove(previewPicture)

    def loadRandomizationStatus(self):
        xml_file = resolveFilename(SCOPE_PLUGINS, status_xml)
        if isfile(xml_file):
            xml_bootlogos = minidom.parse(xml_file)

            for bootlogo in xml_bootlogos.firstChild.childNodes:
                if bootlogo.nodeType == bootlogo.ELEMENT_NODE and bootlogo.localName == "bootlogo":
                    name = str(bootlogo.getAttribute("name"))
                    status = str(bootlogo.getAttribute("status"))

                    menu_tmp = list(self["bootlogo_menu"].list)
                    for x in range(len(menu_tmp)):
                        if menu_tmp[x][1] == name:
                            if status == "checked":
                                menu_tmp[x] = (self.png_checked, name)
                            else:
                                menu_tmp[x] = (self.png_unchecked, name)
                    self["bootlogo_menu"].setList(menu_tmp)
        self.bootlogo_menu_backup = list(self["bootlogo_menu"].list)

    def createAllBootlogosList(self):
        self.all_bootlogos_list = []
        files = listdir(self.bootlogo_directory)
        files.sort()
        for x in files:
            path_tmp = self.bootlogo_directory + x
            if isdir(path_tmp):
                if config.BootlogoChanger.ignore_empty_folder.value:
                    list_mvi = [i for i in listdir(path_tmp) if i.endswith(".mvi")]
                    if not list_mvi == []:
                        self.all_bootlogos_list.append(x)
                else:
                    self.all_bootlogos_list.append(x)

        if self.debug:
            print(_("[BootlogoChanger] found Bootlogos") + ":\n")
            for x in range(len(self.all_bootlogos_list)):
                print("[BootlogoChanger] 		" + self.all_bootlogos_list[x] + "\n")

    def createIgnoreList(self):
        self.ignore_list = []
        xml_file = resolveFilename(SCOPE_PLUGINS, ignore_xml)
        if isfile(xml_file):
            xml_ignore_bootlogos = minidom.parse(xml_file)

            for bootlogo in xml_ignore_bootlogos.firstChild.childNodes:
                if bootlogo.nodeType == bootlogo.ELEMENT_NODE and bootlogo.localName == "bootlogo":
                    self.ignore_list.append(str(bootlogo.getAttribute("name")))

    def createBootlogoMenu(self):
        self.bootlogos_list = []
        self.bootlogos_list.append((self.png_original, current_bootlogo))

        for x in range(len(self.all_bootlogos_list)):
            if self.all_bootlogos_list[x] not in self.ignore_list:
                self.bootlogos_list.append((self.png_checked, self.all_bootlogos_list[x]))

        self["bootlogo_menu"].setList(self.bootlogos_list)
        self.loadRandomizationStatus()

        if self.debug:
            print(_("[BootlogoChanger] selected bootlogos") + ":\n")
            for x in range(len(self.bootlogos_list)):
                print("[BootlogoChanger] 		" + self.bootlogos_list[x][1] + "\n")

    def changeItemRandomizationStatus(self):
        if (not self.status_pic == self.png_original) and self["key_blue"].visible:
            self.getItem()

            if self.status_pic == self.png_checked:
                self.status_pic = self.png_unchecked
                self.showText(_("Bootlogo is excluded from random selection"), "info")
            else:
                self.status_pic = self.png_checked
                self.showText(_("Bootlogo is included in random selection"), "info")

            self["bootlogo_menu"].modifyEntry(self.index, tuple([self.status_pic, self.bootlogoName]))

    def setBlueKey(self):
        if self["key_blue"].visible:
            if self.status_pic == self.png_checked:
                self["key_blue"].setText(_("Exclude"))
            elif self.status_pic == self.png_unchecked:
                self["key_blue"].setText(_("Include"))
            elif self.status_pic == self.png_original:
                self["key_blue"].setText("")

    def getItem(self):
        self.bootlogoName = ""
        self.status_pic = ""
        self.index = ""

        self.index = self["bootlogo_menu"].getIndex()
        item = self["bootlogo_menu"].getCurrent()
        if item:
            self.status_pic = item[0]
            if item[1] == current_bootlogo:
                self.bootlogoName = ""
                self.selectedBootlogo = img_bootlogo_directory + self.bootlogoName
            else:
                self.bootlogoName = item[1]
                self.selectedBootlogo = self.bootlogo_directory + self.bootlogoName + "/"
        self.selectedBootlogoPreviewPic = self.selectedBootlogo + bootlogo_preview
        if self.debug:
            print("[BootlogoChanger] bootlogoName: " + str(self.bootlogoName) + "\n")
        if self.debug:
            print("[BootlogoChanger] selectedBootlogo: " + str(self.selectedBootlogo) + "\n")
        self.setBlueKey()

    def loadPreview(self):
        self.getItem()
        if self.debug:
            print("[BootlogoChanger] selectedBootlogoPreviewPic: " + str(self.selectedBootlogoPreviewPic) + "\n")
        if not isfile(self.selectedBootlogoPreviewPic):
            if not self.extractPreviewJPG():
                self.selectedBootlogoPreviewPic = resolveFilename(SCOPE_PLUGINS, no_preview)

        ptr = getPic(self["preview"].instance.size().width(), self["preview"].instance.size().height(),
                     self.selectedBootlogoPreviewPic)
        if ptr is not None:
            self["preview"].instance.setPixmap(ptr.__deref__())
            # self['preview'].instance.setPixmap(ptr)

        self.findMVIFiles()

    def findMVIFiles(self):
        for x in range(len(mviFiles)):
            if isfile(self.selectedBootlogo + mviFiles[x]) is True:
                self["mviGefunden" + str(x + 1)].show()
                self["mviFehlt" + str(x + 1)].hide()
            else:
                self["mviGefunden" + str(x + 1)].hide()
                self["mviFehlt" + str(x + 1)].show()

    def showFullsize(self):
        self.session.open(PicFullView, self.selectedBootlogoPreviewPic)

    def save(self):
        configfile.save()
        self.saveRandomizationStatus()
        self.copyLogoFiles()
        self.close()

    def saveRandomizationStatus(self):
        if self["key_blue"].visible:
            xml_file = resolveFilename(SCOPE_PLUGINS, status_xml)
            xml_bootlogos = Document()
            bootlogos = xml_bootlogos.createElement("bootlogos")
            xml_bootlogos.appendChild(bootlogos)
            for bootlogo in self["bootlogo_menu"].list:
                if bootlogo[0] != self.png_original:
                    xml_item = xml_bootlogos.createElement("bootlogo")
                    xml_item.setAttribute("name", bootlogo[1])
                    status = "checked" if bootlogo[0] == self.png_checked else "unchecked"
                    xml_item.setAttribute("status", status)
                    bootlogos.appendChild(xml_item)

            prettyxml = xml_bootlogos.toprettyxml()
            with open(xml_file, "w", encoding="utf-8") as file:
                file.write(prettyxml)

    def updateRandomizationSettings(self):
        randomization_tmp = randomization_status
        if config.BootlogoChanger.randomization.value:
            randomization_tmp += _("on")
            self["key_blue"].show()
            self["bootlogo_menu"].setList(self.bootlogo_menu_backup)
        else:
            randomization_tmp += _("off")
            self["key_blue"].hide()
            self.bootlogo_menu_backup = list(self["bootlogo_menu"].list)
            menu_tmp = list(self["bootlogo_menu"].list)
            for x in range(len(menu_tmp)):
                menu_tmp[x] = (self.png_original, menu_tmp[x][1])
            self["bootlogo_menu"].setList(menu_tmp)
        self["key_yellow"].setText(randomization_tmp)
        self.setBlueKey()

    def randomization(self):
        if config.BootlogoChanger.randomization.value:
            config.BootlogoChanger.randomization.setValue(False)
            self.showText(_("Random selection at startup disabled"), "info")
        else:
            config.BootlogoChanger.randomization.setValue(True)
            self.showText(_("Random selection at startup enabled"), "info")
        self.updateRandomizationSettings()
        config.BootlogoChanger.randomization.save()

    def copyLogoFiles(self):
        try:
            copyfiles = True
            if self.selectedBootlogo != self.bootlogo_directory:
                filelist = [x for x in listdir(self.selectedBootlogo) if x.endswith(".mvi")]
                if not filelist == []:
                    if self.delete_old_files:
                        oldfilelist = [x for x in listdir(img_bootlogo_directory) if
                                       (x.endswith(".mvi") and not (x == "backdrop.mvi"))]
                        if not oldfilelist == []:
                            for file in oldfilelist:
                                if isfile(self.bootlogo_directory + file):
                                    remove(self.bootlogo_directory + file)
                                if self.debug:
                                    print(_(
                                        "[BootlogoChanger] deleting old bootlogo files") + ": " + self.bootlogo_directory + file + "\n")
                    for file in filelist:
                        if (copyfile(self.selectedBootlogo + file, self.bootlogo_directory)) != 0:
                            copyfiles = False
                            print(_("[BootlogoChanger] copy failed") + ": " + self.selectedBootlogo + file[
                                1] + " nach " + self.bootlogo_directory + "\n")
                            break
                    if copyfiles:
                        print(_("[BootlogoChanger] activated new bootlogo") + ": " + self.selectedBootlogo + "\n")
                    else:
                        self.session.open(MessageBox, _("Copy logofiles failed") + ": " + self.selectedBootlogo + "\n",
                                          MessageBox.TYPE_WARNING)
                else:
                    self.session.open(MessageBox,
                                      _("No bootlogos found in directory") + ": " + self.selectedBootlogo + "\n",
                                      MessageBox.TYPE_WARNING)
            return copyfiles
        except:
            import traceback
            traceback.print_exc()

    def extractPreviewJPG(self):
        cmd = "ffmpeg -f mpegvideo -i \"" + self.selectedBootlogo + self.previewPicture + ".mvi\" -vframes 1 -loglevel error -hide_banner \"" + self.selectedBootlogoPreviewPic + "\""
        print('convert mvi to jpg =', cmd)
        if self.debug:
            print("[BootlogoChanger] cmd: " + str(cmd) + "\n")
        output, error = execute_command(cmd)
        if isfile(self.selectedBootlogoPreviewPic):
            if self.debug:
                print("[BootlogoChanger] extractPreviewJPG ffmpeg stdout: " + str(output) + "\n")
            return True
        else:
            if self.debug:
                print("[BootlogoChanger] extractPreviewJPG ffmpeg stderr: " + str(error) + "\n")
            return False

    def showText(self, text, type_text):
        if type_text == "info":
            self["status_text_info"].setText(text)
            self["status_text_info"].show()
        else:
            self["status_text_error"].setText(text)
            self["status_text_error"].show()
        self.textTimer.stop()
        self.textTimer.start(config.BootlogoChanger.status_text_time.value * 1000, 1)

    def hideText(self):
        self["status_text_info"].hide()
        self["status_text_error"].hide()


class PicFullView(Screen):
    def __init__(self, session, png_file):
        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()
        self.png_file = png_file
        self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
        <widget name=\"pic\" position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" zPosition=\"5\" alphatest=\"on\" /> \
        </screen>"
        Screen.__init__(self, session)
        self["pic"] = Pixmap()
        self["myActionMap"] = ActionMap(["BootlogoChangerActions"],
                                        {"ok": self.Exit,
                                         "cancel": self.Exit}, -1)
        self.onLayoutFinish.append(self.loadFullPreview)

    def loadFullPreview(self):
        ptr = getPic(self["pic"].instance.size().width(), self["pic"].instance.size().height(), self.png_file)
        if ptr is not None:
            self["pic"].instance.setPixmap(ptr.__deref__())

    def Exit(self):
        self.close()


def LocationBoxClosed(path):
    if path is not None:
        if path.endswith('/'):
            config.BootlogoChanger.bootlogo_directory.setValue(path)
        else:
            config.BootlogoChanger.bootlogo_directory.setValue(path) + "/"


class BLCSetup(Screen, ConfigListScreen):
    def __init__(self, session, allBootlogosList, ignoreList):
        self.allBootlogosList = allBootlogosList
        self.ignoreList = ignoreList
        config.BootlogoChanger.logos = ConfigSubList()
        for i in range(len(self.allBootlogosList)):
            if self.allBootlogosList[i] in self.ignoreList:
                config.BootlogoChanger.logos.append(ConfigYesNo(default=False))
            else:
                config.BootlogoChanger.logos.append(ConfigYesNo(default=True))

        Screen.__init__(self, session)
        self.skinName = ["BootlogoChanger Setup", "Setup"]
        self.setup_title = "BootlogoChanger - Settings"
        self.onChangedEntry = []
        self.session = session
        self["actions"] = ActionMap(
            [
                "SetupActions"
            ],
            {
                "cancel": self.close,
                 "save": self.save,
                 "ok": self.ok
            }, -2
        )
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("OK"))
        self["configdesc"] = StaticText()

        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self["config"].onSelectionChanged.append(self.updateHelp)
        self.setTitle(self.setup_title)
        self.onLayoutFinish.append(self.createSetup)

    def createSetup(self):
        self.list = []
        self.list.append(getConfigListEntry(_("Install/deinstall ffmpeg"), config.BootlogoChanger.ffmpeg,
                                            _("FFmpeg is needed to generate thumbnails from the mvi files")))
        self.list.append(getConfigListEntry(_("Preview Logo"), config.BootlogoChanger.preview_picture,
                                            _("Which logo should be displayed as a preview picture?")))
        self.list.append(
            getConfigListEntry(_("Directory with bootlogo folders"), config.BootlogoChanger.bootlogo_directory,
                               _("Search for folders with boot logos in this directory")))
        self.list.append(getConfigListEntry(_("Delete current mvi-files before changing bootlogo"),
                                            config.BootlogoChanger.delete_mvi_before_copy,
                                            _(
                                                "First delete the mvi-files of the current bootlogo then copy the files of the new one")))
        self.list.append(getConfigListEntry(_("Hide empty directories"),
                                            config.BootlogoChanger.ignore_empty_folder,
                                            _("Hide directories without 'mvi'-files")))
        self.list.append(
            getConfigListEntry(_("Display duration of the status messages (sec)"),
                               config.BootlogoChanger.status_text_time,
                               _("How many seconds should status messages be displayed (1-60 sec)")))
        self.list.append(
            getConfigListEntry(_("Debugmode"), config.BootlogoChanger.debug,
                               _("Activate the debug-output on console")))
        section0 = ("-----------------  ABOUT:  -----------------")
        self.list.append(section0)

        section1 = ("BootlogoChanger | " + __version__)
        self.list.append(section1)

        section2 = ("Last Update date: " + bootlogoChanger_date)
        self.list.append(getConfigListEntry(section2))

        section3 = ("by " + author)
        self.list.append(getConfigListEntry(section3))

        section4 = ('---------------  BOOTLOGOS:  ---------------')
        self.list.append(getConfigListEntry(section4))

        for i in range(len(self.allBootlogosList)):
            self.list.append(getConfigListEntry(self.allBootlogosList[i], config.BootlogoChanger.logos[i],
                                                _("Which bootlogos should be displayed?")))

        self["config"].list = self.list
        self["config"].l.setList(self.list)
        self.updateHelp()

    def updateHelp(self):
        cur = self["config"].getCurrent()
        if cur:
            self["configdesc"].text = cur[2]

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)

    def keyRight(self):
        ConfigListScreen.keyRight(self)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def ok(self):
        if self["config"].getCurrent()[1] == config.BootlogoChanger.bootlogo_directory:
            self.session.openWithCallback(LocationBoxClosed, LocationBox, _("Directory with bootlogo folders"),
                                          currDir=config.BootlogoChanger.bootlogo_directory.value)

    def save(self):
        xml_file = resolveFilename(SCOPE_PLUGINS, ignore_xml)
        xml_bootlogos = Document()
        bootlogos = xml_bootlogos.createElement("bootlogos")
        xml_bootlogos.appendChild(bootlogos)
        for x in range(len(self.allBootlogosList)):
            if not config.BootlogoChanger.logos[x].value:
                xml_item = xml_bootlogos.createElement("bootlogo")
                xml_item.setAttribute("name", self.allBootlogosList[x])
                bootlogos.appendChild(xml_item)
        prettyxml = xml_bootlogos.toprettyxml()
        with open(xml_file, "w", encoding="utf-8") as file:
            file.write(prettyxml)
        configfile.save()
        self.close()
