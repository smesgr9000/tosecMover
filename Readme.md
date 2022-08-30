TosecMover
==========

TosecMover is a TOSEC Dat parser and file mover. It is a simple tool to:
- scan files
- detect matching to a given TOSEC dat file or directories of Dat files
- move & rename the matched files into a destination folder structure

You properly want a more suffisticated tool like [JRomManger](https://github.com/optyfr/JRomManager).
The benefit of this it runs from the shell without ui.

The current fixed destination structure is determened
by the name tag of the Tosec Dat file e.g. `Acorn BBC - Games - [ADL]`
will create:

```
Acorn BBC/Games - [ADL]/<game name>
```

If a game contains multiple files or ROMs the structure is:

```
Acorn BBC/Games - [ADL]/<game name>/<rom name>
```

Currently the tool does **NOT** support:
- not multithreaded
- diagnostic could be improved
- more flexible destination
- compression/decompression for target files
- files in ZIP archives can be scaned, but only extracted not moved

Running
-------

For flags and shell command arguments and options excute in the directory:

```
python3 tosecMover.py --help
```

Running Tests
-------------

Unit tests are written to be used by pytest. Running all tests can be done
by following command:

```
pytest
```

License
-------

Under BSD-3clause see [LICENSE](./LICENSE)

