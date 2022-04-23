TosecMover
==========

TosecMover is a TOSEC Dat parser and file mover. It is a simple tool to:
- scan files
- detect matching to a given TOSEC dat file or directories of Dat files
- move & rename the matched files into a destination folder structure

You properly want a more suffisticated tool like [JRomManger](https://github.com/optyfr/JRomManager).
The benefit of this it runs from the shell without ui.

The current fixed destination structure is determened
by the name tag of the Tosec Dat file e.g. `Acorn BBC - Games - \[ADL\]`
will create:

```
Acorn BBC/Games - \[ADL\]/Game/Soccer Challenge (19xx)(Discovery)\[h 8-Bit\]\[ADFS\].adl
```

Currently the tool does **NOT** support:
- DAT entries with more than one file per entry
- not multithreaded
- diagnostic could be improved
- more flexible destination
- compression/decompression

Running
-------

For flags and shell command arguments and options excute in the directory:

```
python3 tosecMover.py --help
```

License
-------

Under BSD-3clause see [LICENSE]

