glio
====

A Python package for Gadget-like I/O. It provides a basic interface for reading
and writing Gadget-like snapshot files from and to file.

New file types may be added by defining a schema for the header and block data,
and subclassing `SnapshotBase` (or one of its subclasses). See for example
`GadgetSnapshot` in `gadget.py`.

To load a Gadget-2 data file,

```python
>>> import glio
>>> s = glio.GadgetSnapshot('filename')
>>> s.load()
```

and similarly for the `SPHRAYSnapshot` class. Header data is accessible as

```python
>>> s.header.header_item
```

where valid `header_item` attributes are defined by the current class' header
schema. They can also be obtained as a list of strings, or looped through,

```python
>>> s.header.fields
['npart', 'mass', ... ]
>>> for (name, value) in s.header.iterfields():
>>>    # Do something with header data.
```

Block data is accessed similarly, and can be iterated over similarly,

```python
>>> s.fields
['pos', 'vel', ... ]
>>> for (name, field) in s.iterfields():
>>>     # Do something with block data.
```

Each block data (`field` above) is a list, with each index `i` corresponding to
that block's particle data for Gadget particle type `i`. When reading from file,
if a block contains no data for a particle type `i`, an empty numpy.ndarray is
set for that particle type in the list; if a particle type is not valid for the
block, `None` is set.

A snapshot can be written to file, optionally with a new filename,

```python
>>> import glio
>>> s = glio.GadgetSnapshot('filename')
>>> # Double all gas-particle smoothing lengths.
>>> s.hsml[0] *= 2
>>> s.fname = 'new_filename'
>>> s.save()
```
