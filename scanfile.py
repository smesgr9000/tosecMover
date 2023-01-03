#!/usr/bin/python

from color import cDim
from pathlib import Path
import binascii
import hashlib
import logging

class IScanFileReader:
    """
    Interface for file operations used by ScanFile class."""

    name: str = None

    def open(self):
        pass

    def close(self):
        pass

    def read(self, size):
        pass

    def size(self):
        pass

    def as_posix(self):
        pass

    def rename(self, destFile: Path):
        pass

    def unlink(self):
        pass

class PlainFileReader(IScanFileReader):
    """
    Implementation of IScanFileReader for a file on a filesystem."""

    def __init__(self, fileName: Path):
        self.__fileName = fileName
        self.__file = None
        self.name = self.__fileName.name

    def __repr__(self):
        return str(self.__fileName.name)

    def open(self):
        if self.__file is not None:
            logging.warning("file is already open %s", cDim(self.__fileName.as_posix()))
            return
        self.__file = open(self.__fileName, "rb")

    def close(self):
        if self.__file is None:
            logging.warning("file is already closed %s", cDim(self.__fileName.as_posix()))
            return
        self.__file.close()
        self.__file = None

    def size(self):
        return self.__fileName.stat().st_size

    def read(self, size: int):
        return self.__file.read(size)

    def as_posix(self):
        return self.__fileName.as_posix()

    def rename(self, destFile: Path):
        self.__fileName.rename(destFile)

    def unlink(self):
        self.__fileName.unlink()

class ScanFile:
    """
    ScanFile represents a found file on the filesystem.
    On init the given file is read to calculate file size, CRC, SHA1 and MD5.
    If the given file coudn't be read an exception is raised."""

    def __init__(self, fileName: IScanFileReader):
        self.fileName = fileName
        self.isLoaded = False
        logging.debug("load file %s into memory", cDim(self.fileName.as_posix()))
        try:
            fileName.open()
            self.size = fileName.size()
            fileLoaded = 0
            rawMD5 = hashlib.md5()
            rawSHA1 = hashlib.sha1()
            rawCRC = 0
            while True:
                fileData = fileName.read(1024*1024)
                if len(fileData) == 0:
                    break
                fileLoaded += len(fileData)
                rawMD5.update(fileData)
                rawSHA1.update(fileData)
                rawCRC = binascii.crc32(fileData, rawCRC)

            logging.debug("file %s bytes loaded %s", cDim(self.fileName.as_posix()), self.size)
            self.crc = format(rawCRC & 0xffffffff, "0>8x")
            self.md5 = rawMD5.hexdigest()
            self.sha1 = rawSHA1.hexdigest()

            if self.size != fileLoaded:
                logging.error("file %s file size %s does not match file system size %s",
                    cDim(self.fileName.as_posix()), cDim(self.size), cDim(fileLoaded))
            else:
                self.isLoaded = True
                logging.info("scan file %s", cDim(str(vars(self))))
        except OSError as error:
            logging.error("open file %s caused an error %s",
                cDim(self.fileName.as_posix()), cDim(error))
        else:
            fileName.close()
