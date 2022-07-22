# Introduction

> **Status**: brainstorming, pre-proposal
>
> ℹ️ **Note** - this is an early draft and has not had any substantive review or circulation. It may contain controversial, undecided, or just plain wrong-headed ideas. I expect several major iterations will be required to converge the underlying primitives with use cases. Please see `issues` noted throughout the doc for a list of active discussions/debates. In particular, this doc has many known gaps identified throughout the with callouts.

The goal of SOMA (“stack of matrices, annotated”) is a flexible, extensible, and open-source API providing access to annotated, 2D matrix data stored in multiple underlying formats and systems. The vision for this API family includes:

- support access to persistent, cloud-resident datasets,
- enable use within popular data science environments (e.g., R, Python), using the tools of that environment (e.g., Python Pandas integration),
- enable "out-of-core" access to data aggregations much larger than single-host main memory
- enable distributed computation over datasets
- provide a building block for higher-level API that may embody domain-specific conventions or schema around annotated 2D matrices (e.g., a cell "atlas").

The SOMA data model is centered on annotated 2-D matrices, conceptually similar to commonly used single-cell 'omics data structures including Seurat Assay, Bioconductor SingleCellExperiment, and ScanPy AnnData. Where possible, the SOMA API attempts to be general purpose and agnostic to the specifics of any given environment, or to the specific conventions of the Single Cell scientific ecosystem.

SOMA is an abstract _API specification_, with the goal of enabling multiple concrete API implementations within different computing environments and data storage systems. SOMA does not specify an at-rest serialization format or underlying storage system.

This document is attempting to codify the abstract, language-neutral SOMA data model and functional operations. Other specifications will document specific language bindings and particular storage system implementations. Where the term `language-specific SOMA specification` is used below, it implies a specification of the SOMA API as it is presented in a given language or computing environment (e.g., the SOMA Python API), common across all storage engine implementations in that language.

# Data Model

The data model is comprised of two layers:

- a set of "foundational" types which are general in nature
- a set of "composed" types, which are composed from the foundational types, and are intended to improve ease of dataset use and interoperability

The foundational types are:

- SOMACollection - a string-keyed container (key-value map) of other SOMA data types, e.g., SOMADataFrame, SOMADataMatrix and SOMACollection.
- SOMADataFrame - a multi-column table with optional indexing -- essentially a dataframe.
- SOMADenseNdArray and SOMASparseNdArray- an offset addressed (zero-based), single-type N-D array, available in either sparse or dense instantiations

The composed types are:

- SOMAExperiment - a specialization and extension of SOMACollection, codifying a set of naming and indexing conventions to represent annotated, 2-D matrix of observations across _multiple_ sets of variables.

In this document, the term `dataframe` implies something akin to an Arrow `RecordBatch`, R `data.frame` or Python `pandas.DataFrame`, where:

- multiple columns may exist, each with a string column name
- all columns are individually typed and contain simple data types (e.g., int64)
- all columns are of equal length
- one or more columns may be indexed

All SOMA data objects are named with URIs.

## Base Type System

