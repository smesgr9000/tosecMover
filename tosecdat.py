#!/usr/bin/python

from color import *
from pathlib import Path
from scanfile import ScanFile
import logging
import xml.etree.ElementTree

class InvalidTosecFileException(Exception):
    pass

class TosecHeader:
    """
    TOSEC DAT file Header. 
    On init the given XML tree is scaned for header and header/name.
    If XML elements aren't found an exception is raised """

    def __init__(self, root: xml.etree.ElementTree.Element):
        header = root.find("header")
        if header is None:
            raise InvalidTosecFileException("no datafile/header found")
        name = header.find("name")
        if name is None:
            raise InvalidTosecFileException("no datafile/header/name found")
        self.games = []
        self.name = name.text
        splitName = self.name.split(" - ", 1)
        self.system = splitName[0]
        self.category = splitName[1] if len(splitName) > 1 else None

class TosecGameEntry:
    """ 
    TOSEC DAT Game entry.
    On init the XML element is parsed. TODO support entries with more than one rom
    If XML structure doesn't fit a game entry an exception is raised """

    def __init__(self, gameEntry: xml.etree.ElementTree.Element, header: TosecHeader):
        self.header = header
        self.name = gameEntry.get("name")
        if self.name is None:
            raise InvalidTosecFileException("no {} found".format(cDim("datafile/game{name}")))
        roms = gameEntry.findall("rom")
        if len(roms) > 1:
            raise InvalidTosecFileException("multiple roms for a single game not supported yet")
        if len(roms) < 1:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom"), cDim(self.name)))
        rom = roms[0]
        self.fileName = rom.get("name")
        if self.fileName is None:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom{name}"), cDim(self.name)))
        self.size = rom.get("size")
        if self.fileName is None:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom{fileName}"), cDim(self.name)))
        self.md5 = rom.get("md5")
        if self.md5 is None:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom{md5}"), cDim(self.name)))
        self.crc = rom.get("crc")
        if self.crc is None:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom{crc}"), cDim(self.name)))
        self.sha1 = rom.get("sha1")
        if self.sha1 is None:
            raise InvalidTosecFileException("no {} found for game {}".format(cDim("datafile/game/rom{sha1}"), cDim(self.name)))
        logging.debug("Parsed game entry %s", cDim(str(self)))

    def isMatching(self, scanFile: ScanFile) -> bool:
        """ 
        Compare the given scanFile to the internal rom entry.
        @param scanFile 
            file to compare to the TOSEC DAT game entry
        @return 
            true if all criteria match, false otherwise """

        return scanFile is not None and self.md5 == scanFile.md5 and self.crc == scanFile.crc and self.size == str(scanFile.size)

    def getFileName(self, basePath: Path) -> Path:
        """ 
        Get the file path for the given Game entry based on the given base path
        the file path has the following structure <base>/<system>[/<category>]/<filename>.
        If TOSEC header has no category the hirachie level is skipped.
        The folder structure isn't created.
        @param basePath
            base path for the created path structure
        @return
            filename path to the game entry file
        """
        
        p = basePath / self.header.system
        if self.header.category is not None:
            p /= self.header.category
        return p / self.fileName