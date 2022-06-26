# Introduction

> **Version**: 20220625T150000 [bkm]. Status: brainstorming, pre-proposal, uncirculated
>
> ℹ️ **Note** - this is an early draft and has not had any review or circulation. It may contain controversial, undecided, or just plain wrong-headed ideas. I expect several iterations will be required to converge the underlying primitives with use cases. Please see `issues` noted throughout the doc for a list of active discussions/debates. In particular, this doc has known gaps in:
>
> - multi-modal support - modelling is still in active requirements identification
> - incremental/streaming reads/queries - will be critical for large datasets
> - the team's desired tradeoffs between flexibility and higher level conventions
> - and more...?

The goal of SOMA (“stack of matrices, annotated”) is a flexible, extensible, and open-source API providing access to annotated, 2D matrix data stored in multiple underlying formats and systems. The vision for this API family includes:

- support for accessing data from persistent, cloud-resident datasets,
- enable use within popular data science environments (eg, R, Python), using the tools of that environment (eg, Python Pandas integration),
- enable access to data aggregations much larger than single-host main memory
- provide a building block for higher-level API that may embody domain-specific conventions or schema around annotated 2D matrices (eg, a cell "atlas").

The SOMA data model is centered on annotated 2-D matrices, conceptually similar to data structures embedded within existing single-cell data models including Seurat Assay, Bioconductor SingleCellExperiment, and ScanPy AnnData. Where possible, the SOMA API attempts to be general purpose and agnostic to the specifics of any given environment, or to the specific conventions of the Single Cell scientific ecosystem.

SOMA is an abstract _API specification_, with the goal of enabling multiple concrete API implementations within different computing environments and data storage systems. SOMA does not specify an at-rest serialization format or underlying storage system.

This document is attempting to codify the abstract, language-neutral SOMA data model and functional operations. Other specifications will document specific language bindings and particular storage system implementations.

# Data Model

The abstract data model comprises three "core" data types, and one specialization intended to improve ease of use and interoperability. The core types are:

- SOMACollection - a string-keyed container (key-value map) of other SOMA data types, eg, SOMADataFrame, SOMAMatrix and SOMACollection.
- SOMADataFrame - a 1-D, string-indexed, multi-column table, with monomorphic columns of equal length -- essentially a single-index dataframe.
- SOMAMatrix - a 2-D, sparse, string-indexed multi-column matrix, with monomorphic columns of equal length -- essentially a two-index dataframe.

In addition, a convenience type is defined:

- SOMA - a specialization and extension of SOMACollection, codifying a set of naming and indexing conventions to represent an annotated, 2-D matrix of observations across a well-defined set of variables.

In this document, the term `dataframe` implies something akin to an Arrow `RecordBatch`, R `data.table` or Python `pandas.DataFrame`, where:

- dimensions are string-indexed
- multiple columns may exist, each with a string column name
- all columns are individually typed, monomorphic, and contain simple types (eg, int64)
- all columns are of equal length

All SOMA data objects are named with URIs.

> ⚠️ **Issue** -- this section would benefit from a data model diagram, helpfing visualize the relationships between the types.

> ⚠️ **Issue** -- the use of `SOMA` to name the API _and_ a data type is confusing. We should consider a new name for the aforementioned SOMA _type_. _Candidate:_ `SOMAAnnotatedMatrix`?

## Base Type System

