# SOMA

SOMA – for “Stack Of Matrices, Annotated” – is a flexible, extensible, and open-source API enabling access to data in a variety of formats. SOMA is designed to be general-purpose for data that can be modeled as one or more sets of 2D annotated matrices with measurements of features across observations.
The driver use case of SOMA is for single-cell data in the form of annotated matrices where observations are frequently cells and features are genes, proteins, or genomic regions.



## Motivation

Datasets generated by profiling single cells are rapidly increasing in size and complexity. This has resulted in a need for scalable solutions to accommodate data sizes that no longer fit in memory and flexibility to accommodate the diversity of data being produced. 

To address these emerging needs in the single cell ecosystem, CZI in partnership with TileDB is:


1. Driving the development of SOMA.
2. Providing its first implementation, [TileDB-SOMA](https://github.com/single-cell-data/TileDB-SOMA) which utilizes the [TileDB Embedded](https://github.com/TileDB-Inc/TileDB) engine.
3. Adopting TileDB-SOMA at [CZ CELLxGENE Discover](https://cellxgene.cziscience.com/) to build the [Cell Census](https://github.com/TileDB-Inc/TileDB) which provides efficient access and querying of its data from nearly 50 million cells, compiled from 700+ datasets.

The `SOMA` specification and its `TileDB-SOMA` implementation provides the following capabilities for single-cell data:

1. An abstract specification with flexibility for data from multiple modalities (e.g. RNA, spatial, epigenomics)
1. A format to store and access datasets larger than memory, as compared to the current paradigm of `.h5ad`/`.mtx`/`.tgz`/`.RData`/`h5Seurat `/ etc.
1. Eliminates in-memory limitations by providing query-ready data management for reading and writing at low latency and cloud scale. 
1. R and python APIs with the flexibility to expand to other future languages.


## Developer information

* [SOMA Abstract specification](https://github.com/single-cell-data/SOMA/blob/main/abstract_specification.md) — language-agnostic SOMA API specification.
* [Python SOMA specification](https://github.com/single-cell-data/SOMA/tree/main/python-spec) — persistence-layer agnostic python definition of SOMA core types. R coming soon.
* [TileDB-SOMA](https://github.com/single-cell-data/TileDB-SOMA) — implementation of Python SOMA specification using [TileDB Embedded](https://github.com/TileDB-Inc/TileDB). R coming soon.

## Coming soon!

* R SOMA specification and its implementation through TileDB-SOMA.
* End-user documentation for both Python and R TileDB-SOMA APIs , including a getting started guide, notebooks, and API reference.


 
## Issues and contacts

* We expect the TileDB-SOMA repository to be the front door for implementation issues [https://github.com/single-cell-data/TileDB-SOMA/issues](https://github.com/single-cell-data/TileDB-SOMA/issues). In addition, for spec-related issues please file a ticket at [https://github.com/single-cell-data/SOMA/issues](https://github.com/single-cell-data/SOMA/issues). 
* If you believe you have found a security issue, in lieu of filing an issue please responsibly disclose it by contacting [security@chanzuckerberg.com](mailto:security@chanzuckerberg.com).
* Feedback is appreciated, this is a community-driven project, if you have well-scoped features/discussions please add them to [https://github.com/single-cell-data/SOMA/issues](https://github.com/single-cell-data/SOMA/issues) for any other inquiries please reach out to [soma@chanzuckerberg.com](mailto:soma@chanzuckerberg.com).
* If you would like to learn more about SOMA or would like to keep up to date with the latest developments, please join our mailing list [here](https://bit.ly/soma-signup).


## Code of Conduct

This project adheres to CZI's Contributor Covenant [code of conduct](https://github.com/chanzuckerberg/.github/blob/master/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to <opensource@chanzuckerberg.com>.

