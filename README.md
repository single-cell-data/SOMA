## Unified Single-cell Data Model and API
### Opportunity:
* The programming language and toolchain used to analyse single cell data determines the format that the data will be published in. These language- and toolchain-driven data silos inhibit use cases like model training that require bringing data to tools.
* Best-in-class algorithms are often available in only a single language ecosystem or toolchain, or take substantial effort to make portable.
* Multimodal data, which are becoming more common, lack standardization and support--particularly in the python ecosystem.
* Data are becoming large enough that moving serialized objects around will soon be infeasible - cloud optimized formats will be required to support the next analysis phase, and out of core processing is becoming increasingly important.

We envision an API that enables users to slice and compute on large (100s millions observations) single cell datasets stored in the cloud using the [AnnData](https://anndata.readthedocs.io/en/latest/), [SingleCellExperiment](http://bioconductor.org/packages/release/bioc/html/SingleCellExperiment.html), and [Seurat](https://satijalab.org/seurat/) toolchains.

To get started, we will focus on enabling data to be used by all major toolchains and on nailing the multi-modal data use cases. We believe this will be sufficient to drive API adoption.
With data silos broken, larger data use cases will be enabled and the need for a cloud-optimized data format will be more widely felt.

Initial Focus:
* A standardized single-cell container, with (basic) read & query access to the data in the container.
* Import/export from all commonly used in-memory formats (eg, AnnData, SingleCellExperiment, or Seurat)
* Access to underlying native (eg, TileDB) objects to allow advanced use cases
* Python and R support

Longer term goals:
* Native support in the popular toolchains, reducing the reliance on on-the-fly conversion (eg, anndata2ri)
* Incremental modification and composition of the dataset
* Optimizations required for performant analysis

The core functions of the initial API are:
* Compose a "sc dataset" Python object out of pre-existing TileDB arrays.  This object is the composition of one or more sc_groups (terms defined below).
* Simple access to sc_dataset/sc_group properties (eg, obs, var, X) and ability to slice/query on the entire object based on obs/var labels.
* For Python, Import/export an in-memory AnnData object (for subsequent use with AnnData/ScanPy) from either a slice/query result or the entire object.  For R, same basic function but to/from Seurat and SingleCellExperiment

This [initial draft](specification.md) proposes an API for single-cell data that attempts to unify the data models followed by AnnData, Bioconductor’s SingleCellExperiment, Seurat and CXG.
The initial API surface is intentionally focused on a small initial set of use cases, on the assumption that API users can always escape to more complete tool chain specific API, or to underlying (advanced) native objects (eg, TileDB).
We are seeking community feedback.

It first describes a general data model that captures all the above frameworks. Then it explains how TileDB can implement this model on-disk so that we have a concrete implementation reference. Next, it describes how TileDB can query this model with its generic array API “soon” (as some minor features are a work in progress). Subsequently, it proposes a more single-cell-specific API that can easily be built on top of TileDB’s, in order to hide the TileDB-specific implementation and API. We will focus only on Python and R for now for simplicity. Finally, it concludes with a list of features that will need to be implemented on the TileDB side in order to have a working prototype very soon.

### Development Roadmap:

Q1 Goal: Demonstrate a proof-of-concept of the Matrix-API and a TileDB-based format implementation that can generate and be created from AnnData, MuData, SingleCellExperiment, MultiAssayExperiment, and Seurat objects.  

#### Deliverables:

* Definition of the matrix API spec for Python, R and C++, fully documented
* A first pass implementation of the API using TileDB
* Single-modality data support:
  * Ability for round-trip AnnData -> matrix API -> write to TileDB format -> read to matrix API -> anndata
  * Ability for round-trip Seurat -> matrix API -> write to TileDB format -> read to matrix API -> Seurat
  * Ability for round-trip SingleCellExperiment -> matrix API -> write to TileDB format -> read to matrix API -> SingleCellExperiment
* Multi-modality data support:
  * Ability for round-trip MultiAssayExperiment -> matrix API -> write to TileDB format -> read to matrix API -> MultiAssayExperiment
  * Ability for round-trip mudata -> matrix API -> write to TileDB format -> read to matrix API -> mudata
* Ability to store analysis results (e.g., graphs, reductions, etc)


#### Plan:

| Category | Milestone | Date |
| --- | --- | --- |
Foundation (C++) | Ability to import a h5ad file to the TileDB on-disk format that the matrix API will use | Feb 4
Foundation (C++) | Implement C++ API of the matrix API spec with read support from the TileDB on-disk format | Feb 4
Python | Define the in-memory format spec for the Python API | Feb 4
Python | Build the Python API wrapper for the C++ API that implements the matrix API, with focus on reads | Feb 4
Python | Implement to_anndata from the Python in-memory objects of the matrix API | Feb 18
Python | Implement from_anndata to the in-memory format of the matrix API spec | Feb 18
R | Define the in-memory format spec for the R API  (done, need to document) | March 4
R | Build the R API that wraps the C++ API of the matrix API spec with focus on reads | Feb 11 
R | Implement to_seurat from the R in-memory objects of the matrix API | March 4
R | Implement from_seurat to the in-memory format of the matrix API spec (done, need to document | Feb 18
R | Implement from_single_cell_experiment for bioconductor | March 4
R | Implement to_single_cell_experiment for bioconductor | March 4
Common | Write from the in-memory TileDB formats to TileDB on disk | March 4
Common | Storage of analysis results, such as, graphs, reductions, etc | Mar 11
Common | Multimodal support with sc_dataset | Mar 18