The SOMA API borrows its base type system from the Arrow language-agnostic in-memory system for data typing and serialization ([format](https://arrow.apache.org/docs/format/Columnar.html)). The SOMA API is intended to be used with an Arrow implementation such as [PyArrow](https://arrow.apache.org/docs/python/) or the [Arrow R package](https://arrow.apache.org/docs/r/), or other libraries which interoperate with Arrow (e.g., Pandas).

Where SOMA requires an explicit typing system, it utilizes the Arrow types and schema. SOMA has no specific requirements on the type or serialization system used by the underlying storage engine, other than it be capable of understanding and representing the Arrow types. It is expected that any given implementation of SOMA will have limits on the underlying capabilities of its data type system (e.g., just because you can express a type in he Arrow type system does not mean all SOMA implementations will understand it).

### Type definitions used in this document

In the following doc:

- `primitive` types in this specification refer to Arrow primitive types, e.g., `int32`, `float`, etc.
- `string` refers to Arrow UTF-8 variable-length `string`, i.e., `List<Char>`.
- `simple` types include all primitive types, plus `string`.

Other Arrow types are explicitly noted as such, e.g., `Arrow RecordBatch`.

> ⚠️ **Issue** - are there parts of the Arrow type system that we wish to _explicitly exclude_ from SOMA? I have left this issue open (i.e., no specific text) for now, thinking that we can come back and subset as we understand what complex types are required, and how much flexibility should be in this spec. We clearly need some complex types (e.g., RecordBatch, List, etc) as they are implied by `string`, etc. My own preference would be to mandate a small set of primitive types, and leave the rest open to implementations to support as they feel useful.

> ⚠️ **Issue** - the above uses Arrow `string`. Should we be using `large_string` instead (no 2GB cap)?

## Metadata

All SOMA objects may be annotated with a small amounts of simple metadata. Metadata for any SOMA object is a `string`-keyed map of values. Metadata values are Arrow primitive types and Arrow strings. The metadata lifecycle is the same as its containing object, e.g., it will be deleted when the containing object is deleted.

> ℹ️ **Note** - larger or more complex types should be stored using SOMADataFrame, SOMADenseNdArray or SOMASparseNdArray and added to a SOMACollection .

## Foundational Types

The foundational types represent the core data structures used to store and index data. They are intended to be moderately general purpose, and to serve as building blocks for the [Composed Types](#composed-types) which codify domain-specific use cases (e.g., single cell experimental datasets).

### SOMACollection

SOMACollection is an unordered, `string`-keyed map of values. Values may be any SOMA foundational or composed type, including other (nested) SOMACollection objects. Keys in the map are unique and singular (no duplicates, i.e., the SOMACollection is _not_ a multi-map). The SOMACollection is expected to be used for a variety of use cases:

- as a container of independent objects (e.g., a collection of single-cell datasets, each manifest as a [SOMAExperiment](#soma-experiment) object)
- as the basis for building other composed types (e.g., using SOMACollection to organize pre-defined fields in [SOMAExperiment](#soma-experiment) such as multiple layers of `X`).

### SOMADataFrame

`SOMADataFrame` is a multi-column table with a user-defined schema, defining the number of columns and their respective column name and value type. The schema is expressed as an Arrow `Schema`. All `SOMADataFrame` contain a "pseudo-column" called `__rowid`, of type `uint64` and domain `[0, #rows)`. The `__rowid` pseudo-column contains a unique value for each row in the `SOMADataFrame`, and is intended to act as a join key for other objects, such as a `SOMADenseNdArray`.

Most language-specific bindings will provide convertors between SOMADataFrame and other convenient data structures, such as Python `pandas.DataFrame`, R `data.frame`.

### SOMADenseNdArray

`SOMADenseNdArray` is a dense, N-dimensional array with offset (zero-based) integer indexing on each dimension. The `SOMADenseNdArray` has a user-defined schema, which includes:

- type - a `primitive` type, expressed as an Arrow type (e.g., `int64`, `float32`, etc), indicating the type of data contained within the array
- shape - the shape of the array, i.e., number and length of each dimension

All dimensions must have a positive, non-zero length.

> ℹ️ **Note** - on TileDB this is an dense array with `N` uint64 dimensions of domain [0, maxUint64), and a single attribute.

### SOMASparseNdArray

`SOMASparseNdArray` is a sparse, N-dimensional array with offset (zero-based) integer indexing on each dimension. The `SOMASparseNdArray` has a user-defined schema, which includes:

- type - a `primitive` type, expressed as an Arrow type (e.g., `int64`, `float32`, etc), indicating the type of data contained within the array
- shape - the shape of the array, i.e., number and length of each dimension

All dimensions must have a positive, non-zero length.

> ℹ️ **Note** - on TileDB this is an sparse array with `N` uint64 dimensions of domain [0, maxUint64), and a single attribute.

## Composed Types

Composed types are defined as a composition of foundational types, adding name, type and indexing constraints. These types are intended to facilitate data interoperability, ease of use, and _potentially_ enable implementation optimizations by virtue of their typing and structural guarantees. The initial composed types are motivated by single cell biology, but additional types may be added in the future for more diverse use cases.

### SOMAExperiment & SOMAMeasurement

`SOMAExperiment` is a specialized `SOMACollection`, representing an annotated 2-D matrix of measurements. In the single-cell biology use case, a `SOMAExperiment` can represent multiple modes of measurement across a single collection of cells (aka a "multimodal dataset"). Within a `SOMAExperiment`, a set of measurements on a single set of variables (features) is represented as a `SOMAMeasurement`.

The `SOMAExperiment` and `SOMAMeasurement` types compose [foundational types](#foundational-types):

- `SOMAExperiment` - a well defined set of annotated observations defined by a `SOMADataFrame`, and one or more "measurement" on those observations.
- `SOMAMeasurement` - for all observables, a common set of annotated variables (defined by a `SOMADataFrame`) for which values (e.g., measurements, calculations) are stored in `SOMADenseNdMatrix` and `SOMASparseNdMatrix`.

In other words, all `SOMAMeasurement` have a distinct set of variables (features), and inherit common observables from their parent `SOMAExperiment`. The `obs` and `var` dataframes define the axis annotations, and their respective `__rowid` values are the indices for all matrixes stored in the `SOMAMeasurement`.

<figure>
    <img src="images/SOMAExperiment.png" alt="SOMAExperiment">
</figure>

> ⚠️ **Issue** - it would be a good idea to factor `SOMAExperiment` and `SOMAMeasurement` into separate sections.

These types have pre-defined fields, each of which have well-defined naming, typing, dimensionality and indexing constraints. Other user-defined data may be added to a `SOMAExperiment` and `SOMAMeasurement`, as both are a specialization of the `SOMACollection`. Implementations _should_ enforce the constraints on these pre-defined fields. Pre-defined fields are distinguished from other user-defined collection elements, where no schema or indexing semantics are presumed or enforced.

The shape of each axis (`obs` and `var`) are defined by their respective dataframes, and the indexing of matrices is defined by the `__rowid` of the respective axis dataframe.

- `obs` - the observation annotations are shared across the entire `SOMAExperiment`. Matrices indexed on this dimension use the domain defined by the `__rowid` values of the `obs` SOMADataFrame (aka `obsid`).
- `var` - the variable annotations are shared within any given `SOMAMeasurement`. Matrices indexed on this dimension use the domain defined by the `__rowid` values of the `var` SOMADataFrame (aka `varid`).

The pre-defined fields of a `SOMAExperiment` object are:

| Field name | Field type                                | Field description                                                                                                                                                                                                           |
| ---------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `obs`      | `SOMADataFrame`                           | Primary annotations on the _observation_ axis. The contents of the `__rowid` pseudo-column define the _observation_ index domain, aka `obsid`. All observations for the SOMAExperiment _must_ be defined in this dataframe. |
| `ms`       | `SOMACollection[string, SOMAMeasurement]` | A collection of named measurements.                                                                                                                                                                                         |

The `SOMAMeasurement` is a sub-element of a SOMAExperiment, and is otherwise a specialized SOMACollection with pre-defined fields:

| Field name | Field type                                                    | Field description                                                                                                                                                                                                                                                                    |
| ---------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `var`      | `SOMADataFrame`                                               | Primary annotations on the _variable_ axis, for variables in this measurement (i.e., annotates columns of `X`). The contents of the `__rowid` pseudo-column define the _variable_ index domain, aka `varid`. All variables for this measurement _must_ be defined in this dataframe. |
| `X`        | `SOMACollection[string, SOMASparseNdArray\|SOMADenseNdArray]` | A collection of matrices, each containing measured feature values. Each matrix is indexed by `[obsid, varid]`. Both sparse and dense 2D arrays are supported in `X`.                                                                                                                 |
| `obsm`     | `SOMACollection[string, SOMADenseNdArray]`                    | A collection of dense matrices containing annotations of each _obs_ row. Has the same shape as `obs`, and is indexed with `obsid`.                                                                                                                                                   |
| `obsp`     | `SOMACollection[string, SOMASparseNdArray]`                   | A collection of sparse matrices containing pairwise annotations of each _obs_ row. Indexed with `[obsid_1, obsid_2].`                                                                                                                                                                |
| `varm`     | `SOMACollection[string, SOMADenseNdArray]`                    | A collection of dense matrices containing annotations of each _var_ row. Has the same shape as `var`, and is indexed with `varid`                                                                                                                                                    |
| `varp`     | `SOMACollection[string, SOMASparseNdArray]`                   | A collection of sparse matrices containing pairwise annotations of each _var_ row. Indexed with `[varid_1, varid_2]`                                                                                                                                                                 |

For the entire `SOMAExperiment`, the index domain for the elements within `obsp`, `obsm` and `X` (first dimension) are the values defined by the `obs` `SOMADataFrame` `__rowid` column. For each `SOMAMeasurement`, the index domain for `varp`, `varm` and `X` (second dimension) are the values defined by the `var` `SOMADataFrame` `__rowid` column in the same measurement. In other words, all predefined fields in the `SOMAMeasurement` share a common `obsid` and `varid` domain, which is defined by the contents of the respective columns in `obs` and `var` SOMADataFrames.

As with other SOMACollections, the `SOMAExperiment` and `SOMAMeasurement` also have a `metadata` field, and may contain other user-defined elements. Keys in a `SOMAExperiment` and `SOMAMeasurement` beginning with the characters `_`, `.`, or `$` are reserved for ad hoc use, and will not be utilized by this specification. All other keys are reserved for future specifications.

The following naming and indexing constraints are defined for the `SOMAExperiment` and `SOMAMeasurement`:

| Field name                     | Field constraints                                                                                                                                                                                                                   |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `obs`, `var`                   | Field type is a `SOMADataFrame`                                                                                                                                                                                                     |
| `X`                            | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMADenseNdArray` or `SOMASparseNdArray`                                                                                                  |
| `obsp`, `varp`                 | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMASparseNdArray`                                                                                                                        |
| `obsm`, `varm`                 | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMADenseNdArray`                                                                                                                         |
| `obsm`, `obsp`, `varm`, `varp` | Fields may be empty collections.                                                                                                                                                                                                    |
| `X` collection values          | All matrixes must have the shape `(#obs, #var)`. The domain of the first dimension is the values of `obs.__rowid`, and the index domain of the second dimension is the values of `var.__rowid` in the containing `SOMAMeasurement`. |
| `obsm` collection values       | All matrixes must have the shape `(#obs, M)`, where `M` is user-defined. The domain of the first dimension is the values of `obs.__rowid`.                                                                                          |
| `obsp` collection values       | All matrixes must have the shape `(#obs, #obs)`. The domain of both dimensions is the values of `obs.__rowid`.                                                                                                                      |
| `varm` collection values       | All matrixes must have the shape `(#var, M)`, where `M` is user-defined. The domain of the first dimension is the values of `var.__rowid`.                                                                                          |
| `varp` collection values       | All matrixes must have the shape `(#var, #var)`. The domain of both dimensions is the values of `var.__rowid`.                                                                                                                      |

# Functional Operations

The SOMA API includes functional capabilities built around the [SOMA data model](#datamodel.md). The specifics of how these operations manifest in any given language and computing environment is defined elsewhere (**to be created**). Each implementation will minimally support the functional operations defined here. For example, it is likely that a Python implementation will prefer `__getattr__` over an explicit `get()` method, and will augment these functional operations with other Pythonic functionality for ease of use.

In several cases an explicit Application Binary Interface (ABI) has been specified for a function, in the form of an Arrow type or construct. The choice of Arrow as both a type system and data ABI is intended to facilitate integration with third party software in a variety of computing environments.

Any given storage "engine" upon which SOMA is implemented may have additional features and capabilities, and support advanced use cases -- it is expected that SOMA implementations will expose storage engine-specific features. Where possible, these should be implemented to avoid conflict with future changes to the common SOMA API.

> ⚠️ **Issue** - this spec needs to provide guidance on HOW to avoid future incompatibility. For example, can we carve out some namespace for extensions in the functional API?

> ℹ️ **Note** - this section is just a sketch, and is primarily focused on defining abstract primitive operations that must exist on each type.

## SOMACollection

Summary of operations on a SOMACollection, where `ValueType` is any SOMA-defined foundational or composed type, including SOMACollection, SOMADataFrame, SOMADenseNdArray, SOMASparseNdArray or SOMAExperiment:

| Operation           | Description                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| create(uri)         | Create a SOMACollection named with the URI.                                                          |
| delete(uri)         | Delete the SOMACollection specified with the URI. Does not delete the objects within the collection. |
| exists(uri) -> bool | Return true if object exists and is a SOMACollection.                                                |
| get metadata        | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping)                       |
| get type            | Returns the constant "SOMACollection"                                                                |

In addition, SOMACollection supports operations to manage the contents of the collection:

| Operation                        | Description                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| get(string key)                  | Get the object associated with the key                                                   |
| has(string key)                  | Test for the existence of key in collection.                                             |
| set(string key, ValueType value) | Set the key/value in the collection.                                                     |
| del(string key)                  | Remove the key/value from the collection. Does not delete the underlying object (value). |
| iterator                         | Iterate over the collection.                                                             |
| get length                       | Get the number of elements in the collection.                                            |

### Operation: create()

Create a new SOMACollection with the user-specified URI.

```
create(string uri, platform_config) -> void
```

Parameters:

- uri - location at which to create the object.
- platform_config - optional storage-engine specific configuration

## SOMADataFrame

> ⚠️ **To be further specified** -- all methods need specification.

Summary of operations:

| Operation                               | Description                                                                                     |
| --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| create(uri, ...)                        | Create a SOMADataFrame.                                                                         |
| delete(uri)                             | Delete the SOMADataFrame specified with the URI.                                                |
| exists(uri) -> bool                     | Return true if object exists and is a SOMADataFrame.                                            |
| get metadata                            | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping)                  |
| get type                                | Returns the constant "SOMADataFrame"                                                            |
| get schema -> Arrow.Schema              | Return data schema, in the form of an Arrow Schema                                              |
| get is_indexed -> bool                  | Return true if indexed, false if non-indexed.                                                   |
| get index_column_names -> [string, ...] | Return index (dimension) column names if dataframe is indexed, or an empty list if non-indexed. |
| read                                    | Read a subset of data from the SOMADataFrame                                                    |
| write                                   | Write a subset of data to the SOMADataFrame                                                     |

A SOMADataFrame may be optionally indexed by one or more dataframe columns (aka "dimensions"). The name and order of dimensions is specified at the time of creation. Subsets of non-indexed dataframes are addressable by offset (i.e. `__rowid`). Subsets of indexed dataframes are addressable by the user-specified dimensions.

### Operation: create()

Create a new SOMADataFrame with user-specified URI and schema.

```
create(string uri, Arrow.Schema schema,  is_indexed=True, string[] index_column_names, platform_config) -> void
create(string uri, Arrow.Schema schema,  is_indexed=False, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- schema - an Arrow Schema defining the per-column schema. This schema must define all columns, including columns to be named as index columns. The column name `__rowid` is reserved for the pseudo-column of the same name. If the schema includes types unsupported by the SOMA implementation, an error will be raised.
- is_indexed - boolean. If `false`, this is a non-indexed dataframe. If `true`, is an indexed dataframe and `index_column_names` must be specified.
- index_column_names - an list of column names to use as index columns, aka "dimensions" (e.g., `['cell_type', 'tissue_type']`). All named columns must exist in the schema, and at least one index column name is required. Index column order is significant and may affect other operations (e.g. read result order). This parameter is undefined if `is_indexed` is False (i.e., if the dataframe is non-indexed).
- platform_config - optional storage-engine specific configuration

### Operation: read()

Read a user-defined slice of data, optionally filtered, and return results as one or more Arrow.RecordBatch.

Summary:

```
read(
    ids=[[id,...]|all, ...],
    column_names=[`string`, ...]|all,
    batch_size,
    partitions,
    result_order,
    value_filter,
    platform_config,
) -> delayed iterator over Arrow.RecordBatch
```

Parameters:

- ids - the rows to read. Defaults to 'all'. Non-indexed dataframes are addressable with a row offset (uint), a row-offset range (slice) or a list of both. Indexed dataframes are addressable, for each dimension, by value, a value range (slice) or a list of both.
- column_names - the named columns to read and return. Defaults to all.
- batch_size - a [`SOMABatchSize`](#SOMABatchSize), indicating the size of each "batch" returned by the read iterator. Defaults to `auto`.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. If dataframe is indexed, can be one of row-major, col-major or unordered. If dataframe is non-indexed, can be one of rowid-ordered or unordered.
- value_filter - an optional [value filter](#value-filters) to apply to the results. Defaults to no filter.
- platform_config - optional storage-engine specific configuration

The `read` operation will return a language-specific iterator over one or more Arrow RecordBatch objects, allowing the incremental processing of results larger than available memory. The actual iterator used is delegated to language-specific SOMA specs.

### Operation: write()

Write an Arrow.RecordBatch to the persistent object. As duplicate index values are not allowed, index values already present in the object are overwritten and new index values are added.

```
write(Arrow.RecordBatch values, platform_config)
```

Parameters:

- values - an Arrow.RecordBatch containing all columns, including the index columns. The schema for the values must match the schema for the SOMADataFrame.
- platform_config - optional storage-engine specific configuration

If the dataframe is non-indexed, the `values` Arrow RecordBatch must contain a `__rowid` (uint64) column, indicating which rows are being written. If the dataframe is indexed, all index coordinates must be specified in the `values` RecordBatch.

## SOMADenseNdArray

> ⚠️ **To be further specified** -- this is incomplete.

Summary of operations:

| Operation                  | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| create(uri, ...)           | Create a SOMADenseNdArray named with the URI.                                  |
| delete(uri)                | Delete the SOMADenseNdArray specified with the URI.                            |
| exists(uri) -> bool        | Return true if object exists and is a SOMADenseNdArray.                        |
| get metadata               | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping) |
| get type                   | Returns the constant "SOMADenseNdArray".                                       |
| get shape -> (int, ...)    | Return length of each dimension, always a list of length `ndims`.              |
| get ndims -> int           | Return number of dimensions.                                                   |
| get schema -> Arrow.Schema | Return data schema, in the form of an Arrow Schema.                            |
| get is_sparse -> False     | Return the constant False.                                                     |
| read                       | Read a slice of data from the SOMADenseNdArray.                                |
| write                      | Write a slice of data to the SOMADenseNdArray.                                 |

### Operation: create()

Create a new SOMADenseNdArray with user-specified URI and schema.

```
create(string uri, type, shape, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- type - an Arrow type defining the type of each element in the array. If the type is unsupported, an error will be raised.
- shape - the length of each domain as a list, e.g., [100, 10]. All lengths must be in the uint64 range.
- platform_config - optional storage-engine specific configuration

### Operation: read()

Read a user-specified subset of the object and return as one or more read batches.

Summary:

```
read(
    [slice, ...],
    batch_size,
    partitions,
    result_order,
    batch_format,
    platform_config,
) -> delayed iterator over ReadResult
```

- slice - per-dimension slice, expressed as a scalar, a range, or a list of both.
- batch_size - a [`SOMABatchSize`](#SOMABatchSize), indicating the size of each "batch" returned by the read iterator. Defaults to `auto`.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. Can be one of row-major or column-major.
- batch_format - a [`SOMABatchFormat`](#SOMABatchFormat) value, indicating the desired format of each batch. Default: `dense`.
- platform_config - optional storage-engine specific configuration

The `read` operation will return a language-specific iterator over one or more `ReadResult` objects, allowing the incremental processing of results larger than available memory. The actual iterator used is delegated to language-specific SOMA specs. The contents of the batch returned by the iterator is specified by the `batch_format` parameter.

### Operation: write()

Write values to the persistent object. As duplicate coordinates are not allowed, coordinates with values already present in the object are overwritten and new coordinates are added.

```
write(values, platform_config)
```

Values to write may be provided in a variety of formats:

- Tensor: caller provides values as an Arrow.Tensor, and the coordinates at which the dense tensor is written.
- SparseTensor: caller provides a Arrow COO, CSC or CSR SparseTensor
- RecordBatch: caller provides COO-encoded coordinates & data as an Arrow.RecordBatch

Parameters:

- values - values to be written. The type of elements in `values` must match the type of the SOMADenseNdArray.
- platform_config - optional storage-engine specific configuration

## SOMASparseNdArray

> ⚠️ **To be further specified** -- this is incomplete.

Summary of operations:

| Operation                  | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| create(uri, ...)           | Create a SOMASparseNdArray named with the URI.                                 |
| delete(uri)                | Delete the SOMASparseNdArray specified with the URI.                           |
| exists(uri) -> bool        | Return true if object exists and is a SOMASparseNdArray.                       |
| get metadata               | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping) |
| get type                   | Returns the constant "SOMASparseNdArray"                                       |
| get shape -> (int, ...)    | Return length of each dimension, always a list of length `ndims`.              |
| get ndims -> int           | Return number of dimensions.                                                   |
| get schema -> Arrow.Schema | Return data schema, in the form of an Arrow Schema                             |
| get is_sparse -> True      | Return the constant True.                                                      |
| get nnz -> uint            | Return the number of non-zero values in the array.                             |
| read                       | Read a slice of data from the SOMASparseNdArray.                               |
| write                      | Write a slice of data to the SOMASparseNdArray.                                |

### Operation: create()

Create a new SOMASparseNdArray with user-specified URI and schema.

```
create(string uri, type, shape, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- type - an Arrow type defining the type of each element in the array. If the type is unsupported, an error will be raised.
- shape - the length of each domain as a list, e.g., [100, 10]. All lengths must be in the uint64 range.
- platform_config - optional storage-engine specific configuration

### Operation: read()

Read a user-specified subset of the object, and return as one or more read batches.

Summary:

```
read(
    [slice, ...],
    batch_size,
    partitions,
    result_order,
    batch_format,
    platform_config,
) -> delayed iterator over ReadResult
```

- slice - per-dimension slice, expressed as a scalar, a range, or a list of both.
- batch_size - a [`SOMABatchSize`](#SOMABatchSize), indicating the size of each "batch" returned by the read iterator. Defaults to `auto`.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. Can be one of row-major, column-major and unordered.
- batch_format - a [`SOMABatchFormat`](#SOMABatchFormat) value, indicating the desired format of each batch. Default: `coo`.
- platform_config - optional storage-engine specific configuration

The `read` operation will return a language-specific iterator over one or more `ReadResult` objects, allowing the incremental processing of results larger than available memory. The actual iterator used is delegated to language-specific SOMA specs. The contents of the batch returned by the iterator is specified by the `batch_format` parameter.

### Operation: write()

Write values to the persistent object. As duplicate coordinates are not allowed, coordinates already present in the object are overwritten and new coordinates are added.

```
write(values, platform_config)
```

Values to write may be provided in a variety of formats:

- Tensor: caller provides values as an Arrow.Tensor, and the coordinates at which the dense tensor is written.
- SparseTensor: caller provides a Arrow COO, CSC or CSR SparseTensor
- RecordBatch: caller provides COO-encoded coordinates & data as an Arrow.RecordBatch

Parameters:

- values - values to be written. The type of elements in `values` must match the type of the SOMASparseNdArray.
- platform_config - optional storage-engine specific configuration

## Common Interfaces

The following are interfaces defined only to make the subsequent specification simpler. They are not elements in the data model, but rather are named sets of operations used to facilitate the definition of supported operations.

### SOMAMetadataMapping

The SOMAMetadataMapping is an interface to a string-keyed mutable map, representing the available operations on the metadata field in all foundational objects. In most implementations, it will be presented with a language-appropriate interface, e.g., Python `MutableMapping`.

The following operations will exist to manipulate the mapping, providing a getter/setter interface plus the ability to iterate on the collection:

| Operation                      | Description                                            |
| ------------------------------ | ------------------------------------------------------ |
| get(string key) -> value       | Get the value associated with the key.                 |
| has(string key) -> bool        | Test for key existence.                                |
| set(string key, value) -> void | Set the value associated with the key.                 |
| del(string key) -> void        | Remove the key/value from the collection.              |
| iterator                       | Iterate over the collection.                           |
| get length                     | Get the length of the map, the number of keys present. |

> ℹ️ **Note** - it is possible that the data model will grow to include more complex value types. If possible, retain that future option in any API defined.

### SOMABatchSize

Read operations on foundational types return an iterator over "batches" of data, enabling the processing of larger-than-core datasets. The SOMABatchSize allows user control over read batch size, and accepts the following methods of determining batch size:

| BatchSize type | Description                                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `count`        | Batch size defined by result count. For a SOMADataFrame this indicates row count returned per RecordBatch, or for an ND array the number of values. |
| `size`         | Partition defined by size, in bytes, e.g., max RecordBatch size returned by SOMADataFRame read operation.                                           |
| `auto`         | An automatically determined, "reasonable" default partition size. This is the default batch size.                                                   |

### SOMAReadPartitions

To facilitate distributed computation, read operations on foundational types accept a user-specified parameter indicating the desired partitioning of reads and which partition any given read should return. The following options are supported:

| Partition Type | Description                                                                                                                                                                        |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IofN`         | Given I and N, read operations will return the Ith partition of N approximately equal size partitions. Partition boundaries will be stable for any given N and array or dataframe. |

### SOMABatchFormat

Array read operations can return results in a variety of formats. The `SOMABatchFormat` format indicates the format encoding.

| Batch format   | Description                                                                                           |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| `dense`        | Return the coordinates of the slice (e.g. origin, shape) and an Arrow Tensor containing slice values. |
| `coo`          | Return an Arrow.SparseCOOTensor                                                                       |
| `csr`          | Return an Arrow.SparseCSRTensor                                                                       |
| `csc`          | Return an Arrow.SparseCSCTensor                                                                       |
| `record-batch` | Return an Arrow.RecordBatch containing COO-encoded coordinates and values.                            |

## General Utilities

> ⚠️ **To be further specified**

Summary:

```
get_version() -> string                   # return semver-compatible version of the supported SOMA API
get_implementation() -> string            # return the implementation name, e.g., "R-tiledb"
get_implementation_version() -> string    # return the package implementation version as a semver
get_storage_engine() -> string            # return underlying storage engine name, e.g., "tiledb"
```

### Method: get_SOMA_version

This is a pre-release specification in active development. As defined by [semver](https://semver.org/), this API is defined as version `0.0.0-dev`.

## Value Filters

> ⚠️ **To be further specified**

Value filters are expressions used to filter the results of a `read` operation, and specify which results should be returned. The specific means to create and manipulate a value filter is delegated to per-language specifications. This specification uses a pseudo-language for _examples only_.

Value filter expressions will have the following capabilities:

- per-column filter expressions which define:
  - a column name
  - a comparison operator, supporting ==, !=, <, >, <=, >=
  - and a constant
- compound expressions combining other expressions with AND and OR boolean operations

Examples, using a pseudo-syntax:

- `col_A > 0`
- `(col_A > 0) AND (col_B != "deleted")`

# ⚠️ Other Issues (open issues with this doc)

Issues to be resolved:

1. Are there operations specific to SOMAExperiment and SOMAMeasurement that need to be defined? Or do they inherit only the ops from SOMACollection?
2. What (if any) additional semantics around writes need to be defined?
3. Value filter support in NdArray has been proposed:
   - Is there a use case to motivate it?
   - This effectively requires that all read() return batches be sparse, as the value filter will remove values.
   - Where the requested batch_format is `dense` (ie, the user wants a tensor back), this would require that we also provide coordinates and/or a mask in addition to the tensor (values). Or disallow that combination - if you specify a value filter, you can only ask for a sparse-capable batch_format.

# Changelog

1. Acceptance of Arrow as base type system
2. Adding explicit separation of foundational and composed types, and clarified the intent of composed types
3. Rename `uns` to `metadata`
4. Added initial prose for value filter expressions
5. Added further clarification to read incremental return
6. SOMAMatrix removed
7. Operations clarified (add description). Remove assumption of handle/object state.
8. SOMADataFrame generalized to row-indexed or (multi-) user-indexed. Adding \_\_rowid pseudo-column to use in indexing dense matrices.
9. Introduced SOMADenseNdArray/SOMAsparseNdArray and SOMAExperiment/SOMAMeasurement
10. Removed composed type `SOMA`
11. Added initial general utility operations
12. Clarified the data types that may be stored in `metadata`.
13. Clarified namespacing of reserved slots in SOMAExperiment/SOMAMeasurement
14. Renamed SOMAMapping to SOMAMetadataMapping to clarify use
15. Add read partitions and ordering to foundational types.
16. Clarify ABI for read/write chunks to NDArrays.
17. Removed open issues around `raw` - there is already sufficient expressiveness in this spec.
18. Removed var_ms/obs_ms
19. Editorial cleanup and clarifications
20. Simplified dataframe indexing to indexed/non-indexed. Removed from data model; isolated to only those operations affected.
21. Add parameter for storage engine-specific config, to read/write/create ops
22. Support both sparse and dense ndarray in SOMAExperiment X slot.
23. Split read batch_size and partitioning, and clarify intent.
24. Allow multiple format support for NDArray read/write ops.
25. Clarified SOMACollection delete semantics.
