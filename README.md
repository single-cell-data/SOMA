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
