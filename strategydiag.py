#!/usr/bin/python

from color import *
from pathlib import Path
from scanfile import ScanFile
from strategy import Strategy
from tosecdat import TosecGameRom
import logging

class StrategyDiag(Strategy):
    """
    Strategy to diagnosis of the given directories.
    Count all game ROMs for following criteria:
    - Missing: ROMs not found but at least another ROM entry was found
    - Having: ROMs found
    - Duplicates: ROMs found but entry was already found before
    - Unknown: Either
            files not matching any TOSEC entry OR
            file has not the expected name for the TOSEC entry"""

    def __init__(self, noMissing: bool, noHaving: bool):
        super().__init__()
        self.goodBySystem = dict()
        self.dups = dict()
        self.bads = []
        self.__noMissing = noMissing
        self.__noHaving = noHaving
    
    def doStrategyMatch(self, scanFile: ScanFile, tosecRoms: list[TosecGameRom]) -> Path:
        found = super().doStrategyMatch(scanFile, tosecRoms) or scanFile.fileName
        logging.debug("diag file %s", cDim(found.name))
        foundRoms = [entry for entry in tosecRoms if found.name == entry.name]
        if len(foundRoms) > 0:
            for rom in foundRoms:
                if rom in self.goodBySystem.get(rom.game.header, dict()):
                    self.dups.setdefault(rom, []).append(found)
                else:
                    self.goodBySystem.setdefault(rom.game.header, dict()).setdefault(rom, found)
            return found
        else:
            logging.debug("found file %s not matching any TOSEC name with %s", cDim(found.name), cDim(tosecRoms[0].sha1))
            self.bads.append([found, tosecRoms[0]])
        return None

    def doStrategyNoMatch(self, scanFile: ScanFile):
        super().doStrategyNoMatch(scanFile)
        self.bads.append([scanFile.fileName, None])

    def doFinal(self):
        super().doFinal()
        for bad in list(self.bads):
            if bad[1] is not None and self.goodBySystem.get(bad[1].game.header, dict()).get(bad[1]) is not None:
                self.dups.setdefault(bad[1], []).append(bad[0])
                self.bads.remove(bad)
        for good in self.goodBySystem.keys():
            having = self.goodBySystem[good].keys();
            print()
            print(f"found {len(having)}/{len(good.roms)} of {cDim(good.name)}")
            missing = dict(good.roms)
            for rom in having:
                missing.pop(rom.sha1, None)
            if len(missing) > 0 and not self.__noMissing:
                print(cRed("Missing"))
                miss = lambda x: "{} - {}".format(x.name, x.sha1)
                self.__printInOrder(miss, self.__flat(missing))
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
                print(cDim(self.goodBySystem[key.game.header][key].as_posix()))
        if len(self.bads) > 0:
            print(cYellow("Unknown"))
            bad = lambda x: cDim(x[0].as_posix()) if x[1] is None else f"{cDim(x[0].as_posix())} should be {cDim(x[1].name)}"
            self.__printInOrder(bad, self.bads)

    def __flat(self, y: dict):
        flat = []
        for values in y.values():
            for entry in values:
                flat.append(entry)
        return flat

    def __printInOrder(self, func, y: list):
        ordered = list(map(func, y))
        ordered.sort()
        for order in ordered:
            print(order)
