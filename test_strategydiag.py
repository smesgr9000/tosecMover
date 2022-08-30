import pytest
from pathlib import Path
from scanfile import PlainFileReader, ScanFile
from strategy import Strategy
from strategydiag import StrategyDiag
from tosecdat import TosecGameRom
from unittest import mock

def createHelloWorld() -> ScanFile:
    m = mock.Mock()
    # For 'HelloWorld'
    m.fileName = PlainFileReader(Path("HelloWorld.txt"))
    m.size = 10
    m.isLoaded = True
    m.crc = "77770c79"
    m.sha1 = "db8ac1c259eb89d4a131b253bacfca5f319d54f2"
    m.md5 = "68e109f0f40ca72a15e05cc22786f8e6"
    return m

def createGameRomFromScanFile(sf: ScanFile) -> TosecGameRom:
    m = mock.Mock()
    m.name = sf.fileName.name
    m.size = sf.size
    m.crc = sf.crc
    m.sha1 = sf.sha1
    m.md5 = sf.md5
    return m

def createSimpleFoundMatchStrategy() -> Strategy:
    m = mock.Mock()
    sf = mock.Mock()
    sf.fileName = PlainFileReader(Path("dummyPath/MockFile.txt"))
    m.doStrategyMatch = mock.MagicMock(return_value = sf)
    return m

def test_doStrategyNoMatch():
    """
    Test StrategyDiag.doStrategyNoMatch will store a no matched ScanFile as BAD"""

    sd = StrategyDiag(False, False)
    mock = createHelloWorld()
    sd.doStrategyNoMatch(mock)
    assert len(sd.goodBySystem) == 0
    assert len(sd.dups) == 0
    assert len(sd.bads) == 1
    assert sd.bads[0] == [mock.fileName, None]

@mock.patch('builtins.print') 
def test_doFinalWithNoMatch(mockPrint):
    """
    Test StrategyDiag.doFinal with a no match found 
    will print UNKNOWN with file name"""

    sd = StrategyDiag(False, False)
    mock = createHelloWorld()
    sd.doStrategyNoMatch(mock)
    sd.doFinal()
    
    assert mockPrint.call_count == 3
    assert mockPrint.call_args_list[1].contain("UNKNOWN")
    assert mockPrint.call_args_list[2].contain(mock.fileName.as_posix())

def test_doStrategyMatchGood():
    """
    Test StrategyDiag.doStrategyMatch will store a matched ScanFile as GOOD"""
    
    sd = StrategyDiag(False, False)
    mockGood = createHelloWorld()
    mockGameRom = createGameRomFromScanFile(mockGood)
    sd.doStrategyMatch(mockGood, [mockGameRom])
    assert len(sd.bads) == 0
    assert len(sd.dups) == 0
    assert len(sd.goodBySystem) == 1
    assert sd.goodBySystem.get(mockGameRom.game.header) == { mockGameRom: mockGood.fileName }

def test_doStrategyMatchGoodOnRenameScan():
    """
    Test StrategyDiag.doStrategyMatch will store a matched ScanFile as GOOD
    even if the file is freshly renamed by StrategyRename"""
    
    sd = StrategyDiag(False, False)
    sd.chain = createSimpleFoundMatchStrategy()
    mockSource = createHelloWorld()
    mockGameRom = createGameRomFromScanFile(mockSource)
    mockGameRom.name = "MockFile.txt"
    sd.doStrategyMatch(mockSource, [mockGameRom])
    assert len(sd.bads) == 0
    assert len(sd.dups) == 0
    assert len(sd.goodBySystem) == 1
    assert sd.goodBySystem.get(mockGameRom.game.header) == { mockGameRom: sd.chain.doStrategyMatch().fileName }

def test_doStrategyMatchDuplicate():
    """
    Test StrategyDiag.doStrategyMatch will store two matched ScanFiles
    with the same file one as GOOD one as DUPLICATE"""

    sd = StrategyDiag(False, False)
    mockGood = createHelloWorld()
    mockGameRom = createGameRomFromScanFile(mockGood)
    mockDups = createHelloWorld()
    sd.doStrategyMatch(mockGood, [mockGameRom])
    sd.doStrategyMatch(createHelloWorld(), [mockGameRom])
    assert len(sd.bads) == 0
    assert len(sd.dups) == 1
    assert len(sd.goodBySystem) == 1
    assert sd.dups.get(mockGameRom)[0].as_posix() == mockDups.fileName.as_posix()
    assert sd.goodBySystem.get(mockGameRom.game.header) == { mockGameRom: mockGood.fileName }
