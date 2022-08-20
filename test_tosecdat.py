import pytest
from tosecdat import InvalidTosecFileException, TosecHeader
from unittest import mock
import xml.etree.ElementTree

def createElementWithText(tag: str, text: str) -> xml.etree.ElementTree.Element:
    t = xml.etree.ElementTree.Element(tag)
    t.text = text
    return t

def createDummyTOSEC(name: str = 'Dummy - Games') -> xml.etree.ElementTree:
    tosec = xml.etree.ElementTree.Element('datafile')
    tosec.append(xml.etree.ElementTree.Element('header'));

    header = tosec.find('header')
    if name != None:
        header.append(createElementWithText('name', name))
    header.append(createElementWithText('category', 'TOSEC'))
    header.append(createElementWithText('version', 'DUMMY'))
    header.append(createElementWithText('author', 'smesgr9000'))
    header.append(createElementWithText('email', 'email@email.email'))
    header.append(createElementWithText('homepage', 'tosecMover'))
    header.append(createElementWithText('url', 'https://github.com/smesgr9000/tosecMover'))
    
    tree = xml.etree.ElementTree.ElementTree(tosec)
    return tree
    

def test_doTosecHeader():
    '''
    Test a valid header is parsed with initialised field'''

    th = TosecHeader(createDummyTOSEC())

    assert len(th.games) == 0
    assert len(th.roms) == 0
    assert th.name == 'Dummy - Games'
    assert th.system == 'Dummy'
    assert th.category == 'Games'

def test_doTosecHeaderNoCategory():
    '''
    Test a valid header is parsed with initialised field'''

    name = 'Dummy'
    th = TosecHeader(createDummyTOSEC(name))

    assert len(th.games) == 0
    assert len(th.roms) == 0
    assert th.name == name
    assert th.system == name
    assert th.category == None

def test_doTosecHeaderNoHeader():
    '''
    Test if no header is present an exception is thrown'''

    dummy = createDummyTOSEC()
    dummy.getroot().clear()
    with pytest.raises(InvalidTosecFileException):
        TosecHeader(dummy)

def test_doTosecHeaderNoName():
    '''
    Test if no name tag is present an exception is thrown'''

    dummy = createDummyTOSEC(None)
    with pytest.raises(InvalidTosecFileException):
        TosecHeader(dummy)

