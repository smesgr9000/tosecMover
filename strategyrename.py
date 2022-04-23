#!/usr/bin/python

from color import *
from pathlib import Path
from scanfile import ScanFile
from strategy import Strategy
from tosecdat import TosecGameEntry
import logging

class Matcher:
    """
    Does Find a list of TOSEC game entries from the given game list 
    and the passed file or None. Only accept matches with SHA1, MD5, size & CRC equal"""
    
    def __init__(self, gameList: dict):
        self.__gameList = gameList

    def findMatch(self, scanFile: ScanFile) -> list[TosecGameEntry]:
        if scanFile.isLoaded:
            if scanFile.sha1 in self.__gameList:
                entry = self.__gameList[scanFile.sha1];
                logging.debug("found file %s as game %s", cDim(scanFile.fileName.as_posix()), cDim(entry[0].name));
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

    def __init__(self, destPath: Path, matcher: Matcher):
        super().__init__()
        self.__destPath = destPath
        self.__matcher = matcher
    
    def doStrategyMatch(self, scanFile: ScanFile, tosecEntry: list[TosecGameEntry]):
        super().doStrategyMatch(scanFile, tosecEntry)
        destFile = tosecEntry[0].getFileName(self.__destPath)
        self.createParentDirectories(destFile)
        if self.renameOrDeleteFoundFile(scanFile, destFile, tosecEntry[0]):
            for entry in tosecEntry[1:]:
                otherDestFile = entry.getFileName(self.__destPath)
                self.createParentDirectories(otherDestFile)
                self.softLink(scanFile, otherDestFile, destFile, entry)
        elif len(tosecEntry) > 1:
            logging.warning("Other entries found for %s skipped due to previous error", cDim(tosecEntry[0].name))

    def createParentDirectories(self, destFile: Path):
        if not destFile.parent.exists():
            logging.debug("creating directory %s", cDim(destFile.parent.as_posix()))
            destFile.parent.mkdir(parents=True)

    def softLink(self, scanFile: ScanFile, destFile: Path, linkTo: Path, tosecEntry: TosecGameEntry):
        if destFile.is_symlink():
            destFile.unlink()
        if destFile.exists():
            self.handleDestFound(scanFile, destFile, tosecEntry, False)
        else:
            logging.info("softlink file %s to %s", cDim(destFile.as_posix()), cDim(linkTo.as_posix()))
            destFile.symlink_to(linkTo)

    def renameOrDeleteFoundFile(self, scanFile: ScanFile, destFile: Path, tosecEntry: TosecGameEntry) -> bool:
        if destFile.is_symlink():
            destFile.unlink()
        if destFile.exists():
            return self.handleDestFound(scanFile, destFile, tosecEntry, args.delDupes)
        else:
            logging.info("rename file %s to %s", cDim(scanFile.fileName.as_posix()), cDim(destFile.as_posix()))
            scanFile.fileName.rename(destFile)
            return True
            
    def handleDestFound(self, scanFile: ScanFile, destFile: Path, tosecEntry: TosecGameEntry, deleteDups: bool):
        scanDest = ScanFile(destFile)
        matchDest = self.__matcher.findMatch(scanDest)
        if matchDest is None or tosecEntry.sha1 != matchDest.sha1:
            logging.error("In destination directory file %s was found but does not match entry it should have. File %s ignored", cDim(destFile.as_posix()), cDim(scanFile.fileName.as_posix()))
            return False
        if deleteDups:
            logging.warning("Delete Duplicate file %s for matching entry %s", cDim(scanFile.fileName.as_posix()), cDim(matchDest.name))
            srcEntry.unlink()
        else:
            logging.warning("Duplicate file found %s for matching entry %s. source file %s ignored", cDim(destFile.as_posix()), cDim(matchDest.name), cDim(scanFile.fileName.as_posix()))
        return True