The SOMA API borrows its base type system from the Arrow language-agnostic in-memory system for data typing and serialization ([format](https://arrow.apache.org/docs/format/Columnar.html)). The SOMA API is intended to be used with an Arrow implementation such as [PyArrow](https://arrow.apache.org/docs/python/) or the [Arrow R package](https://arrow.apache.org/docs/r/), or other libraries which interoperate with Arrow (eg, Pandas).

Where SOMA requires an explicit typing system, it utilizes the Arrow types and schema. SOMA has no specific requirements for the type or serialization system used by the underlying storage engine, other than it be capable of understanding and representing the Arrow types. It is understood and expected that each implementation of SOMA will have data type expressiveness limits (eg, just because you can express a type in he Arrow type system does not mean all SOMA implementations will understand it).

In the following doc:

- `primitive` types in this specification refers to Arrow primitive types, eg, `int32`, `float`, etc.
- `string` refers to Arrow UTF-8 variable-length `string`, ie, `List<Char>`.
- `simple` types include all primitive types, plus `string`.

Other Arrow types are explicitly noted as such, eg, `Arrow.RecordBatch`.

> ⚠️ **Issue** - is the use of Arrow as a base type language acceptable? There are others, up to and including inventing a new system, but it seemed prudent to adopt an existing, language neutral specification, which is already supported by many "engines".

> ⚠️ **Issue** - are there parts of the Arrow type system that we wish to _explicitly exclude_ from SOMA? I have left this issue open (ie, no specific text) for now, thinking that we can come back and subset as we understand what complex types are required, and how much flexibility should be in this spec. We clearly need some complex types (eg, RecordBatch, List, etc) as they are implied by `string`, etc. My own preference would be to mandate a small set of primitive types, and leave the rest open to implementations to support as they feel useful.

## Metadata (uns)

All SOMA objects may be annotated with a small amount of metadata, in the form of a simple key/value map:

- `uns` (map[string, simple]) - string-keyed mapping to any **simple** type (eg, int32, string, etc).

Only `simple` types are supported in the metadata values. The metadata lifecycle is the same as its containing object, eg, it will be deleted when the containing object is deleted.

> ⚠️ **Issue** - `uns` - do we need more complex typing for uns values, and if so, how to represent capture what can is required to be supported? (eg, anything Arrow can represent? a subset?)
>
> **Proposal**: restrict `uns` to a mapping of string keys and `simple` values. Extend to complex types in the future as we have concrete use cases which warrant the complexity.

> ⚠️ **Issue** - the name `uns` is not really all that suggestive. **Proposal:** rename `uns` to `metadata`, eg, `print(soma.metadata['version'])`

## SOMACollection

SOMACollection is an unordered, `string`-keyed map of values of type SOMADataFrame, SOMAMatrix, SOMACollection or SOMA. SOMACollection objects are typically persistent, and may be nested to any level (eg, SOMACollection may contain other SOMACollection objects). Keys in the map are unique and singular (no duplicates, ie, it is not a multi-map).

## SOMADataFrame

SOMADataFrame is a 1-D multi-column table of monomorphic arrays, all of equal length -- ie, a "dataframe". The SOMADataFrame has a user-defined schema, which includes:

- a table schema, expressed as an `Arrow.RecordBatch` type, defining number of columns, and their respective names and types
- the index column name

A SOMADataFrame must contain at least a single column which is the named index column. The index column _must_ be of `string` type. Index values are non-null and must be unique (ie, no duplicates are allowed) within the object. The index is sparse and unordered, ie, supported indexing is by ID value only, with no indexing order or positional (offset-based) indexing.

Most language-specific implementations will present SOMADataFrame in more convenient forms, such as Python `pandas.DataFrame`, R `data.frame` or other environment-specific data structures. Specific implementations of the SOMA API may extend this type with convertors to/from the underlying data structure, and enforce indexing conventions.

> ⚠️ **Issue** - this spec requires that index column is a `string` type. Most underlying "engines" will support more flexibility. Do we want to enable that flexibility, or stick with requiring string for simplicity/commonality?

## SOMAMatrix

SOMAMatrix is a 2-D multi-column table of monomorphic arrays, ie, a "dataframe" with two index dimensions. SOMAMatrix is an extension of SOMADataFrame, with two indexing dimensions. The SOMAMatrix has a user-defined schema, which includes:

- a table schema, expressed as an `Arrow.RecordBatch` type, defining the number of columns, and their respective names and types
- the _primary_ index column name
- the _secondary_ index column name

A SOMAMatrix must contain (minimally) two columns which are the primary and secondary index columns. The index columns _must_ be of `string` type. Index values are non-null and must be unique (ie, no duplicates are allowed) within the object. The index is sparse and unordered, ie, supported indexing is by ID value only, with no indexing order or positional (offset-based) indexing.

> ⚠️ **Issue** - SOMAMatrix and SOMADataFrame differ only in the number of dimensions (2 vs 1 respectively). Should they be unified into a single type object/API of more general nature? Clarity vs flexibility?

## SOMA

The SOMA type is a specialized SOMACollection, representing an annotated 2-D matrix of observations across a set of variables. The SOMA composes SOMACollection, SOMADataFrame and SOMAMatrix types using a set of predefined fields (keys & values), to represent the annotated matrix. Each predefined field in the SOMA has a well-defined type, dimensionality and indexing convention. Other user defined data may be added to a SOMA, as a SOMA is a specialization of a SOMACollection.

Implementations _should_ enforce the naming and indexing constraints on these pre-defined fields. Pre-defined fields are distinguished from other user-defined collection elements, where no schema or indexing semantics are presumed or enforced.

The predefined fields within SOMA share common indices and `shape`:

- obs_id - the observation, a `string` type
- var_id - the variable, a `string` type

SOMA pre-defined fields are principally differentiated by:

- dimensionality, eg, 1-D (SOMADataFrame) or 2-D (SOMAMatrix)
- index column names, `obs_id` or `var_id` or both

The pre-defined fields are:

| Field name | Field type                              | Field description                                                                                                                                                                                                                                               |
| ---------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `obs`      | `SOMADataFrame`                         | Primary annotations on the _observation_ axis. Must be of length #observations (ie, every observation _must_ be defined in this field), and must contain and be indexed by the `obs_id` column. The contents of `obs_id` define the _observation_ index domain. |
| `var`      | `SOMADataFrame`                         | Primary annotations on the _variable_ axis. Must be of length #variables (ie, every variable _must_ be defined in this field), and must contain and be indexed by the `var_id` column. The contents of `var_id` define _variable_ index domain.                 |
| `obsm`     | `SOMACollection[string, SOMADataFrame]` | Secondary _observation_ annotations, indexed with `obs_id`                                                                                                                                                                                                      |
| `varm`     | `SOMACollection[string, SOMADataFrame]` | Secondary _variable_ annotations, indexed with `var_id`                                                                                                                                                                                                         |
| `obsp`     | `SOMACollection[string, SOMAMatrix]`    | Pairwise _observation_ annotations, indexed with `[obs_1_id, obs_2_id]`                                                                                                                                                                                         |
| `varp`     | `SOMACollection[string, SOMAMatrix]`    | Pairwise _variable_ annotations, indexed with `[var_1_id, var_2_id]`                                                                                                                                                                                            |
| `X`        | `SOMACollection[string, SOMAMatrix]`    | Sparse observations on a variable, indexed by `[obs_id, var_id]`                                                                                                                                                                                                |

The `obs_id` domain for `obsp`, `obsm` and `X` (primary dimension) are the values defined by the `obs` SOMADataFrame `obs_id` column. The `var_id` domain for `varp`, `varm` and `X` (secondary dimension) are the values defined by the `var` SOMADataFrame `var_id` column. In other words, all predefined fields in the SOMA share a common `obs_id` and `var_id` domain, which is defined by the contents of the respective columns in `obs` and `var` SOMADataFrames.

As with other SOMACollections, the SOMA also has a `metadata` field, and may contain other user-defined elements.

### SOMA field constraints

The following naming and indexing constraints are defined for the SOMA:

| Field name              | Field constraints                                                                                                                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _all predefined fields_ | Index column(s) are of type `string`                                                                                                                                                     |
| obs, var                | Field value type is `SOMADataFrame`                                                                                                                                                      |
| obsm, varm              | Field value type is a `SOMACollection`, where each element in the collection has a value of type `SOMADataFrame`                                                                         |
| obsp, varp , X          | Field value type is a `SOMACollection`, where each element in the collection has a value of type `SOMAMatrix`                                                                            |
| obs, obsm               | Index column name is `'obs_id'`. All `obs_id` values exist in the `obs_id` column of the `obs` field.                                                                                    |
| var, varm               | Index column name is `'var_id'`. All `var_id` values exist in the `var_id` column of the `var` field.                                                                                    |
| obsp                    | Index column names are `['obs_1_id', 'obs_2_id']`. All `obs_1_id` and `obs_2_id` values exist in the `obs_id` column of the `obs` field.                                                 |
| varp                    | Index column names are `['var_1_id', 'var_2_id']`. All `var_1_id` and `var_2_id` values exist in the `var_id` column of the `var` field.                                                 |
| X                       | Index column names are `['obs_id', 'var_id']`. All `obs_id` values exist in the `obs_id` column of the `obs` field. All `var_id` values exist in the `var_id` column of the `var` field. |

> ⚠️ **Issue** `raw` -- do we need `raw.X` and `raw.var` at all, or can we model them with existing structures? **Proposal**: the current `X` and `varm` can represent typical `raw` semantics (filtered subset, or transformed values). Assume that higher level usage conventions will utilize these to represent raw, eg, `X['raw']` and `varm['raw']`, or alternatively by adding additional columns to `var` that indicate filtering status.

> ⚠️ **Issue** `obsm` and `varm` schema -- if these are RecordBatches indexed by obs_id / var_id, then they are essentially identical to obs/var slots. Are they necessary, or can we represent obsm/varm with conventions layered on top of obs/var? if they are different, how? The only current difference is that `obs` and `var` are required to have an entry for each value on that dimension, whereas `obsm`/`varm` do not require all dimension IDs to exist (ie, they are sparse like X). **Proposal**: retain, but differentiate by considering obsm/varm as secondary annotations on the axis, which do **not** require a value for each obs_id/var_id (ie are **sparse**).

> ⚠️ **Issue** `obsm` and `varm` names - field inspiration and name were borrowed from AnnData, but are misleading in this context as both are essentially a collection of SOMADataFrame values, not a collection of dense "matrix" in the AnnData sense. We should consider renaming them. While they can express the typical use case of AnnData.obsm/varm, they are better thought of as a collection of DataFrame containing secondary annotations for the obs/var axis. Possible ideas for better names: obsd/vard ('d' as in dataframe), obs_axis/var_axis, "axis annotation layers", or?

# Functional Operations

The SOMA API includes functional capabilities around the [SOMA data model](#datamodel.md). The specifics of how these operations manifest in any given language and computing environment is defined in per-language specifications (**to be created**), but each implementation will minimally support the functional operations defined here. For example, it is likely that a Python implementation will prefer `__getattr__` over an explicit `get()` method, and will add other Pythonic functionality to facilitate use.

As any given storage "engine" upon which SOMA is implemented may have additional features and capabilities required to support advanced use cases, it is expected that SOMA implementations will expose engine-specific features. Where possible, these should be implemented to avoid conflict with future changes to the common SOMA API.

> ⚠️ **Issue** - this spec needs to provide guidance on HOW to do that. Fro example, can we carve out some namespace for extensions in the functional API?

In the following, a pseudo-object-oriented syntax is used, eg, `obj.op()` is calling `op()` upon `obj`. Where a type is used, eg, SOMA.op(), it is a `static` operation (ie, no state other than parameters provided).

> ℹ️ **Note** - this section is just a sketch. Primarily focused on adding pseudo-signatures for any primitive operation that must exist on each type.

## SOMAMapping interface

> ℹ️ **Note** - this is an interface defined only to make the subsequent prose simpler. It is not a primary element in the data model.

The SOMAMapping is a string-keyed map. It may be immutable or mutable depending on the context. In most implementations, it will be presented with a language-appropriate interface, eg, Python `Mapping` or `MutableMapping`.

The following operations manipulate the mapping, providing a getter/setter interface plus the ability to iterate on the collection:

```
  mapping.get(string key) -> value
  mapping.has(string key) -> bool
  mapping.set(string key, simple value) -> void
  mapping.del(string key) -> void
  mapping.__iterator__
  mapping.__length__
```

> ⚠️ Issue - do we need a "is_readonly" or "is_immutable" attribute, or assume user can figure it out from the context?

> ℹ️ **Note** - it is possible that the data model will grow to include more complex value types. If possible, retain that future option in any API defined.

## SOMACollection

In the following, `soco` refers to an SOMACollection instance or handle.

```
SOMACollection.create(uri) ->
SOMACollection.open(uri, mode=read|write) -> soco
SOMACollection.delete(uri) -> void
SOMACollection.exists(uri) -> bool   # exists and is a SOMACollection
soco.close()
soco.uns -> metadata as a SOMAMapping
```

> ⚠️ **Issue** - do we need a specific open/close API, or is the object stateless? Or is that language/environment-specific?

Collection operations include access to the collection using the SOMAMaping interface:

```
type ValueType = SOMACollection | SOMADataFrame | SOMAMatrix

soco.get(string key) -> ValueType
soco.has(string key) -> bool
soco.set(string key, ValueType value)
soco.del(string key) -> void
soco.__iterator__ -> key/value iterator for collection
soco.__length__ -> int
```

## SOMADataFrame

> 🛑 **To be further specified** -- methods need additional specification.

In the following, `sdf` is used to indicate an "instance" or "handle" to a SOMADataFrame.

Summary:

```
SOMADataFrame.create(string uri, Arrow.Schema schema, string index_column_name) -> void

SOMADataFrame.delete(string uri) -> void
SOMADataFrame.exists(string uri) -> bool  # exists and is a SOMADataFrame
SOMADataFrame.open(string uri, mode=read|write) -> sdf
sdf.close()

sdf.shape -> (int, )                      # length of each index dimension, always a list of length 1
sdf.ndims -> 1                            # returns a constant
sdf.schema -> Arrow.Schema                # data schema, which must be the schema for an Arrow.RecordBatch
sdf.index_column_names -> (string, )      # list of index column names, always a list of length 1

sdf.read(ids=[...]|all, column_names=[...]|all, filter=_TBD_) -> Arrow.RecordBatch
sdf.write(Arrow.RecordBatch values)          # write
```

### Method: create()

Create a new SOMADataFrame with user-specified URI and schema. If the schema includes unsupported types, an error will be raised.

```
SOMADataFrame.create(string uri, Arrow.Schema schema, string index_column_name) -> void
```

Parameters:

- uri - location at which to create the object
- schema - an Arrow.RecordBatch type defining all column schema, including the index columns
- index_column_name - the name of the index column (eg, 'obs_id')

### Method: read()

Read a user-defined subset of data and return as an Arrow.RecordBatch. User-provided parameters specify the index values (`ids`), which columns to read, and column filters to apply. There is no guarantee of result ordering.

```
sdf.read(ids=[`string`, ...]|all, column_names=[`string`, ...]|all, ValueFilter filter=_TBD_) -> Arrow.RecordBatch
```

Parameters:

- ids - list of indices to read. Defaults to 'all'
- column_names - the named columns to read and return. Defaults to all.
- filter - [value filter](#value-filters) to apply (_TBD_). Defaults to no filter.

> ⚠️ **Issue** - sdf.read() needs further definition for:
>
> - incremental/streaming queries - critical gap
> - result ordering - would be useful, but also adds complexity (order by index? order by column value?). Most useful for streaming queries where the total result may be too large to load into memory and sort.
> - filtering based upon values - need to write the section: [Value Filter](#value-filters)

> ℹ️ **Note** -- with this definition for read(), it should be possible to implement the equivalent of the higher level functions in the current prototype:
>
> - ids() -- read(ids=all, column_names=['the index column name, eg, obs_id'])
> - query()/attribute_filter() -- read(column_names=['ids', 'a_col'], filter='a_col == "foobar"')

### Method: write()

Write an Arrow.RecordBatch to the persistent object. As duplicate index values are not allowed, index values already present in the object are overwritten and new index values are added.

```
sdf.write(Arrow.RecordBatch values)          # write
```

Parameters:

- values - an Arrow.RecordBatch containing all columns, including the index column. The schema for the values must match the schema for the SOMADataFrame.

## SOMAMatrix

> 🛑 **To be further specified** -- will look essentially the same as SOMADataFrame, extended with a second index dimension.

In the following, `smx` is used to indicate an "instance" or "handle" to a SOMAMatrix.

Summary:

```
SOMAMatrix.create(string uri, Arrow.Schema schema, string index_column_name) -> void

SOMAMatrix.delete(string uri) -> void
SOMAMatrix.exists(string uri) -> bool  # exists and is a SOMADataFrame
SOMAMatrix.open(string uri, mode=read|write) -> smx
smx.close()

smx.shape -> (int, int)                     # length of each index dimension, always a list of length 2
smx.ndims -> 2                              # returns a constant
smx.schema -> Arrow.Schema                  # data schema, which must be the schema for an Arrow.RecordBatch
smx.index_column_names -> (string, string)  # list of index column names, always a list of length 2

smx.read(ids=[...]|all, column_names=[...]|all, filter=_TBD_) -> Arrow.RecordBatch
smx.write(Arrow.RecordBatch values)          # write
```

## SOMA

SOMA supports all SOMACollection functions, including access to the predefined fields (eg, `X`) using SOMACollection API. The primary difference in behavior between a SOMACollection and a SOMA is that the SOMA _should_ enforce naming and indexing conventions for the predefine fields (eg, `obs`), as define in the [SOMA data model](#soma).

Summary:

```
SOMA.create(uri) -> soma
SOMA.open(uri, mode=read|write) -> soma
SOMA.delete(uri) -> void
SOMA.exists(uri) -> bool   # exists and is a SOMA
soma.close()
soma.uns -> metadata

type ValueType = SOMACollection | SOMADataFrame | SOMAMatrix

soma.get(string key) -> ValueType
soma.has(string key) -> bool
soma.set(string key, ValueType value)
soma.del(string key) -> void
soma.__iterator__ -> key/value iterator for collection
soma.__length__ -> int
```

## General Utilities

Summary:

```
get_version() -> string                   # return semver-compatible version of the supported SOMA API
get_implementation() -> string            # return the implementation name, eg, "R-tiledb"
get_implementation_version() -> string    # return the package implementation version as a semver
get_storage_engine() -> string            # return underlying storage engine name, eg, "tiledb"
```

### Method: get_SOMA_version

This is a pre-release specification in active development. As defined by [semver](https://semver.org/), this API is defined as version `0.0.0-dev`.

## Value Filters

> 🛑 **To be specified** -- a string-based language which can express simple filters and filter combinations based on column values, eg, "col_name == 'value'".

# Other

> ⚠️ **Issue** language bindings - we need to define the base-level language bindings for Python & R, _somewhere_...
