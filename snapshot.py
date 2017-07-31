from copy import copy

import numpy as np

from .fortranio import FortranFile
from .snapview import SnapshotView

class SnapshotIOException(Exception):
    """Base class for exceptions in the the snapshot module."""
    def __init__(self, message):
        super(SnapshotIOException, self).__init__(message)

class SnapshotHeader(object):
    """
    A class for a Gadget-like header.


    Accessing header data
    ---------------------

    The header information from a header, hdr, can be accessed as,

        >>> hdr.header_entry_name

    where 'hdr_entry_name' can be any of the strings acting as keys of the
    schema dictionary for this header type. All valid keys are contained within
    the list hdr.fields.

    All (entry_name, entry_value) pairs may be iterated through using

        >>> for (name, data) in hdr.iterfields():
        >>>     # Do something


    Acccessing metadata
    -------------------

    The Snapshot file name with which this header is associated may be accessed
    as
        >>> hdr.fname
        'some_file_name'
    """
    def __init__(self, fname, header_schema):
        super(SnapshotHeader, self).__init__()
        self._fname = fname
        # Use copy so that reference schema is not altered.
        self._schema = copy(header_schema)
        self._fields = []
        self.verify_schema()
        self.init_fields()

    @property
    def fields(self):
        return self._fields

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, fname):
        self._fname = fname

    def init_fields(self):
        """Reset all header attributes to zero-like values."""
        for (name, fmt) in self._schema.items():
            dtype, size = fmt
            data = np.zeros(size, dtype=dtype)
            if size == 1:
                data = data[0]
            setattr(self, name, data)

    def iterfields(self):
        for name in self.fields:
            yield (name, getattr(self, name))

    def load(self):
        """Load the snapshot header from the current file."""
        with FortranFile(self.fname, 'rb') as ffile:
            self._load(ffile)

    def to_array(self):
        """Return a structured array representing the header data."""
        dtype = [(k, dt, size) for k, (dt, size) in self._schema.items()]
        values = tuple(getattr(self, name) for name in self.fields)
        return np.array(values, dtype=dtype)

    def save(self, fname=None):
        """
        Write the snapshot header to the current file, overwriting the file.

        A different file name to write to may optionally be provided. This
        does not modify the header's fname attribute, so later calling
        load() will re-load data from the original file.

        The method will raise a SnapshotIOException if the current header is
        not valid. See verify().
        """
        if fname is None:
            fname = self.fname

        if self.verify() != []:
            raise SnapshotIOException("Current header state invalid")

        with FortranFile(fname, 'wb') as ffile:
            self._save(ffile)

    def verify(self):
        """
        Return a list of header attributes which do not conform to the schema.

        An empty list indicates that the header is valid.
        """
        malformed = []
        for (name, fmt) in self._schema.items():
            dtype, size = fmt
            data = getattr(self, name)

            try:
                count = len(data)
            except TypeError:
                count = 1

            if count != size:
                malformed.append(name)
            else:
                try:
                    converted = np.asarray(data).view(dtype=dtype)
                except ValueError:
                    malformed.append(name)

        return malformed

    def verify_schema(self):
        """
        Verify the header formatter, and update it if necessary.

        When an element type is not supplied, it is assumed to be a 4-byte
        float.
        When an element length is also not supplied, it is assumed to be one.

        Completes the header schema if possible, else raises a
        SnapshotIOException exception.
        """

        self._ptypes = 0
        for (name, fmt) in self._schema.items():
            # So that these are defined even for an invalid formatter
            dtype, size = ('f4', 1)
            if len(fmt) == 2:
                dtype, size = fmt
            elif len(fmt) == 1:
                dtype, size = (fmt[0], 1)
            else:
                message = "Schema for header element '%s' is invalid" % name
                raise SnapshotIOException(message)

            try:
                dtype = np.dtype(dtype)
            except TypeError:
                # Given dtype does not correspond to a numpy dtype.
                message = "Data type for header element '%s' is invalid." % name
                raise SnapshotIOException(message)

            try:
                size = int(size)
            except TypeError:
                message = "Data size for header element '%s' is invalid." % name
                raise SnapshotIOException(message)

            if (dtype.itemsize * size) % 4 != 0:
                message = "Data bytes for header element '%s' not a multiple of 4" % name
                raise SnapshotIOException(message)

            self._schema[name] = (dtype, size)
            self._ptypes = max(size, self._ptypes)

        self._fields = self._schema.keys()

    def _load(self, ffile):
        raw_header = ffile.read_record('b1')
        offset = 0
        for (name, fmt) in self._schema.items():
            dtype, size = fmt
            bytewords = dtype.itemsize * size
            # Must be non-scalar ndarray, hence wrap in np.array()
            raw_data = np.array(raw_header[offset:offset + bytewords])
            try:
                data = raw_data.view(dtype=dtype)
            except ValueError:
                raise SnapshotIOException('Could not reinterpret')
            if size == 1:
                data = data[0]
            offset += bytewords
            setattr(self, name, data)

    def _save(self, ffile):
        array = self.to_array()
        ffile.write_ndarray(array)

