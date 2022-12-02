# Reorganizing SOMA APIs for ephemeral vs. durable collections

The current SOMA APIs somewhat combine together two layers of operation: the **storage interface** and the **behavior** of SOMA objects.
Looking at the existing implementations of [Experiment](https://github.com/single-cell-data/TileDB-SOMA/blob/be365f0bc85ee07398c4ebb64268c1a14ed7ad51/apis/python/src/tiledbsoma/experiment.py) and [Measurement](https://github.com/single-cell-data/TileDB-SOMA/blob/be365f0bc85ee07398c4ebb64268c1a14ed7ad51/apis/python/src/tiledbsoma/measurement.py), there is nothing TileDB-specific there—they are just additional convenience behaviors around collections that are technically independent of the storage implementation itself.
Decoupling these **client-side semantics** from the **backend storage** will allow us to achieve several goals:

  - Users can analyze durable collecions of data (those stored in one location, like a single TileDB Group) but can also assemble their own collections from any SOMA-formatted data sources they have access to.
  - The frontend behaviors associating data across multiple sources (like multiple distinct TileDB Arrays) can be implemented *once* by the base SOMA implementation, rather than having duplicative work across implementations.
  - The backend can more predictably pass implementation-specific context around, since it will *only* ever have to deal with concrete storage, and it can assert “ownership” over everything it creates.

This proposal combines both the [ephemeral/durable collection separation](https://docs.google.com/document/d/1D0VC90_vZtuLqaC4XWA3GO34WVAObYlodQYDLdLqLFY/edit) previously discussed and the [“context” idea](https://github.com/single-cell-data/TileDB-SOMA/issues/322#issuecomment-1276547412) into one, since while they are somewhat distinct, together they provide more benefits than either alone.

## Context

A `Context` is an opaque object containing durable configuration data that will last over the course of the session.
Each implementation defines its own Context type, which a user can set up.
The implementation can use this context object as it sees fit for the its lifetime.
Other code (e.g. third-party libraries) will usually never have to handle it directly, but if it does, it should just pass the context unchanged rather than attempting to introspect it, particularly since there is no guarantee of what a context will be.

Examples of data that would go into a Context type include:

  - Login credentials
  - Semi-global storage configuration (API endpoints, etc.)
  - More?

Concrete SOMA storage classes (e.g. the TileDB implementation of `SOMACollection`) keep a reference to the context they were created with.
When one of these objects “spawns” another related object, the child object has the same context as the parent.
For instance, if the user creates a `Collection`, and they then create a `DataFrame` within that collection, the `Collection` would pass its context to the `DataFrame` as part of creating it.

(While [TileDB has a `Ctx` type](https://tiledb-inc-tiledb.readthedocs-hosted.com/projects/tiledb-py/en/stable/python-api.html#context), the type the TileDB SOMA implementation uses as a `Context` may not necessarily be a `tiledb.Ctx`.)

## Separating ephemeral from durable collections

### Ephemeral collections

The base SOMA package introduces a concrete implementation of the `SOMACollection` interface that exists solely in-memory.
For instance, in Python, this would be handled as a simple `dict` with the additional SOMA behaviors on top of it.

`SimpleCollection` implements `SOMACollection`:

  - `[key: str] -> SOMAObject`: Gets the entry in the collection.
  - `[key: str] = val: SOMAObject`: Sets the entry in the collection with some SOMA value.
  - `delete [key: str]`: Removes the entry from the collection.
  - `get metadata -> MetadataMapping`: Returns a mutable string-to-string dictionary representing this collection’s metadata. This dictionary is only stored internally.
  - `get soma_type -> str`: `SOMACollection`

### Durable collections

Durable collections are represented by a new `StoredCollection` interface.
These differ from ephemeral collections in that they *own* the objects inside of them and you cannot freely assign to them.

interface `DurableCollection` extends `SOMACollection`:

  - `[key: str] -> SOMAObject`: Gets the entry in the collection. This represents loading the object out of its storage.
  - `[key: str] = val: SOMAObject`: **Possibly invalid.** Since this collection represents a durable mapping, objects must be added to it by the collection creating them itself, so that it owns the child object and is in sync with its stored state. If the collection type supports adding arbitrary elements this way, it can choose to implement this.
  - `delete [key: str]`: Removes the entry from the collection. Depending upon the implementation, this may delete the backing storage entirely, or simply unlink the given entry from the collection.
  - `get metadata -> MetadataMapping`: Returns a mutable string-to-string dictionary representing this collection’s metadata. Writing to this *updates stored metadata*.
  - `create_ndarray(key: str, uri: str, density: Density, dtype: primitive, platform_config: PlatformConfig) -> NDArray`: Creates a child NDArray.
  - `create_dataframe(key: str, uri: str, schema: arrow.Schema, platform_config: PlatformConfig) -> DataFrame`: Creates a child DataFrame. (TODO: how to separate indexed vs. non-indexed?)
  - `create_collection(key: str, uri: str, platform_config: PlatformConfig) -> DurableCollection`: Creates a durable child collection.

The URI passed in is optional and may not be needed if the storage engine constructs the URI based on the key (e.g., a storage system that uses the filesystem might say that the path of a child of a collection is just `collection_uri/child_key`).

The collection itself is agnostic to the type of data that is stored therein.

### Experiments and Measurements by composition

The current version of the specification uses inheritance, not composition to specify the `Experiment` and `Measurement` classes.
The creation of the `SimpleCollection` type means that the base SOMA implementation should instead provide a concrete `Experiment` and `Measurement` that, rather than being *subtypes* of the `SOMACollection` type, are instead layers atop the type, which can sit atop any storage interface.
These two classes still provide proxy methods to the storage implementation they sit on top of, but otherwise offer a layer on top of them:

#### Experiment

The Experiment object is a concrete type provided by the base SOMA implementation.
A user can create an experiment by providing it a `SOMACollection`.

  - `storage: SOMACollection`: The backing storage for the collection.
  - `get obs -> DataFrame`: Returns the `obs` element of the backing collection.
  - `get ms -> Measurements`: Returns a wrapper around the `ms` element of the backing collection.
  - General SOMA collection methods are proxied to the backing storage and have the same features as calling the backing storage directly.
    - `[key: str] -> SOMAObject`
    - `[key: str] = val: SOMAObject`
    - `delete [key: str]`
    - <code>create_<i>whatever</i></code>

A basic sketch of a Python implementation (to be provided by `somabase`) looks like:

```python
class Experiment:
  # __init__ takes a SOMACollection and assigns it to self.storage.

  @property
  def obs(self) -> DataFrame:
    return DataFrame(self.storage["obs"])

  @property
  def ms(self) -> Measurements:
    return Measurements(self.storage["ms"])

  def __getitem__(self, key: str) -> ...:
    return self.storage[key]

  # setitem and delitem work similarly
```

#### Measurement

Likewise, the `Measurements` (note the `s`) type is a proxy over a `SOMACollection` containing multiple measurement `SOMACollection`s:

  - `storage: SOMACollection`: The backing storage for the collection.
  - `[key: str] -> Measurement`: Returns a `Measurement` object wrapping the specific element of the collection.
  - `[key: str] = val: Measurement`: Sets the measurement, *if supported*.
  - `delete [key: str]`: Removes the measurement.
  - `create_measurement(...)`: Creates a new child `Measurement` collection in backing storage, if applicable.

```python
class Measurements:

  def __init__(self, storage: SOMACollection):
    self.storage = storage

  def __getitem__(self, key: str) -> Measurement:
    return Measurement(self.storage[key])

  def __setitem__(self, key: str, value: Measurement):
    self.storage[key] = value.storage

  # This could also be named `add`.
  def create_measurement(self, ...) -> Measurement:
    new_collection = self.storage.create_collection(...)
    # add necessary members to the collection with
    # new_collection.create_whatever
    return Measurement(new_collection)

  # ...
```

And a single `Measurement` is a proxy over a `SOMACollection`:

```python
class Measurement:

  def __init__(self, storage: SOMACollection):
    self.storage = storage

  # getitem, setitem, etc. straightforward proxies
  # also add typed accessors for x, varm, varp, etc.
```

## Other notes

`Density` is an enum `{SPARSE, DENSE}`.

## Examples

These examples present a fictional `vsoma` implementation to represent what calls to a general SOMA implementation will do.

### Creating new SOMA objects in backing storage

```python
# This creates the backing storage and structure for a new Experiment and
# returns the experiment itself, opened for writing.
#
# For instance, this would create the backend collection itself and the `obs`
# and `ms` sub-elements of the collections.
#
#     TODO: Should this method create the `obs` and `ms` elements, or should
#     we have `create_obs(...)` and `create_ms(...)` methods?
#
# Because the somabase Experiment class is just a wrapper around a
# SOMACollection (here embodied by the `vsoma.SOMACollection` implementation),
# we tell vsoma that we want to create an Experiment, and vsoma handles setting
# up the structure for it.
#
# For languages where types are not first-class, this could be implemented as
# `create_experiment`/`create_ndarray`/`create_dataframe`/etc. functions.
new_exp = vsoma.create(
    somabase.Experiment,
    "backend:///path/to/some/new/experiment",
    # Other options:
    # - platform_config
    # - context
    # - other platform-specific options
)

# new_exp is a somabase.Experiment with its `storage` being a vsoma
# SOMACollection.

# If we don't create the `obs` and `ms` collections directly in `.create`, here
# would be calls to `new_exp.create_obs(...)` and `new_exp.create_ms(...)`.

# Add a Measurement to the experiment. This again creates the storage skeleton
# of a Measurement as a `vsoma.SOMACollection` and returns a
# `somabase.Measurement` whose `storage` points to that collection.
#
# The Context of this Measurement (and of new_exp.ms) is the same as the Context
# of the new_exp, and measure_a is "owned" and its lifecycle is managed by
# new_exp.ms (which is in turn owned by new_exp).
measure_a = new_exp.ms.create_measurement(
    "measure_a",
    # Other creation options, e.g. platform_config, etc.
    # This can also include a `uri` parameter to allow for the case of where
    # a backend needs to know what the URI to create the object is.
)

# You can similarly recurse into measure_a, adding X, obsm/varm/varp/etc. tables
# and loading data into them. They all have the same Context as new_exp.

# This closes all the
new_exp.close()
```

### Opening an existing SOMA object

```python
# This locates and opens the named SOMA object, determines its type based on
# the stored metadata, and returns the appropriate object.
#
# For instance, if it is given the path to something that looks like an
# Experiment, it will open a vsoma collection and wrap it in a
# somabase.Experiment.
my_exp = vsoma.open(
    "backend:///path/to/existing/experiment",
    # Other options:
    # - platform_config
    # - context
    # - timestamp
    # - mode (default "r")
)

# Internally, this operates much like the above, but in read mode. This is how
# you would run queries on the experiment/measurements/etc. using the existing
# API we have already defined.
```
