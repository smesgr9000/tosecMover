#!/usr/bin/python

from pathlib import Path
from scanfile import ScanFile
from tosecdat import TosecGameRom

class Strategy:
    """
    Abstract Strategy. Main logic of the program to react to hooks while
    scaning the directory structure. Several Stragegies can be chained. The strategies
    are executed in order."""

    def __init__(self):
        self.chain = None

    def doStrategyMatch(self, scanFile: ScanFile, tosecRomMatches: list[TosecGameRom]) -> Path:
        """ 
        Scan found matching TOSEC entries
        @param scanFile
            the file was scaned and caused the match
        @tosecRomMatches
            the ROM entries matching the scaned file criteria
        @return
            the found match in target directory or None on error"""

        if self.chain is not None:
            return self.chain.doStrategyMatch(scanFile, tosecRomMatches)
        return None

    def doStrategyNoMatch(self, scanFile: ScanFile):
        """
        Scan found a non-matching file
        @param scanFile
            the file was scaned and caused this miss"""

        if self.chain is not None:
            self.chain.doStrategyNoMatch(scanFile)
    
    def doFinal(self):
        """
        Scan has ended"""

        if self.chain is not None:
            self.chain.doFinal()

    def doChain(self, chain):
        """
        Chain another Strategy to this Strategy
        @param
            the strategy to chain and is executed after this strategy on every hook
        @return
            the given strategy"""

        chain.chain = self
        return chain