class SnapshotBase(object):
    """
    A base class for a single Gadget-like simulation snapshot.

    This class defines general attributes, properties and methods for
    snapshot classes.  All snapshot types derive from this class.

    This class is not intended to be used directly. If implementing a subclass,
    it is most likely it should be a subclass of GadgetSnapshot, not this class.
    Subclasses will likely need to implement the _load_block() and
    _parse_block() methods.


    Acessing Arrays
    ---------------

    An array may be acessed from an instantiated SnapshotBase object, s, as,

        >>> array = s.block_name

    'block_name' can be any of the strings acting as keys of the schema
    dictionary for this snapshot type.  A list is returned, with one item for
    each particle type associated with this snapshot. If a particle type is not
    valid for this block, its entry in the list is None. Otherwise, it is a
    numpy.ndarray. For valid-but-empty particle data in a block, an empty
    numpy.ndarray is present. All valid keys are contained within the list
    s.fields.

    All (block_name, block_data) pairs may be iterated through using

    >>> for (name, data) in s.iterfields():
    >>>     # Do something


    Particle Type Aliases
    ---------------------

    If provied, particle type indices may be aliased to attributes. For example,
    if gas particles have particle type 0, and 'pos' is a valid field, then

        >>> s.pos[0] is s.gas.pos
        True

    However, note that s.gas is a SnapshotView, which is a read-only object.
    In order to modify the dataset one must, in general, operate on s.pos[0] or
    similar.

    In the case that no index-to-name mapping is provided, s.gas or similar will
    raise an AttributeError. The dictionary of index-to-name mappings may be
    accessed as s.ptype_aliases. It will be None if no mapping is present, it
    is not required to map all valid particle indices, and it cannot be
    assigned to.


    Acessing metadata
    -----------------

    The file name and header are both properties of the snapshot, accessed
    as

        >>> s.fname
        'some_file_name'
        >>> s.header

    For the latter, see the SnapshotHeader class.

    The indices of all valid particle types for this snapshot are stored in the
    list s.ptype_indices.
    """

    def __init__(self, fname, header_schema=None, blocks_schema=None,
                 ptype_aliases=None, **kwargs):
        """
        Initializes a Gadget-like snapshot.

        header_schema defines the schema for loading the file header.
        blocks_schema defines the schema for loading the various field data
        ptype_aliases is an optional string-to-index mapping for the particle
                      types contained in the snapshot
        """
        if header_schema is None:
            raise TypeError("header_schema is required")
        if blocks_schema is None:
            raise TypeError("blocks_schema is required")

        super(SnapshotBase, self).__init__(**kwargs)
        self._fname = fname
        self._aliases = ptype_aliases
        self.header = SnapshotHeader(fname, header_schema)
        self._fields = []

        # Use copy so that reference schema is not altered.
        self._schema = copy(blocks_schema)
        self._ptypes = 0
        self.verify_schema()
        self.init_fields()

    def __getattr__(self, name):
        if self._aliases and name in self._aliases:
            idx = self._aliases[name]
            return self._ptype_view(idx)
        else:
            msg = "'%s' object has no attribute %s" % (type(self).__name__, name)
            raise AttributeError(msg)

    @property
    def fields(self):
        return self._fields

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, fname):
        self.header.fname = fname
        self._fname = fname

    @property
    def ptype_aliases(self):
        return self._aliases

    @property
    def ptype_indices(self):
        """
        A list of the Gadget-like particle type indices in this snapshot.

        Contains all valid particle types, some of which may not have any
        associated data in the snapshot.
        """
        return range(self._ptypes)

    @ptype_indices.setter
    def ptype_indices(self, value):
        """
        Set the valid Gadget-like particle type indices for this snapshot.

        Must be an iterable containing all required particle types. Gaps are
        allowed; both [0, 1, 2, 3] and [0, 3] result in identical behaviour.
        """
        self._ptypes = max(value)

    def init_fields(self):
        """Reset all data attributes to zero-like values."""
        for (name, fmt) in self._schema.items():
            dtype, ndims, ptypes, _ = fmt
            pdata = self._null_block(dtype, ndims, ptypes)
            setattr(self, name, pdata)

    def iterfields(self):
        for name in self.fields:
            yield (name, getattr(self, name))

    def load(self):
        """Load in snapshot data from the current file."""
        with FortranFile(self.fname, 'rb') as ffile:
            self.header._load(ffile)
            self._load(ffile)

    def save(self, fname=None):
        """
        Write header and snapshot to the current file, overwriting the file.

        A different file name to write to may optionally be provided. This
        does not modify the header's or the snapshot's fname attribute, so
        later calling load() will re-load data from the original file.

        The method will raise a SnapshotIOException if the any field is not
        valid. See verify().
        """
        if fname is None:
            fname = self.fname

        if self.header.verify() != []:
            raise SnapshotIOException("Current header state invalid")
        if self.verify() != []:
            raise SnapshotIOException("A field does not match the schema")

        self.update_header()
        with FortranFile(fname, 'wb') as ffile:
            self.header._save(ffile)
            self._save(ffile)

    def update_header(self):
        """
        Update the header based on the current snapshot state.

        This method has no effect, but is called when saving a snapshot to file.
        It should be overridden by subclasses.
        """
        pass

    def verify(self):
        """
        Return a list of fields which do not conform to the schema.

        An empty list indicates that all fields are valid.
        """
        malformed = []
        for name in self.fields:
            # If a is an empty numpy array, nothing will be written, so we
            # do not need to filter out empty arrays.
            dtype, ndims, _, _ = self._schema[name]
            arrays = [a for a in getattr(self, name) if a is not None]
            for a in arrays:
                if a.dtype != dtype or (a.ndim > 1 and a.shape[-1] != ndims):
                    print name, a.dtype, dtype
                    malformed.append(name)
                    # Don't want duplicates; one problem is sufficient.
                    break
        return malformed

    def verify_schema(self):
        """Verify the current schema."""
        self._verify_schema()

    def _block_exists(self, name, ptypes):
        """
        Return True if specified particle types exist for specified block.

        Must be overriden by subclasses.
        """
        raise NotImplementedError("Subclassees must override _block_exists")

    def _get_flag(self, flag):
        if isinstance(flag, str):
            return getattr(self.header, flag)
        else:
            return flag

    def _load(self, ffile):
        """
        Load data for each block in the schema from the open FortranFile ffile.

        Only blocks with flags resolving to True are loaded from the file.
        """
        for (name, fmt) in self._schema.items():
            dtype, ndims, ptypes, flag = fmt
            if self._block_exists(name, ptypes) and self._get_flag(flag):
                block_data = self._load_block(ffile, name, dtype)
                pdata = self._parse_block(block_data, name, dtype, ndims, ptypes)
            else:
                pdata = self._null_block(dtype, ndims, ptypes)
            setattr(self, name, pdata)

    def _load_block(self, ffile, name, dtype):
        """
        Return the next block from the open FortranFile ffile as an ndarray.

        This is called before parsing each block's raw data, and may need to
        be overriden by subclasses.
        """
        return ffile.read_record(dtype)

    def _null_array(self, dtype):
        """Return an empty numpy array of element type dtype."""
        return np.empty(0, dtype=dtype)

    def _null_block(self, dtype, ndims, ptypes):
        """
        Return a block of zero-like data, or None where ptype not appropriate.
        """
        pdata = []
        for p in self.ptype_indices:
            if p not in ptypes:
                parray = None
            else:
                parray = self._null_array(dtype)
                if ndims > 1:
                    parray.shape = (0, ndims)
            pdata.append(parray)
        return pdata

    def _parse_block(self, block_data, name, dtype, ndims, ptypes):
        """
        Return a list of data for each particle type in the block.

        Interpret the raw data within block_data according to the schema,
        and apply the specified particle type and dimensionality operations.

        Must be overriden by subclasses.
        """
        raise NotImplementedError("Subclasses must override _parse_block")

    def _ptype_view(self, index):
        ptype_data = ((name, field[index]) for name, field in self.iterfields())
        view = SnapshotView(self, ptype_data)
        return view

    def _save(self, ffile):
        for name in self.fields:
            # If a is an empty numpy array, nothing will be written, so we
            # do not need to filter out empty arrays.
            arrays = [a for a in getattr(self, name) if a is not None]
            ffile.write_ndarrays(arrays)

    def _verify_schema(self):
        """
        Verifies the block formatter, and updates it if necessary.

        When a block's data type is not supplied, it is assumed to be 4-byte
        floats.
        When a block's N-dimesion value is also not supplied, it is assumed to
        be 1.
        When a block's particle type is also not supplied, it is assumed to
        apply to all particle types.

        All valid particle types must appear in at least one of the block
        schemas, though a particle type of 0 is always assumed.

        When called with no arguments, the internal block formatter is used.

        Completes the block schema if possible, else raises a
        SnapshotIOException.
        """

        max_ptype = -1
        for (name, fmt) in self._schema.items():
            # So that these are defined even for an invalid formatter.
            dtype, ndims, ptypes, flag = ('f4', 1, [None, ], True)
            if len(fmt) == 4:
                dtype, ndims, ptypes, flag = fmt
            elif len(fmt) == 3:
                dtype, ndims, ptypes = fmt
            elif len(fmt) == 2:
                dtype, ndims  = fmt
            elif len(fmt) == 1:
                dtype, = fmt
            else:
                message = "Formatter for block '%s' is invalid" % name
                raise SnapshotIOException(message)

            try:
                dtype = np.dtype(dtype)
            except TypeError:
                # Given dtype does not correspond to a numpy dtype.
                message = "Data type for block '%s' is invalid." % name
                raise SnapshotIOException(message)

            try:
                ndims = int(ndims)
            except TypeError:
                message = "N-dimensions size for block '%s' is invalid." % name
                raise SnapshotIOException(message)

            max_ptype = max(max_ptype, max(ptypes))
            self._schema[name] = (dtype, ndims, ptypes, flag)

        if max_ptype == -1:
            message = 'At least one block schema must have specified ptypes'
            raise SnapshotIOException(message)

        # For any block which had no ptypes set, assume it is valid for all
        # ptypes.
        self._ptypes = max_ptype + 1
        for (name, fmt) in self._schema.items():
            _, _, ptype, _ = fmt
            if ptypes == [None]:
                self._schema[name] = self.ptype_indices

        self._fields = self._schema.keys()
