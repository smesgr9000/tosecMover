#!/usr/bin/python

from pathlib import Path
from color import *
from strategydiag import StrategyDiag
from strategyrename import StrategyRename, Matcher
from strategyscan import StrategyScan
from strategyscancompressed import StrategyScanCompressed
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
            romList = {}
            for tosecEntry in tosecPath.iterdir():
                if not tosecEntry.is_dir():
                    newRomList = self.__readTosecFile(tosecEntry)
                    self.__joinRomLists(romList, newRomList)
        self.__matcher = Matcher(romList)

    def __readTosecFile(self, tosecFile: Path) -> dict:
        """
        Reads a single TOSEC DAT file. Returns a dictonary of all ROM entries
        of the DAT file. If a ROM is found several times in the DAT the complete
        game entry is skipped."""

        fileRomList = {}
        try:
            root = xml.etree.ElementTree.parse(tosecFile.as_posix()).getroot()
            gameList = []
            header = TosecHeader(root)
            for game in root.findall("game"):
                try:
                    entry = TosecGameEntry(game, header)
                    gameRomList = self.__createGameEntryRomList(entry, fileRomList)
                    gameList.append(entry)
                    self.__joinRomLists(fileRomList, gameRomList)
                except InvalidTosecFileException as exception:
                    logging.warning("TOSEC DAT file %s parser error. Entry skipped because: %s",
                        cDim(tosecFile.as_posix()), exception)
            logging.info("TOSEC DAT file %s loaded %s entries with %s roms",
                cDim(tosecFile.as_posix()), len(gameList), len(fileRomList))
            header.games = gameList
            header.roms = fileRomList
        except (InvalidTosecFileException, xml.etree.ElementTree.ParseError) as exception:
            logging.warning("TOSEC DAT file %s parser error. File skipped because: %s",
                cDim(tosecFile.as_posix()), exception)
        return fileRomList

    def __createGameEntryRomList(self, entry: TosecGameEntry, romList: dict) -> dict:
        """
        Reads a single TOSEC DAT game entry ROM files.
        It will check the given SHA1 dictonary if any ROM file is already
        in the database. Will throw an exception if all ROMs of at least another game entries is identical
        Otherwise a dict of sha1 ROMs is returned."""

        dups = {}
        gameRomList = {}
        for rom in entry.roms:
            if rom.sha1 in romList:
                for gameEntry in romList[rom.sha1]:
                    game = gameEntry.game
                    dups[game] = dups.get(game, 0) + 1
            gameRomList[rom.sha1] = [rom]

        if len(dups) > 0:
            for game, duplicateRoms in dict(dups).items():
                if len(game.roms) != duplicateRoms or duplicateRoms != len(gameRomList):
                    dups.pop(game)
            if len(dups) > 0:
                sha1s = ', '.join(str(rom.sha1) for rom in entry.roms)
                games = ', '.join(str(dup.name) for dup in dups.keys())
                logging.debug("All Game ROMs %s of with sha1 %s were already added in other game %s",
                    cDim(entry.name), cDim(sha1s), cDim(games))
                raise InvalidTosecFileException("All Game ROMs {} were already added in other game {}".format(cDim(entry.name), cDim(games)))
        return gameRomList

    def __joinRomLists(self, romList: dict, concatList: dict):
        """
        Joins two dictonaries together by adding entres for concatList into romList.
        Will skip all files with matching sha1, but different values for md5, size or crc
        If a ROM sha1 occurs in several roms entries the returned rom list will contain all."""

        for entryKey, rom in concatList.items():
            rom0 = rom[0]
            if entryKey in romList:
                existingEntry = romList[entryKey][0]
                logging.info("TOSEC file %s with same sha1 %s and matching {md5=%s size=%s} already found in other TOSEC file %s",
                    cDim(existingEntry.game.header.name + "/" + existingEntry.name),
                    cDim(entryKey),
                    existingEntry.md5 == rom0.md5,
                    existingEntry.size == rom0.size,
                    cDim(rom0.game.header.name + "/" + rom0.name))
                if existingEntry.md5 == rom0.md5 and existingEntry.size == rom0.size and existingEntry.crc == rom0.crc:
                    romList[entryKey].extend(rom)
            else:
                romList[entryKey] = rom

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
            strategy = StrategyRename(destPath, self.__matcher, args.delDupes, args.noWritePermission)
            if args.diag:
                strategy = strategy.doChain(StrategyDiag(args.noMissing, args.noHaving))
        else:
            scanPath = Path(args.dest).resolve()
            strategy = StrategyDiag(args.noMissing, args.noHaving)
        if args.scanCompressed:
            strategy = strategy.doChain(StrategyScanCompressed(self.__matcher))
        else:
            strategy = strategy.doChain(StrategyScan(self.__matcher))
        if not scanPath.exists():
            logging.error("directory %s to scan does not exsits", cDim(scanPath.as_posix()))
            return
        try:
            scanPaths = [scanPath]
            while True:
                startPaths = scanPaths
                scanPaths = strategy.doStrategyScan(scanPaths)
                if not args.recursive or len(scanPaths) <= 0 or startPaths == scanPaths:
                    break
        finally:
            strategy.doFinal()

parser = argparse.ArgumentParser()
parser.add_argument("--loglevel", choices=["error", "warning", "info", "debug"], default="warning", help="Loglevel for the programm. debug - very verbose. error - only important messages")
parser.add_argument("--delDupes", action="store_true", help="Delete duplicates found in source directory")
parser.add_argument("--diag", action="store_true", help="Also print diagnostic information when scanning source directory. This is always enabled if source is not given")
parser.add_argument("--noHaving", action="store_true", help="If in diagnostic mode don't print 'Having' files")
parser.add_argument("--noMissing", action="store_true", help="If in diagnostic mode don't print 'Missing' files")
parser.add_argument("--noWritePermission", action="store_true", help="remove write permission on a renamed file")
parser.add_argument("tosec", help="filename of TOSEC DAT file or directory to process")
parser.add_argument("--source", help="source file or directory to scan")
parser.add_argument("-r", action="store_true", dest="recursive", help="source directory is scaned recursively")
parser.add_argument("-x", action="store_true", dest="scanCompressed", help="compressed files in source directory is scaned. Supported file formats is ZIP. **Experimental** file is not only extracted but not moved")
parser.add_argument("dest", help="destination directory to move found files. If no source is given the directory is scaned without moving")

args = parser.parse_args()

logging.basicConfig(level=args.loglevel.upper())
t = Tosec(args.tosec)
t.scanDirectory(args)
