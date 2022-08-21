import pytest
from tosecdat import InvalidTosecFileException, TosecGameEntry, TosecGameRom, TosecHeader
from unittest import mock
from test_strategydiag import createHelloWorld
import xml.etree.ElementTree

def createElementWithText(tag: str, text: str) -> xml.etree.ElementTree.Element:
    t = xml.etree.ElementTree.Element(tag)
    t.text = text
    return t

def createDummyTOSEC(name: str = "Dummy - Games") -> xml.etree.ElementTree:
    tosec = xml.etree.ElementTree.Element("datafile")
    tosec.append(xml.etree.ElementTree.Element("header"));

    header = tosec.find("header")
    if name != None:
        header.append(createElementWithText("name", name))
    header.append(createElementWithText("category", "TOSEC"))
    header.append(createElementWithText("version", "DUMMY"))
    header.append(createElementWithText("author", "smesgr9000"))
    header.append(createElementWithText("email", "email@email.email"))
    header.append(createElementWithText("homepage", "tosecMover"))
    header.append(createElementWithText("url", "https://github.com/smesgr9000/tosecMover"))
    
    tree = xml.etree.ElementTree.ElementTree(tosec)
    return tree

def createDummyTOSECRom() -> xml.etree.ElementTree.Element:
    hw = createHelloWorld()
 
    rom = xml.etree.ElementTree.Element("rom")
    rom.attrib["name"] = str(hw.fileName)
    rom.attrib["crc"] = hw.crc
    rom.attrib["md5"] = hw.md5
    rom.attrib["sha1"] = hw.sha1
    rom.attrib["size"] = str(hw.size)
    return rom

def createDummyTOSECGame(roms: list[TosecGameRom] = [createDummyTOSECRom()]) -> xml.etree.ElementTree.Element:
    game = xml.etree.ElementTree.Element("game")
    game.attrib["name"] = "DummyGame"
    game.append(createElementWithText("description", "DummyGame"))
    for rom in roms:
        game.append(rom) 
    return game

def test_doTosecHeader():
    """
    Test a valid header is parsed with initialised field"""

    th = TosecHeader(createDummyTOSEC())

    assert len(th.games) == 0
    assert len(th.roms) == 0
    assert th.name == "Dummy - Games"
    assert th.system == "Dummy"
    assert th.category == "Games"

def test_doTosecHeaderNoCategory():
    """
    Test a valid header is parsed with initialised field"""

    name = "Dummy"
    th = TosecHeader(createDummyTOSEC(name))

    assert len(th.games) == 0
    assert len(th.roms) == 0
    assert th.name == name
    assert th.system == name
    assert th.category == None

def test_doTosecHeaderNoHeader():
    """
    Test if no header is present an exception is thrown"""

    dummy = createDummyTOSEC()
    dummy.getroot().clear()
    with pytest.raises(InvalidTosecFileException):
        TosecHeader(dummy)

def test_doTosecHeaderNoName():
    """
    Test if no name tag is present an exception is thrown"""

    dummy = createDummyTOSEC(None)
    with pytest.raises(InvalidTosecFileException):
        TosecHeader(dummy)

def test_doTosecGameEntry():
    """
    Test a valid game entry is parsed with initialised field"""

    test = createDummyTOSECGame()
    tge = TosecGameEntry(test, mock.Mock())

    assert len(tge.roms) == 1
    assert tge.name == "DummyGame"

def test_doTosecGameEntryMultipleRoms():
    """
    Test a valid game entry is parsed with initialised field"""

    test = createDummyTOSECGame([createDummyTOSECRom(), createDummyTOSECRom(), createDummyTOSECRom()])
    tge = TosecGameEntry(test, mock.Mock())

    assert len(tge.roms) == 3
    assert tge.name == "DummyGame"
    
def test_doTosecGameEntryNoName():
    """
    Test if no name attribute is present an exception is thrown"""

    test = createDummyTOSECGame()
    test.attrib["name"] = None

    with pytest.raises(InvalidTosecFileException):
        TosecGameEntry(test, mock.Mock())

def test_doTosecGameEntryNoRoms():
    """
    Test if no name attribute is present an exception is thrown"""

    test = createDummyTOSECGame([])

    with pytest.raises(InvalidTosecFileException):
        TosecGameEntry(test, mock.Mock())

