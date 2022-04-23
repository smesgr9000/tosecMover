#!/usr/bin/python

from color import *
from pathlib import Path
import binascii
import hashlib
import logging

class ScanFile:
    """
    ScanFile represents a found file on the filesystem. 
    On init the given path is read to calculate file size, CRC, SHA1 and MD5.
    If file coudn't be read an exception is raised """

    def __init__(self, fileName: Path):
        self.fileName = fileName
        self.isLoaded = False
        logging.debug("Load file %s into memory", cDim(self.fileName.as_posix()))
        try:
            file = open(fileName, "rb")
            self.size = fileName.stat().st_size
            fileLoaded = 0
            rawMD5 = hashlib.md5();
            rawSHA1 = hashlib.sha1()
            rawCRC = 0
            while True:
                fileData = file.read(1024*1024)
                if len(fileData) == 0:
                    break
                fileLoaded += len(fileData)
                rawMD5.update(fileData)
                rawSHA1.update(fileData)
                rawCRC = binascii.crc32(fileData, rawCRC)
                
            logging.debug("File %s bytes loaded %s", cDim(self.fileName.as_posix()), self.size)
            self.crc = format(rawCRC & 0xffffffff, "0>8x")
            self.md5 = rawMD5.hexdigest()
            self.sha1 = rawSHA1.hexdigest()
            
            if self.size != fileLoaded:
                logging.error("File %s file size %s does not match file system size %s", cDim(self.fileName.as_posix()), cDim(self.size), cDim(fileLoaded))
            else:
                self.isLoaded = True
                logging.info("Scan file %s", cDim(str(self)))
        except OSError as error:
            logging.error("Open file %s caused an error %s", cDim(self.fileName.as_posix()), cDim(error))
        else:
            file.close()
