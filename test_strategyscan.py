#!/usr/bin/python

import pytest
from pathlib import Path
from strategyrename import Matcher
from strategyscan import StrategyScan
from unittest import mock

def createMockMatcher(val: bool) -> Matcher:
    m = mock.Mock()
    m.findMatch = mock.MagicMock(return_value = 'any' if val else None)
    return m

def createMockDirWithEntry(entry: list[Path]) -> Path:
    m = mock.Mock()
    m.is_dir = mock.MagicMock(return_value = True)
    m.is_file = mock.MagicMock(return_value = False)
    m.is_symlink = mock.MagicMock(return_value = False)
    m.iterdir = mock.MagicMock(return_value = entry)
    m.as_posix = mock.MagicMock(return_value = 'DirWithEntry')
    return m

def createMockFile() -> Path:
    m = mock.Mock()
    m.is_dir = mock.MagicMock(return_value = False)
    m.is_file = mock.MagicMock(return_value = True)
    m.as_posix = mock.MagicMock(return_value = 'MockFile')
    stat = mock.Mock()
    stat.st_size = 4
    m.stat = mock.MagicMock(return_value = stat)
    return m

def mockOtherStrategis(toPatch: StrategyScan) -> StrategyScan:
    toPatch.doStrategyNoMatch = mock.MagicMock()
    toPatch.doStrategyMatch = mock.MagicMock()
    return toPatch
    

def test_doStrategyScanEmptyDirectory():
    """
    Test StrategyScan.doStrategyScan with empty directory
    will not call Matcher and return empty array"""

    matcher = createMockMatcher(False)
    mockDir = createMockDirWithEntry([])
    ss = mockOtherStrategis(StrategyScan(matcher))

    ret = ss.doStrategyScan([mockDir])

    assert len(ret) == 0
    matcher.findMatch.assert_not_called()
    mockDir.iterdir.assert_called_once()
    ss.doStrategyNoMatch.assert_not_called()
    ss.doStrategyMatch.assert_not_called()

@mock.patch("builtins.open", mock.mock_open(read_data=b'test'))
def test_doStrategyScanSingleFileNegative():
    """
    Test StrategyScan.doStrategyScan with a single file in directory 
    will call Matcher and return empty array.
    Matcher will return false so doStrategyNoMatch is called"""

    matcher = createMockMatcher(False)
    mockDir = createMockDirWithEntry([createMockFile()])
    ss = mockOtherStrategis(StrategyScan(matcher))
    
    ret = ss.doStrategyScan([mockDir])

    assert len(ret) == 0
    matcher.findMatch.assert_called_once()
    mockDir.iterdir.assert_called_once()
    ss.doStrategyNoMatch.assert_called_once()
    ss.doStrategyMatch.assert_not_called()

@mock.patch("builtins.open", mock.mock_open(read_data=b'test'))
def test_doStrategyScanSingleFilePositive():
    """
    Test StrategyScan.doStrategyScan with a single file in directory 
    will call Matcher and return empty array.
    Matcher will return true so doStrategyMatch is called"""

    matcher = createMockMatcher(True)
    mockDir = createMockDirWithEntry([createMockFile()])
    ss = mockOtherStrategis(StrategyScan(matcher))
    
    ret = ss.doStrategyScan([mockDir])

    assert len(ret) == 0
    matcher.findMatch.assert_called_once()
    mockDir.iterdir.assert_called_once()
    ss.doStrategyNoMatch.assert_not_called()
    ss.doStrategyMatch.assert_called_once()

def test_doStrategyScanSingleDirectory():
    """
    Test StrategyScan.doStrategyScan with a single directory in directory 
    will not call Matcher and return empty directory."""

    matcher = createMockMatcher(True)
    subDir = [createMockDirWithEntry([])];
    mockDir = createMockDirWithEntry(subDir)
    ss = mockOtherStrategis(StrategyScan(matcher))
    
    ret = ss.doStrategyScan([mockDir])

    assert len(ret) == 1
    assert ret == subDir
    matcher.findMatch.assert_not_called()
    mockDir.iterdir.assert_called_once()
    ss.doStrategyNoMatch.assert_not_called()
    ss.doStrategyMatch.assert_not_called()
