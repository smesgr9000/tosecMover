#!/usr/bin/python

from color import *
from pathlib import Path
from scanfile import ScanFile
from strategy import Strategy
from tosecdat import TosecGameRom
import logging

class Matcher:
    """
    Search files in the given ROM list. May return a list of TOSEC rom entries matching
    the file or None if no match could be found. Only accept matches with SHA1, MD5, size & CRC equal the TOSEC entry"""
    
    def __init__(self, romList: dict):
        self.__romList = romList

    def findMatch(self, scanFile: ScanFile) -> list[TosecGameRom]:
        if scanFile.isLoaded:
            if scanFile.sha1 in self.__romList:
                entry = self.__romList[scanFile.sha1];
                logging.debug("found file %s as ROM %s", cDim(scanFile.fileName.as_posix()), cDim(entry[0].name));
                if entry[0].isMatching(scanFile):
                    return entry
                logging.error("file %s matching sha1 but not other values for entry %s", cDim(vars(scanFile)), cDim(vars(entry)))
        return None

class StrategyRename(Strategy):
    """
    Strategy to move/rename every matching file from the source directory
    to the target directory. Ignore all files not matching in source.
    If a file should be renamed following cases are handeled:
    - target paths are not exising -> paths are created
    - target files already exists and is identical -> either skip or delete source @see --delDupes
    - target files already exists and it not identical -> move is skiped
    - several target files and move of first worked -> softlink other targets to first target"""

    def __init__(self, destPath: Path, matcher: Matcher, delDupes: bool):
        super().__init__()
        self.__destPath = destPath
        self.__matcher = matcher
        self.__delDupes = delDupes
    
    def doStrategyMatch(self, scanFile: ScanFile, tosecRomMatches: list[TosecGameRom]):
        super().doStrategyMatch(scanFile, tosecRomMatches)
        destFile = tosecRomMatches[0].getFileName(self.__destPath)
        self.createParentDirectories(destFile)
        if self.renameOrDeleteFoundFile(scanFile, destFile, tosecRomMatches[0]):
            for rom in tosecRomMatches[1:]:
                otherDestFile = rom.getFileName(self.__destPath)
                self.createParentDirectories(otherDestFile)
                self.softLink(scanFile, otherDestFile, destFile, rom)
        elif len(tosecRomMatches) > 1:
            logging.warning("Other entries found for %s skipped due to previous error", cDim(tosecRomMatches[0].name))

    def createParentDirectories(self, destFile: Path):
        if not destFile.parent.exists():
            logging.debug("creating directory %s", cDim(destFile.parent.as_posix()))
            destFile.parent.mkdir(parents=True)

    def softLink(self, scanFile: ScanFile, destFile: Path, linkTo: Path, tosecRomMatch: TosecGameRom):
        if destFile.is_symlink():
            destFile.unlink()
        if destFile.exists():
            self.handleDestFound(scanFile, destFile, tosecRomMatch, False)
        else:
            logging.info("softlink file %s to %s", cDim(destFile.as_posix()), cDim(linkTo.as_posix()))
            destFile.symlink_to(linkTo)

    def renameOrDeleteFoundFile(self, scanFile: ScanFile, destFile: Path, tosecRomMatch: TosecGameRom) -> bool:
        if destFile.is_symlink():
            destFile.unlink()
        if destFile.exists():
            return self.handleDestFound(scanFile, destFile, tosecRomMatch, self.__delDupes)
        else:
            logging.info("rename file %s to %s", cDim(scanFile.fileName.as_posix()), cDim(destFile.as_posix()))
            scanFile.fileName.rename(destFile)
            return True
            
    def handleDestFound(self, scanFile: ScanFile, destFile: Path, tosecRomMatch: TosecGameRom, deleteDups: bool):
        scanDest = ScanFile(destFile)
        matchDests = self.__matcher.findMatch(scanDest)
        if matchDests is None:
            logging.error("In destination directory file %s was found but does not match ROM it should have. File %s ignored", cDim(destFile.as_posix()), cDim(scanFile.fileName.as_posix()))
            return False
        if deleteDups:
            for matchDest in matchDests:
                logging.warning("Delete Duplicate file %s for matching ROM %s", cDim(scanFile.fileName.as_posix()), cDim(matchDest.name))
            srcEntry.unlink()
        else:
            for matchDest in matchDests:
                logging.warning("Duplicate file found %s for matching ROM %s. source file %s ignored", cDim(destFile.as_posix()), cDim(matchDest.name), cDim(scanFile.fileName.as_posix()))
        return True
