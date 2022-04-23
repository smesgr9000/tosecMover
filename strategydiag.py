#!/usr/bin/python

from color import *
from scanfile import ScanFile
from strategy import Strategy
from tosecdat import TosecGameEntry
import logging

class StrategyDiag(Strategy):
    """
    Strategy to diagnosis of the given directories.
    Count all found, missed and duplicate game entries.
    Also try to find game files without a game entry and 
    files with wrong name according to the game entry"""

    def __init__(self, noMissing: bool, noHaving: bool):
        super().__init__()
        self.goodBySystem = dict()
        self.dups = dict()
        self.bads = []
        self.__noMissing = noMissing;
        self.__noHaving = noHaving;
    
    def doStrategyMatch(self, scanFile: ScanFile, tosecEntry: list[TosecGameEntry]):
        super().doStrategyMatch(scanFile, tosecEntry)
        foundEntries = [entry for entry in tosecEntry if scanFile.fileName.name == entry.fileName]
        if len(foundEntries) > 0:
            for entry in foundEntries:
                if entry in self.goodBySystem.get(entry.header, dict()):
                    self.dups.setdefault(entry, []).append(scanFile.fileName)
                else:
                    self.goodBySystem.setdefault(entry.header, dict()).setdefault(entry, scanFile.fileName)
        else:
            logging.debug("Found file %s not matching any TOSEC name with %s", cDim(scanFile.fileName.name), cDim(tosecEntry[0].sha1))
            self.bads.append([scanFile.fileName, tosecEntry[0]])

    def doStrategyNoMatch(self, scanFile: ScanFile):
        super().doStrategyNoMatch(scanFile)
        self.bads.append([scanFile.fileName, None])

    def doFinal(self):
        super().doFinal()
        for bad in list(self.bads):
            if bad[1] is not None and self.goodBySystem.get(bad[1].header, dict()).get(bad[1]) is not None:
                self.dups.setdefault(bad[1], []).append(bad[0])
                self.bads.remove(bad)
        for good in self.goodBySystem.keys():
            having = self.goodBySystem[good].keys();
            print()
            print(f"Found {len(having)}/{len(good.games)} of {cDim(good.name)}")
            missing = dict(good.games)
            for game in having:
                missing.pop(game.sha1, None)
            if len(missing) > 0 and not self.__noMissing:
                print(cRed("Missing"))
                miss = lambda x: "{} - {}".format(missing[x].name, x)
                self.__printInOrder(miss, missing)
            if len(having) > 0 and not self.__noHaving:
                print(cGreen("Having"))
                have = lambda x: "{} - {}".format(x.name, x.sha1)
                self.__printInOrder(have, having)
        print()
        if len(self.dups) > 0:
            print(cYellow("Duplicates"))
            for key in self.dups.keys():
                print(key.name, end=": ")
                [print(cDim(dup.as_posix()), end=", ") for dup in self.dups[key]]
                print(cDim(self.goodBySystem[key.header][key].as_posix()))
        if len(self.bads) > 0:
            print(cYellow("Unknown"))
            bad = lambda x: cDim(x[0].as_posix()) if x[1] is None else f"{cDim(x[0].as_posix())} should be {cDim(x[1].name)}"
            self.__printInOrder(bad, self.bads)

    def __printInOrder(self, func, y: list):
        ordered = list(map(func, y))
        ordered.sort()
        for order in ordered:
            print(order)
