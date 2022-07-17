#!/usr/bin/python

from pathlib import Path
from color import *
from scanfile import *
from strategy import Strategy
from strategydiag import StrategyDiag
from strategyrename import StrategyRename, Matcher
from tosecdat import *
import argparse
import logging
import xml.etree.ElementTree

class Tosec:
    """
    Tosec scanner. On init read all TOSEC DATs found in the given directory
    or the single file.
    The class will scan the given directores and either rename or diagnosis 
    the result depending on the given arguments."""

    def __init__(self, tosecDir: str):
        logging.debug("Init TOSEC DAT path %s", cDim(tosecDir))
        tosecPath = Path(tosecDir).resolve()
        if not tosecPath.exists():
            logging.error("TOSEC DAT path %s does not exists", cDim(tosecPath))
            return
        if not tosecPath.is_dir():
            romList = self.__readTosecFile(tosecPath)
        else:
            romList = dict()
            for tosecEntry in tosecPath.iterdir():
                if not tosecEntry.is_dir():
                    newRomList = self.__readTosecFile(tosecEntry)
                    for entryKey in newRomList.keys():
                        rom = newRomList[entryKey]
                        rom0 = rom[0]
                        if entryKey in romList:
                            existingEntry = romList[entryKey][0]
                            logging.info("TOSEC file %s with same sha1 %s and matching {md5=%s size=%s} already found in other TOSEC file %s", cDim(existingEntry.game.header.name + "/" + existingEntry.name), cDim(entryKey), existingEntry.md5 == rom0.md5, existingEntry.size == rom0.size, cDim(rom0.game.header.name + "/" + rom0.name));
                            if existingEntry.md5 == rom0.md5 and existingEntry.size == rom0.size and existingEntry.crc == rom0.crc:
                                romList[entryKey].extend(rom)
                        else:
                            romList[entryKey] = rom
        self.__matcher = Matcher(romList)

    def __readTosecFile(self, tosecFile: Path) -> dict:
        """
        Reads a single TOSEC DAT file. Returns a dictonary of all ROM entries
        of the DAT file. If a ROM is found several times in the DAT the complete 
        game entry is skipped."""

        root = xml.etree.ElementTree.parse(tosecFile.as_posix()).getroot()
        romList = dict()
        gameList = []
        try:
            header = TosecHeader(root)
            for game in root.findall("game"):
                try:
                    entry = TosecGameEntry(game, header);
                    gameRomList = dict()
                    for rom in entry.roms:
                        if rom.sha1 in romList:
                            raise InvalidTosecFileException("ROM with sha1 {} was already added".format(cDim(rom.sha1)))
                        gameRomList[rom.sha1] = [rom]
                    gameList.append(entry)
                    romList.update(gameRomList)
                except InvalidTosecFileException as exception:
                    logging.warning("TOSEC DAT file %s parser error. Entry skipped because: %s", cDim(tosecFile.as_posix()), exception)
            logging.info("TOSEC DAT file %s loaded %s entries with %s roms", cDim(tosecFile.as_posix()), len(gameList), len(romList))
            header.games = gameList
            header.roms = romList
        except InvalidTosecFileException as exception:
            logging.warning("TOSEC DAT file %s parser error. File skipped because: %s", cDim(tosecFile.as_posix()), exception)
        return romList

    def __scanFile(self, entry: Path, strategy: Strategy):
        scan = ScanFile(entry)
        match = self.__matcher.findMatch(scan)
        if match is None:
            strategy.doStrategyNoMatch(scan)
        else:
            strategy.doStrategyMatch(scan, match)
    
    def __scanDirectory(self, listPath: list[Path], strategy: Strategy) -> list[Path]:
        foundDirectories = []
        for scanPath in listPath:
            if scanPath.is_dir() and not scanPath.is_symlink():
                for entry in scanPath.iterdir():
                    if entry.is_file():
                        self.__scanFile(entry, strategy)
                    elif not scanPath.is_symlink():
                        logging.debug("add directory %s to list to scan", cDim(entry.as_posix()))
                        foundDirectories.append(entry)
            elif scanPath.is_file():
                self.__scanFile(scanPath, strategy)
        return foundDirectories
    
    def scanDirectory(self, args: argparse.Namespace):
        if args.source is not None:
            scanPath = Path(args.source).resolve()
            destPath = Path(args.dest).resolve()
            if not destPath.exists():
                logging.error("destination directory %s does not exists", cDim(args.dest))
                return
            if not destPath.is_dir():
                logging.error("destination %s is not a directory", cDim(args.destDir))
                return
            strategy = StrategyRename(destPath, self.__matcher, args.delDupes)
            if args.diag:
                strategy = strategy.doChain(StrategyDiag(args.noMissing, args.noHaving))
        else:
            scanPath = Path(args.dest).resolve()
            strategy = StrategyDiag(args.noMissing, args.noHaving)
        if not scanPath.exists():
            logging.error("directory %s to scan does not exsits", cDim(scanPath.as_posix()))
            return
        try:
            scanPaths = [scanPath]
            while len(scanPaths) > 0:
                scanPaths = self.__scanDirectory(scanPaths, strategy)
        finally:
            strategy.doFinal()

parser = argparse.ArgumentParser()
parser.add_argument("--loglevel", choices=["error", "warning", "info", "debug"], default="warning", help="Loglevel for the programm")
parser.add_argument("--delDupes", action="store_true", help="Delete duplicates found in source directory")
parser.add_argument("--diag", action="store_true", help="Also print diagnostic information when scanning source directory. This is always enabled if source is not given")
parser.add_argument("--noHaving", action="store_true", help="If in diagnostic mode don't print 'Having' files")
parser.add_argument("--noMissing", action="store_true", help="If in diagnostic mode don't print 'Missing' files")
parser.add_argument("tosec", help="filename of TOSEC DAT file or directory to process")
parser.add_argument("--source", help="source file or directory to scan")
parser.add_argument("dest", help="destination directory to move found files. If no source is given the directory is scaned without moving")

args = parser.parse_args()

logging.basicConfig(level=args.loglevel.upper())
t = Tosec(args.tosec)
t.scanDirectory(args)
