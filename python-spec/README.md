# `somacore`: the Python version of the SOMA specification

`somacore` is the Python interpretation of the [abstract SOMA specification](https://github.com/single-cell-data/SOMA/blob/main/abstract_specification.md).
If you’re using SOMA to store or retrive data, you probably want to **install a SOMA implementation instead**, and not this package directly:

- [tiledbsoma](https://pypi.org/project/tiledbsoma/) ([source code](https://github.com/single-cell-data/TileDB-SOMA/))

This core pacakge contains base interfaces, shared types, and other cross-implementation code.
It is intended for use primarily by SOMA implementors or libraries that handle SOMA data, rather than end users.
