# Introduction

> **Status**: brainstorming, pre-proposal, in active development. Version: `0.2.0-dev`
>
> ℹ️ **Note** - this is an early working draft (WORK IN PROGRESS). It may contain controversial, undecided, or incomplete proposals - feedback is encouraged. It is expect that additional revisions will be required to converge the underlying primitives with use cases, and to incorporate lessons from initial implementation and early users. Please see `issues` and other call-outs throughout the doc for a list of active discussions/debates.

The goal of SOMA (“stack of matrices, annotated”) is a flexible, extensible, and open-source API providing access to annotated, 2D matrix data stored in multiple underlying formats and systems. The vision for this API family includes:

- support access to persistent, cloud-resident datasets,
- enable use within popular data science environments (e.g., R, Python), using the tools of that environment (e.g., Python Pandas integration),
- enable "out-of-core" access to data aggregations much larger than single-host main memory
- enable distributed computation over datasets
- provide a building block for higher-level API that may embody domain-specific conventions or schema around annotated 2D matrices (e.g., a cell "atlas").

The SOMA data model is centered on annotated 2-D matrices, conceptually similar to commonly used single-cell 'omics data structures including Seurat Assay, Bioconductor SingleCellExperiment, and ScanPy AnnData. Where possible, the SOMA API attempts to be general purpose and agnostic to the specifics of any given environment, or to the specific conventions of the Single Cell scientific ecosystem.

SOMA is an abstract _API specification_, with the goal of enabling multiple concrete API implementations within different computing environments and data storage systems. SOMA does not specify an at-rest serialization format or underlying storage system.

This document is attempting to codify the abstract, language-neutral SOMA data model and functional operations. Other specifications will document specific language bindings and particular storage system implementations. Where the term `language-specific SOMA specification` is used below, it implies a specification of the SOMA API as it is presented in a given language or computing environment (e.g., the SOMA Python API), common across all storage engine implementations in that language.

# Lifecycle Stages

