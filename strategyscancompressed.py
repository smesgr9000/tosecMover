#!/usr/bin/python

from pathlib import Path
from scanfile import *
from strategyrename import Matcher
from strategyscan import StrategyScan
import logging
import zipfile

class ZipFileReader(IScanFileReader):
    """
    Implementation of IScanFileReader for a file in a ZIP archive.
    Not all operations are implemented yet :-("""

    def __init__(self, archive: Path, zipInfo: zipfile.ZipInfo):
        self.__zipInfo = zipInfo
        self.__archive = archive
        self.__file = None
        self.__size = zipInfo.file_size
        self.name = Path(zipInfo.filename).name

    def open(self):
        if self.__file is not None:
            logging.warning("zip file is already open %s", cDim(self.as_posix()))
            return
        self.__file = self.__archive.open(self.__zipInfo)

    def close(self):
        if self.__file is None:
            logging.warning("zip file is already closed %s", cDim(self.as_posix()))
            return
        self.__file.close()
        self.__file = None

    def size(self):
        return self.__size

    def read(self, size: int):
        return self.__file.read(size)

    def as_posix(self):
        return self.__archive.filename + '/' + self.__zipInfo.filename

    def rename(self, destFile: Path):
        self.__archive.extract(self.__zipInfo, destFile)
        # TODO remove file from archive currently not supported by 
        # Python see https://github.com/python/cpython/pull/19358
        # either wait for that MR or after complete file is scaned
        # delete the complete zip or create new zip and move over all left over files
        logging.warning("Moving a zip entry is not supported right now. File is only extracted %s", cDIM(self.as_posix()))

    def unlink(self):
        # TODO See rename
        logging.warning("Deleting a zip entry is not supported right now. File Skipped %s", cDIM(self.as_posix()))

class StrategyScanCompressed(StrategyScan):
    """
    Strategy to scan every directory/files from the source directory.
    If a directory is found the content is retruned. 
    Otherwise the file is checked. If Matcher does not match and file is a
    ZIP archive every entry of the ZIP archive is scaned.
    For each found entry either doStrategyMatch or doStrategyNoMatch is called.
    doStrategyNoMatch is called for the ZIP archive if the ZIP has either no
    entry or an error occurs while processing the ZIP archive."""

    def __init__(self, matcher: Matcher):
        super().__init__(matcher)

    def _scanFile(self, entry: Path):
        scan = ScanFile(PlainFileReader(entry))
        match = self._matcher.findMatch(scan)
        if match is None:
            if zipfile.is_zipfile(entry):
                self.__scanZipFile(entry)
            else:    
                self.doStrategyNoMatch(scan)
        else:
            self.doStrategyMatch(scan, match)

    def __scanZipFile(self, entry: Path):
        logging.debug("scan zip file %s", cDim(entry.as_posix()))
        zip = zipfile.ZipFile(entry)
        try:
            infoList = zip.infolist()
            if len(infoList) == 0:
                self.doStrategyNoMatch(entry)
                return

            for info in infoList:
                if info.is_dir():
                    continue
                logging.debug("scan zip file entry %s", cDim(info.filename))
                scan = ScanFile(ZipFileReader(zip, info))
                match = self._matcher.findMatch(scan)
                if match is None:
                    self.doStrategyNoMatch(scan)
                else:
                    self.doStrategyMatch(scan, match)
             return
        finally:
            zip.close()
        self.doStrategyNoMatch(entry)
