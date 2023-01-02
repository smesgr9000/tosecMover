#!/usr/bin/python

from color import cDim
from pathlib import Path
from scanfile import PlainFileReader, ScanFile
from strategyrename import Matcher
from strategy import Strategy
import logging

class StrategyScan(Strategy):
    """
    Strategy to scan every directory/files from the source directory.
    If a directory is found the content is retruned. Otherwise
    either doStrategyMatch or doStrategyNoMatch is called"""

    def __init__(self, matcher: Matcher):
        super().__init__()
        self._matcher = matcher

    def doStrategyScan(self, listPath: list[Path]) -> list[Path]:
        scanPath = super().doStrategyScan(listPath)
        return self.__scanDirectory(scanPath)

    def _scanFile(self, entry: Path):
        scan = ScanFile(PlainFileReader(entry))
        match = self._matcher.findMatch(scan)
        if match is None:
            self.doStrategyNoMatch(scan)
        else:
            self.doStrategyMatch(scan, match)

    def __scanDirectory(self, listPath: list[Path]) -> list[Path]:
        foundDirectories = []
        for scanPath in listPath:
            if scanPath.is_dir() and not scanPath.is_symlink():
                logging.debug("scan directory %s", cDim(scanPath.as_posix()))
                for entry in scanPath.iterdir():
                    if entry.is_file():
                        self._scanFile(entry)
                    elif not scanPath.is_symlink():
                        logging.debug("add directory %s to list to scan", cDim(entry.as_posix()))
                        foundDirectories.append(entry)
            elif scanPath.is_file():
                self._scanFile(scanPath)
        return foundDirectories