The SOMA API uses [RStudio's lifecycle stage model](https://lifecycle.r-lib.org) to indicate the maturity of its classes, methods and parameters. The lifecycle stages are:

- `experimental`: Under active development and may undergo significant and breaking changes.
- `maturing`: Under active development but the interface and behavior have stabilized and are unlikely to change significantly but breaking changes are still possible.
- `stable`: The interface is considered stable and breaking changes will be avoided where possible. Breaking changes that cannot be avoided will be accompanied by a major version bump.
- `deprecated`: The API is no longer recommended for use and may be removed in a future release.

Lifecycle stages are indicated in the documentation for each class, method and parameter using a `[lifecycle: <stage>]` tag. For example:

```python
class DataFrame():
    """
    A multi-column table with indexing on user-specified columns [lifecycle: maturing].
    """
...
    def create(
        self,
        schema: pa.Schema,
    ) -> "DataFrame":
        """
        Create a SOMADataFrame from a `pyarrow.Schema` [lifecycle: maturing].

        Parameters
        ----------
        schema : pyarrow.Schema
            The schema of the DataFrame to create [lifecycle: stable].
        """
```

If a class, method or parameter is not explicitly marked with a lifecycle stage, it is assumed to be `experimental`.

# Data Model

The data model is comprised of two layers:

- a set of "foundational" types which are general in nature
- a set of "composed" types, which are composed from the foundational types, and are intended to improve ease of dataset use and interoperability

The foundational types are:

- SOMACollection - a string-keyed container (key-value map) of other SOMA data types, e.g., SOMADataFrame, SOMADataMatrix and SOMACollection.
- SOMADataFrame - a multi-column table -- essentially a dataframe with indexing on user-specified columns.
- SOMADenseNdArray and SOMASparseNdArray- an offset addressed (zero-based), single-type N-D array, available in either sparse or dense instantiations

The composed types are:

- SOMAExperiment - a specialization and extension of SOMACollection, codifying a set of naming and indexing conventions to represent annotated, 2-D matrix of observations across _multiple_ sets of variables.

In this document, the term `dataframe` implies something akin to an Arrow `Table` (or `RecordBatch`), R `data.frame` or Python `pandas.DataFrame`, where:

- multiple columns may exist, each with a string column name
- all columns are individually typed and contain simple data types (e.g., int64)
- all columns are of equal length
- rows are addressed by one or more dataframe columns

All SOMA data objects are named with URIs.

## Base Type System

The SOMA API borrows its base type system from the Arrow language-agnostic in-memory system for data typing and serialization ([format](https://arrow.apache.org/docs/format/Columnar.html)). The SOMA API is intended to be used with an Arrow implementation such as [PyArrow](https://arrow.apache.org/docs/python/) or the [Arrow R package](https://arrow.apache.org/docs/r/), or other libraries which interoperate with Arrow (e.g., Pandas).

Where SOMA requires an explicit typing system, it utilizes the Arrow types and schema. SOMA has no specific requirements on the type or serialization system used by the underlying storage engine, other than it be capable of understanding and representing the Arrow types. It is expected that any given implementation of SOMA will have limits on the underlying capabilities of its data type system (e.g., just because you can express a type in the Arrow type system does not mean all SOMA implementations will understand it).

### Type definitions used in this document

In the following doc:

- `primitive` types in this specification refer to Arrow primitive types, e.g., `int32`, `float`, etc.
- `string` refers to Arrow UTF-8 variable-length `string`, i.e., `List<Char>`.
- `simple` types include all primitive types, plus `string`.

Other Arrow types are explicitly noted as such, e.g., `Arrow RecordBatch`.

Numeric index types (eg, offset indexing into dense arrays) are specified with `int64` type and a domain of `[0, 2^63-1)`. In other words, positive `int64` values are used for offset indexing.

> ⚠️ **Issue** - are there parts of the Arrow type system that we wish to _explicitly exclude_ from SOMA? I have left this issue open (i.e., no specific text) for now, thinking that we can come back and subset as we understand what complex types are required, and how much flexibility should be in this spec. We clearly need some complex types (e.g., RecordBatch, List, etc) as they are implied by `string`, etc. My own preference would be to mandate a small set of primitive types, and leave the rest open to implementations to support as they feel useful.

### Type conformance and promotion

SOMA is intended to be strongly typed. With one exception noted below, all requests for a given Arrow type must be fulfilled or generate an error based upon the capabilities of the underlying storage system. Silently casting to a less capable type (eg, float64 to float32) is _not_ permitted. All operations specifying or introspecting the type system must be self-consistent, eg, if object `create` accepts a given Arrow type or schema, the `get schema` operation must return the same types.

SOMA _does_ permit one form of type promotion - variable length types (`string`, `binary`) may be promoted to their 64-bit variants (`large_string`, `large_binary`) at the time of object creation. However, this promotion must be explicit and visible to the API user via the `get schema` operation.

SOMA places no constraints on the underlying types used by the storage system, as long as the API-level representation is consistent across operations, and the supported types full match the Arrow definition of their type semantics.

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

`SOMADataFrame` is a multi-column table with a user-defined schema, defining the number of columns and their respective column name and value type. The schema is expressed as an Arrow `Schema`.

All `SOMADataFrame` must contain a column called `soma_joinid`, of type `int64` and domain `[0, 2^63-1)`. The `soma_joinid` column contains a unique value for each row in the `SOMADataFrame`, and intended to act as a joint key for other objects, such as `SOMASparseNdArray`.

The default "fill" value for `SOMADataFrame` is the zero or null value of the respective column data type (e.g., Arrow.float32 defaults to 0.0, Arrow.string to "", etc).

Most language-specific bindings will provide convertors between SOMADataFrame and other convenient data structures, such as Python `pandas.DataFrame`, R `data.frame`.

### SOMADenseNdArray

`SOMADenseNdArray` is a dense, N-dimensional array of `primitive` type, with offset (zero-based) integer indexing on each dimension. The `SOMADenseNdArray` has a user-defined schema, which includes:

- type - a `primitive` type, expressed as an Arrow type (e.g., `int64`, `float32`, etc), indicating the type of data contained within the array
- shape - the shape of the array, i.e., number and length of each dimension

All dimensions must have a positive, non-zero length, and there must be 1 or more dimensions. Where explicitly referenced in the API, the dimensions are named `soma_dim_N`, where `N` is the dimension number (eg, `soma_dim_0`), and elements are named `soma_data`.

The default "fill" value for `SOMADenseNdArray` is the zero or null value of the array type (e.g., Arrow.float32 defaults to 0.0).

> ℹ️ **Note** - on TileDB this is an dense array with `N` `int64` dimensions of domain [0, maxInt64), and a single attribute.

### SOMASparseNdArray

`SOMASparseNdArray` is a sparse, N-dimensional array of `primitive` type, with offset (zero-based) integer indexing on each dimension. The `SOMASparseNdArray` has a user-defined schema, which includes:

- type - a `primitive` type, expressed as an Arrow type (e.g., `int64`, `float32`, etc), indicating the type of data contained within the array
- shape - the shape of the array, i.e., number and length of each dimension

All dimensions must have a positive, non-zero length, and there must be 1 or more dimensions. Implicitly stored elements (ie, those not explicitly stored in the array) are assumed to have a value of zero. Where explicitly referenced in the API, the dimensions are named `soma_dim_N`, where `N` is the dimension number (eg, `soma_dim_0`), and elements are named `soma_data`.

The default "fill" value for `SOMASparseNdArray` is the zero or null value of the array type (e.g., Arrow.float32 defaults to 0.0).

> ℹ️ **Note** - on TileDB this is an sparse array with `N` `int64` dimensions of domain [0, maxInt64), and a single attribute.

## Composed Types

Composed types are defined as a composition of foundational types, adding name, type and indexing constraints. These types are intended to facilitate data interoperability, ease of use, and _potentially_ enable implementation optimizations by virtue of their typing and structural guarantees. The initial composed types are motivated by single cell biology, but additional types may be added in the future for more diverse use cases.

### SOMAExperiment & SOMAMeasurement

`SOMAExperiment` is a specialized `SOMACollection`, representing an annotated 2-D matrix of measurements. In the single-cell biology use case, a `SOMAExperiment` can represent multiple modes of measurement across a single collection of cells (aka a "multimodal dataset"). Within a `SOMAExperiment`, a set of measurements on a single set of variables (features) is represented as a `SOMAMeasurement`.

The `SOMAExperiment` and `SOMAMeasurement` types compose [foundational types](#foundational-types):

- `SOMAExperiment` - a well defined set of annotated observations defined by a `SOMADataFrame`, and one or more "measurement" on those observations.
- `SOMAMeasurement` - for all observables, a common set of annotated variables (defined by a `SOMADataFrame`) for which values (e.g., measurements, calculations) are stored in `SOMADenseNdMatrix` and `SOMASparseNdMatrix`.

In other words, all `SOMAMeasurement` have a distinct set of variables (features), and inherit common observables from their parent `SOMAExperiment`. The `obs` and `var` dataframes define the axis annotations, and their respective `soma_joinid` values are the indices for all matrixes stored in the `SOMAMeasurement`.

<figure>
    <img src="images/SOMAExperiment.png" alt="SOMAExperiment">
</figure>

> ⚠️ **Issue** - it would be a good idea to factor `SOMAExperiment` and `SOMAMeasurement` into separate sections.

These types have pre-defined fields, each of which have well-defined naming, typing, dimensionality and indexing constraints. Other user-defined data may be added to a `SOMAExperiment` and `SOMAMeasurement`, as both are a specialization of the `SOMACollection`. Implementations _should_ enforce the constraints on these pre-defined fields. Pre-defined fields are distinguished from other user-defined collection elements, where no schema or indexing semantics are presumed or enforced.

The shape of each axis (`obs` and `var`) are defined by their respective dataframes, and the indexing of matrices is defined by the `soma_joinid` of the respective axis dataframe.

- `obs` - the observation annotations are shared across the entire `SOMAExperiment`. Matrices indexed on this dimension use the domain defined by the `soma_joinid` values of the `obs` SOMADataFrame (aka `obsid`).
- `var` - the variable annotations are shared within any given `SOMAMeasurement`. Matrices indexed on this dimension use the domain defined by the `soma_joinid` values of the `var` SOMADataFrame (aka `varid`).

The pre-defined fields of a `SOMAExperiment` object are:

| Field name | Field type                                | Field description                                                                                                                                                                                                               |
| ---------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `obs`      | `SOMADataFrame`                           | Primary annotations on the _observation_ axis. The contents of the `soma_joinid` pseudo-column define the _observation_ index domain, aka `obsid`. All observations for the SOMAExperiment _must_ be defined in this dataframe. |
| `ms`       | `SOMACollection[string, SOMAMeasurement]` | A collection of named measurements.                                                                                                                                                                                             |

The `SOMAMeasurement` is a sub-element of a SOMAExperiment, and is otherwise a specialized SOMACollection with pre-defined fields:

| Field name | Field type                                                    | Field description                                                                                                                                                                                                                                                                        |
| ---------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `var`      | `SOMADataFrame`                                               | Primary annotations on the _variable_ axis, for variables in this measurement (i.e., annotates columns of `X`). The contents of the `soma_joinid` pseudo-column define the _variable_ index domain, aka `varid`. All variables for this measurement _must_ be defined in this dataframe. |
| `X`        | `SOMACollection[string, SOMASparseNdArray\|SOMADenseNdArray]` | A collection of matrices, each containing measured feature values. Each matrix is indexed by `[obsid, varid]`. Both sparse and dense 2D arrays are supported in `X`.                                                                                                                     |
| `obsm`     | `SOMACollection[string, SOMADenseNdArray]`                    | A collection of dense matrices containing annotations of each _obs_ row. Has the same shape as `obs`, and is indexed with `obsid`.                                                                                                                                                       |
| `obsp`     | `SOMACollection[string, SOMASparseNdArray]`                   | A collection of sparse matrices containing pairwise annotations of each _obs_ row. Indexed with `[obsid_1, obsid_2].`                                                                                                                                                                    |
| `varm`     | `SOMACollection[string, SOMADenseNdArray]`                    | A collection of dense matrices containing annotations of each _var_ row. Has the same shape as `var`, and is indexed with `varid`                                                                                                                                                        |
| `varp`     | `SOMACollection[string, SOMASparseNdArray]`                   | A collection of sparse matrices containing pairwise annotations of each _var_ row. Indexed with `[varid_1, varid_2]`                                                                                                                                                                     |

For the entire `SOMAExperiment`, the index domain for the elements within `obsp`, `obsm` and `X` (first dimension) are the values defined by the `obs` dataframe `soma_joinid` column. For each `SOMAMeasurement`, the index domain for `varp`, `varm` and `X` (second dimension) are the values defined by the `var` dataframe `soma_joinid` column in the same measurement. In other words, all predefined fields in the `SOMAMeasurement` share a common `obsid` and `varid` domain, which is defined by the contents of the respective columns in `obs` and `var` dataframes.

As with other SOMACollections, the `SOMAExperiment` and `SOMAMeasurement` also have a `metadata` field, and may contain other user-defined elements. Keys in a `SOMAExperiment` and `SOMAMeasurement` beginning with the characters `_`, `.`, or `$` are reserved for ad hoc use, and will not be utilized by this specification. All other keys are reserved for future specifications.

The following naming and indexing constraints are defined for the `SOMAExperiment` and `SOMAMeasurement`:

| Field name                     | Field constraints                                                                                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `obs`, `var`                   | Field type is a `SOMADataFrame`                                                                                                                                          |
| `X`                            | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMADenseNdArray` or `SOMASparseNdArray`                                       |
| `obsp`, `varp`                 | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMASparseNdArray`                                                             |
| `obsm`, `varm`                 | Field type is a `SOMACollection`, and each element in the collection has a value of type `SOMADenseNdArray`                                                              |
| `obsm`, `obsp`, `varm`, `varp` | Fields may be empty collections.                                                                                                                                         |
| `X` collection values          | All matrixes must have the shape `(O, V)`, where `O` is the domain of `obs.soma_joinid`, and `V` is the domain of `var.soma_joinid` in the containing `SOMAMeasurement`. |
| `obsm` collection values       | All matrixes must have the shape `(O, M)`, where `M` is user-defined. The domain of the first dimension is the values of `obs.soma_joinid`.                              |
| `obsp` collection values       | All matrixes must have the shape `(O, O)`. The domain of both dimensions is the values of `obs.soma_joinid`.                                                             |
| `varm` collection values       | All matrixes must have the shape `(V, M)`, where `M` is user-defined. The domain of the first dimension is the values of `var.soma_joinid`.                              |
| `varp` collection values       | All matrixes must have the shape `(V, V)`. The domain of both dimensions is the values of `var.soma_joinid`.                                                             |

# Functional Operations

The SOMA API includes functional capabilities built around the [SOMA data model](#datamodel.md). The specifics of how these operations manifest in any given language and computing environment is defined elsewhere (**to be created**). Each implementation will minimally support the functional operations defined here. For example, it is likely that a Python implementation will prefer `__getattr__` over an explicit `get()` method, and will augment these functional operations with other Pythonic functionality for ease of use.

In several cases an explicit Application Binary Interface (ABI) has been specified for a function, in the form of an Arrow type or construct. The choice of Arrow as both a type system and data ABI is intended to facilitate integration with third party software in a variety of computing environments.

Any given storage "engine" upon which SOMA is implemented may have additional features and capabilities, and support advanced use cases -- it is expected that SOMA implementations will expose storage engine-specific features. Where possible, these should be implemented to avoid conflict with future changes to the common SOMA API. Where possible, types and variables beginning with 'soma' or 'SOMA' should be preserved for future versions of this spec.

> ℹ️ **Note** - this section is just a sketch, and is primarily focused on defining abstract primitive operations that must exist on each type.

## SOMACollection

Summary of operations on a SOMACollection, where `ValueType` is any SOMA-defined foundational or composed type, including SOMACollection, SOMADataFrame, SOMADenseNdArray, SOMASparseNdArray or SOMAExperiment:

| Operation           | Description                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| create(uri)         | Create a SOMACollection named with the URI.                                                          |
| delete(uri)         | Delete the SOMACollection specified with the URI. Does not delete the objects within the collection. |
| exists(uri) -> bool | Return true if object exists and is a SOMACollection.                                                |
| get metadata        | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping)                       |
| get soma_type       | Returns the constant "SOMACollection"                                                                |

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
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

## SOMADataFrame

> ⚠️ **To be further specified** -- all methods need specification.
>
> Summary of operations:

| Operation                               | Description                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------ |
| create(uri, ...)                        | Create a SOMADataFrame.                                                        |
| delete(uri)                             | Delete the SOMADataFrame specified with the URI.                               |
| exists(uri) -> bool                     | Return true if object exists and is a SOMADataFrame.                           |
| get metadata                            | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping) |
| get soma_type                           | Returns the constant "SOMADataFrame"                                           |
| get schema -> Arrow.Schema              | Return data schema, in the form of an Arrow Schema                             |
| get index_column_names -> [string, ...] | Return index (dimension) column names.                                         |
| read                                    | Read a subset of data from the SOMADataFrame                                   |
| write                                   | Write a subset of data to the SOMADataFrame                                    |

A SOMADataFrame is indexed by one or more dataframe columns (aka "dimensions"). The name and order of dimensions is specified at the time of creation. [Slices](#indexing-and-slicing) are addressable by the user-specified dimensions. The `soma_joinid` column may be specified as an index column.

SOMADataFrame rows require unique coordinates. In other words, the read and write operations will assume that any given coordinate tuple for indexed columns uniquely identifies a single dataframe row.

### Operation: create()

Create a new SOMADataFrame with user-specified URI and schema.

The schema parameter must define all user-specified columns. The schema may optionally include `soma_joinid`, but an error will be raised if it is not of type Arrow.int64. If `soma_joinid` is not specified, it will be added to the schema. All other column names beginning with `soma_` are reserved, and if present in the schema, will generate an error. If the schema includes types unsupported by the SOMA implementation, an error will be raised.

```
create(string uri, Arrow.Schema schema, string[] index_column_names, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- schema - an Arrow Schema defining the per-column schema.
- index_column_names - an list of column names to use as index columns, aka "dimensions" (e.g., `['cell_type', 'tissue_type']`). All named columns must exist in the schema, and at least one index column name is required. Index column order is significant and may affect other operations (e.g. read result order). The `soma_joinid` column may be indexed.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

### get schema

Return the SOMADataFrame schema as an Arrow schema object. The schema will include all user- and system-defined columns, including `soma_joinid`.

### get index column names

Return a list of all column names which index the dataframe.

### Operation: read()

Read a user-defined slice of data, optionally filtered, and return results as one or more Arrow.Table.

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
) -> delayed iterator over Arrow.Table
```

Parameters:

- ids - the rows to read. Defaults to 'all'. Coordinates for each dimension may be specified by value, a value range (slice -- see the [indexing and slicing](#indexing-and-slicing) section below), an Arrow array of values, or a list of both.
- column_names - the named columns to read and return. Defaults to all, including system-defined columns (`soma_joinid`).
- batch_size - a [`SOMABatchSize`](#SOMABatchSize), indicating the size of each "batch" returned by the read iterator. Defaults to `auto`.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. If dataframe is indexed, can be one of row-major, col-major or unordered. If dataframe is non-indexed, can be one of rowid-ordered or unordered.
- value_filter - an optional [value filter](#value-filters) to apply to the results. Defaults to no filter.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

The `read` operation will return a language-specific iterator over one or more Arrow Table objects, allowing the incremental processing of results larger than available memory. The actual iterator used is delegated to language-specific SOMA specs.

### Operation: write()

Write an Arrow.RecordBatch or Arrow.Table to the persistent object. As duplicate index values are not allowed, index values already present in the object are overwritten and new index values are added.

```
write(Arrow.RecordBatch values, platform_config)
write(Arrow.Table values, platform_config)
```

Parameters:

- values - a parameter containing all columns, including the index columns. The schema for the values must match the schema for the SOMADataFrame.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

All columns, including index columns and `soma_joinid` must be specified in the `values` parameter.

## SOMADenseNdArray

> ⚠️ **To be further specified** -- this is incomplete.

Summary of operations:

| Operation                  | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| create(uri, ...)           | Create a SOMADenseNdArray named with the URI.                                  |
| delete(uri)                | Delete the SOMADenseNdArray specified with the URI.                            |
| exists(uri) -> bool        | Return true if object exists and is a SOMADenseNdArray.                        |
| get metadata               | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping) |
| get soma_type              | Returns the constant "SOMADenseNdArray".                                       |
| get shape -> (int, ...)    | Return length of each dimension, always a list of length `ndims`.              |
| get ndims -> int           | Return number of dimensions.                                                   |
| get schema -> Arrow.Schema | Return data schema, in the form of an Arrow Schema.                            |
| get is_sparse -> False     | Return the constant False.                                                     |
| read                       | Read a subarray from the SOMADenseNdArray.                                     |
| write                      | Write a subarray to the SOMADenseNdArray.                                      |

### Operation: create()

Create a new SOMADenseNdArray with user-specified URI and schema.

```
create(string uri, type, shape, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- type - an Arrow `primitive` type defining the type of each element in the array. If the type is unsupported, an error will be raised.
- shape - the length of each domain as a list, e.g., [100, 10]. All lengths must be positive values the `int64` range `[0, 2^63-1)`.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

### Operation: get schema

Return the array schema as an Arrow.Schema object. This operation will return the schema of the Arrow.RecordBatch returned
by the `read` operation when it is called with a `batch_format` parameter value of `record-batch`. Field names in the schema
will be:

- `soma_dim_N`: the type of the Nth dimension. This will always be an `int64` in the range `[0, 2^63-1)`.
- `soma_data`: the user-specified type of the array elements, as specified in the `create` operation.

### Operation: read()

Read a user-specified dense subarray from the object and return as an Arrow.Tensor.

Summary:

```
read(
    coords,
    batch_size,
    partitions,
    result_order,
    platform_config,
) -> Arrow.Tensor
```

- coords - per-dimension slice (see the [indexing and slicing](#indexing-and-slicing) section below), expressed as a per-dimension list of scalar or range.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. Can be one of row-major or column-major.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

The `read` operation will return an Arrow Tensor containing the requested subarray.

> ⚠️ **Issue** - support for other formats, such as Arrow Table, is under discussion.

### Operation: write()

Write an Arrow Tensor to a dense subarray of the persistent object.

```
write(
    [slice, ...]
    values,
    platform_config
)
```

Values are specified as an Arrow Tensor.

Parameters:

- coords - per-dimension slice, expressed as a per-dimension list of scalar or range.
- values - values to be written, provided as an Arrow Tensor. The type of elements in `values` must match the type of the SOMADenseNdArray.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

## SOMASparseNdArray

> ⚠️ **To be further specified** -- this is incomplete.

Summary of operations:

| Operation                  | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| create(uri, ...)           | Create a SOMASparseNdArray named with the URI.                                 |
| delete(uri)                | Delete the SOMASparseNdArray specified with the URI.                           |
| exists(uri) -> bool        | Return true if object exists and is a SOMASparseNdArray.                       |
| get metadata               | Access the metadata as a mutable [`SOMAMetadataMapping`](#SOMAMetadataMapping) |
| get soma_type              | Returns the constant "SOMASparseNdArray"                                       |
| get shape -> (int, ...)    | Return length of each dimension, always a list of length `ndims`.              |
| get ndims -> int           | Return number of dimensions.                                                   |
| get schema -> Arrow.Schema | Return data schema, in the form of an Arrow Schema                             |
| get is_sparse -> True      | Return the constant True.                                                      |
| get nnz -> uint            | Return the number stored values in the array, including explicit zeros.        |
| read                       | Read a slice of data from the SOMASparseNdArray.                               |
| write                      | Write a slice of data to the SOMASparseNdArray.                                |

### Operation: create()

Create a new SOMASparseNdArray with user-specified URI and schema.

```
create(string uri, type, shape, platform_config) -> void
```

Parameters:

- uri - location at which to create the object
- type - an Arrow `primitive` type defining the type of each element in the array. If the type is unsupported, an error will be raised.
- shape - the length of each domain as a list, e.g., [100, 10]. All lengths must be in the `int64` range `[0, 2^63-1)`.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

### Operation: get schema

Return the array schema as an Arrow.Schema object. This operation will return the schema of the Arrow.RecordBatch returned
by the `read` operation when it is called with a `batch_format` parameter value of `record-batch`. Field names in the schema
will be:

- `soma_dim_N`: the type of the Nth dimension. This will always be a `int64` in the range `[0, 2^63-1)`.
- `soma_data`: the user-specified type of the array elements, as specified in the `create` operation.

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

- slice - per-dimension slice (see the [indexing and slicing](#indexing-and-slicing) section below), expressed as a scalar, a range, an Arrow array or chunked array of scalar, or a list of both.
- batch_size - a [`SOMABatchSize`](#SOMABatchSize), indicating the size of each "batch" returned by the read iterator. Defaults to `auto`.
- partition - an optional [`SOMAReadPartitions`](#SOMAReadPartitions) to partition read operations.
- result_order - order of read results. Can be one of row-major, column-major and unordered.
- batch_format - a [`SOMABatchFormat`](#SOMABatchFormat) value, indicating the desired format of each batch. Default: `coo`.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

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
- Table: caller provides COO-encoded coordinates & data as an Arrow.Table

Parameters:

- values - values to be written. The type of elements in `values` must match the type of the SOMASparseNdArray.
- [platform_config](#platform-specific-configuration) - optional storage-engine specific configuration

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
| `count`        | Batch size defined by result count. For a SOMADataFrame this indicates row count returned per Arrow.Table, or for an ND array the number of values. |
| `size`         | Partition defined by size, in bytes, e.g., max Arrow.Table size returned by SOMADataFRame read operation.                                           |
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
| `table`        | Return an Arrow.Table containing COO-encoded coordinates and values.                                  |

## General Utilities

> ⚠️ **To be further specified**

Summary:

```
get_SOMA_version() -> string              # return semver-compatible version of the supported SOMA API
get_implementation() -> string            # return the implementation name, e.g., "R-tiledb"
get_implementation_version() -> string    # return the package implementation version as a semver-compatible string
get_storage_engine() -> string            # return underlying storage engine name, e.g., "tiledb"
```

Semver compatible strings comply with the specification at [semver.org](https://semver.org).

### Method: get_SOMA_version

This is a pre-release specification in active development. As defined by [semver](https://semver.org/), this API is defined as version `0.2.0-dev`.

_Note:_ this API was preceded by another (un-versioned) API draft, which is colloquially referred to as `0.0.0-dev` and `0.1.0-dev`

## Indexing and slicing

* In the above `read()` methods, indexing by an empty list of IDs must result in zero-length query results.
* Negative indices must not be interpeted as aliases for positive indices (as is common in Python) or as exclusionary (as is common in R).
* Slices are doubly inclusive -- e.g. slicing with bounds 2 and 4 includes array indices 2, 3, and 4.
* Slices may be doubly open -- slicing with no bounds (e.g. Python's `[:]`) means select all
* Slices may be half-open -- slicing with lower bound 2 and no upperbound selects indices 2 through the highest index present in the given data; slicing with no lower bound and upper bound 4 selects from the lower index present in the given data up to and including 4.

## Value Filters

> ⚠️ **To be further specified**

Value filters are expressions used to filter the results of a `read` operation, and specify which results should be returned. Value filters operate on materialized columns, including `soma_joinid`, and will not filter pseudo-columns such as `soma_rowid`.

The specific means to create and manipulate a value filter is delegated to per-language specifications. This specification uses a pseudo-language for _examples only_.

Value filter expressions will have the following capabilities:

- per-column filter expressions which define:
  - a column name
  - a comparison operator, supporting ==, !=, <, >, <=, >=
  - and a constant
- compound expressions combining other expressions with AND and OR boolean operations

Examples, using a pseudo-syntax:

- `col_A > 0`
- `(col_A > 0) AND (col_B != "deleted")`

## Platform-Specific Configuration

Many operations include a `platform_config` parameter. This parameter provides a generic way to pass storage-platform–specific hints to the backend implementation that cannot effectively be exposed in SOMA’s generic, platform-agnostic API. End users and libraries can use these to tune or otherwise adjust the behavior of individual operations without needing to know exactly which backend is being used, or directly depending upon the storage platform implementation in question.

The `platform_config` parameter is defined as a key–value mapping from strings to configuration data. Each **key** in the mapping corresponds to the name of a particular SOMA implementation (i.e., the same string returned by the `get_storage_engine` call). The value stored in each is implementation defined. For example, a Python library that handles SOMA dataframes would make a call that looks roughly like this:

```python
def process(df: somabase.DataFrame) -> ...:
    # ...
    results = df.read(
        ...,
        platform_config={
            "tiledb": {
                # TileDB-specific read config settings go here.
            },
            "otherimpl": {
                # OtherImpl-specific read config settings go here.
            },
        },
    )
```

When a SOMA DataFrame is passed into this code, the function does not need to care whether the dataframe in question is TileDB-based, OtherImpl-based, or otherwise; each platform will read the configuration necessary to tune its own reading process (and in other cases, the storage backend will simply use the default settings).

> TODO: Add discussion of a Context type and how that will fit in with the `platform_config`.

### Configuration data structure

The exact contents of each platform’s entry in the configuration mapping are fully specified by that platform’s implementation itself, but it should conform to certain conventions. While the specification or its generic implementation cannot *enforce* these guidelines, following them will ensure that API users have a consistent and predictable interface.

- At the top level, each individual platform’s configuration should be a string-keyed mapping.
  - In Python, these keys should be `snake_case`.
- The contents of these configuration entries should be represented declaratively, using built-in data structures from the host language to the extent possible (for example, strings, dicts, lists and tuples, etc. in Python). This allows libraries that use SOMA objects to provide configuration data to multiple platforms without having to depend upon implementation it *may* want to use.
  - An implementation may also use objects and types from libraries that the generic SOMA interface specification uses, like Arrow types.
  - For highly-specialized cases, a storage platform implementation may also accept its internal object types. However, to the extent possible, using platform-specific objects should be an option *in addition to* a fully delcarative structure, and should *not* be the *only* way to provide configuration data.
- In situations where a configuration setting of the same name, but with different type, semantics, or values will be used across operations, a separate string key should be provided for that setting for each operation. This allows for the same `platform_config` data to be reused across multiple operations by the user.
  - For example, a storage backend may provide a way to read and write data in a given block size. However, the performance characteristics of these operations may be very different. The implementation should provide `read_block_size` and `write_block_size` parameters (or use some similar disambiguation strategy) rather than only allowing a single `shard_size` parameter.

### Implementation and usage guidelines

The configuration passed in the `platform_config` object is intended for operation-specific tuning (though it may make sense for user code to use the same `platform_config` across multiple operations). A `platform_config` should only be used for the operation it was provided to (and to directly dependent operations); it should not be stored for later calls. Environmental configuration (like login credentials or backend storage region) should be provided via the (to-be-defined) Context object.

Operations should not *require* a `platform_config` entry to complete; the platform should use a sensible default if a given configuration value is not provided. Required environmental data generally belongs in the Context object.

A platform should only ever examine its own entry in the `platform_config` mapping. Since the structure and contents of each entry is wholly implementation-defined, one platform cannot make any assumptions at all about another’s configuration, and for predictability should avoid even trying to extract any information from any other configuration entries.

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
26. \_\_rowid changed to soma_rowid. Use `soma` and `SOMA` as "reserved" prefixes.
27. Various editorial clarifications
28. Clarify distinction between soma_rowid pseudo-column and soma_joinid column.
29. Split indexed/non-indexed dataframe into two types to clarify differing indexing/slicing semantics, and the existence of the soma_rowid pseudo-column only in non-indexed dataframes.
30. Most use of Arrow RecordBatch updated to be a Table, as this allows for chunked arrays (larger objects).
31. Clarify that read operations can accept a "list of scalar" in the form of an Arrow Array or ChunkedArray
32. Clarify the return value of `get schema` operation for NdArray types.
33. Clarified the function name returning the SOMA API version (`get_SOMA_version`), and bumped API version to `0.2.0-dev`
34. All offset types (soma_rowid, soma_joinid) changed from uint64 to positive int64.
35. Remove `reshape` operation from the NdArray types.
36. Clarify type conformance and promotion
37. NdArray COO column names - add `soma` prefix to move all names into the reserved namespace.
38. Clarify explicit nature of soma_rowid/soma_joinid handling throughout.
39. Renamed `type` fields to `soma_type`.
40. Remove SOMADataFrame; rename SOMAIndexedDataFame to SOMADataFrame
41. Add description of `platform_config` objects.
