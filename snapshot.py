from copy import copy

import numpy as np

from .fortranio import FortranFile

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


    Accessing block data
    --------------------

    The data associated with a block 'block' can be acccessed as,

        >>> s.block

    which is a list of ndarrays, one for each particle type for block 'block'.
    All (block_name, block_data) pairs may be iterated through using

        >>> for (name, data) in s.iterfields():
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

    @property
    def fields(self):
        return self._fields

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, fname):
        self._fname = fname

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

        A different file name to write to may optionally be provided.
        """
        if fname is None:
            fname = self.fname

        with FortranFile(fname, 'wb') as ffile:
            self._save(ffile)

    def verify_schema(self):
        """
        Verifies the header formatter, and updates it if necessary.

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


    Acessing Arrays
    ---------------

    An array may be acessed from an instantiated SnapshotBase object, s, as,

        >>> array = s.block_name

    'block_name' can be any of the strings acting as keys of the schema
    dictionary for this snapshot type.  A numpy array is returned. All valid
    keys are contained within the list s.fields.


    Acessing metadata
    -----------------

    The file name and header are both properties of the snapshot, accessed
    as

        >>> s.fname
        'some_file_name'
        >>> s.header

    For the latter, see the SnapshotHeader class.
    """

    def __init__(self, fname, header_schema, block_schema):
        """Initializes a Gadget-like snapshot."""
        super(SnapshotBase, self).__init__()
        self._fname = fname
        self.header = SnapshotHeader(fname, header_schema)
        self._fields = []

        # Use copy so that reference schema is not altered.
        self._schema = copy(block_schema)
        self._ptypes = 0
        self.verify_schema()

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
    def ptypes(self):
        """
        A list of the Gadget-like particle type indices in this snapshot.

        Contains all valid particle types, some of which may not have any
        associated data in the snapshot.
        """
        return range(self._ptypes)

    @ptypes.setter
    def ptypes(self, value):
        """Set the valid Gadget-like particle type indices for this snapshot.

        Must be an iterable containing all required particle types. Gaps are
        allowed; both [0, 1, 2, 3] and [0, 3] result in identical behaviour.
        """
        self._ptypes = max(value)

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

        A different file name to write to may optionally be provided.
        """
        if fname is None:
            fname = self.fname

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

    def verify_schema(self):
        """Verify the current schema."""
        self._verify_schema()

    def _load(self, ffile):
        """Load data for each block according to the schema."""
        for (name, fmt) in self._schema.items():
            dtype, ndims, _ = fmt
            block_data = ffile.read_record(dtype)
            pdata = self._parse_block(block_data, fmt)
            setattr(self, name, pdata)

    def _parse_block(self, block_data, fmt):
        """
        Interpret data within a block, according to the schema.

        Should be overriden by subclasses, as it assumes data is to be read
        exactly as described by the schema, and makes no use of information
        in the header.
        """
        _, ndims, ptypes = fmt
        N = len(block_data) // (ndims * len(ptypes))
        begin = 0
        pdata = []
        for p in self.ptypes:
            if p not in ptypes:
                parray = None
            else:
                end = begin + N * ndims
                parray = block_data[begin:end]
                begin = end
                if ndims > 1:
                    parray.shape = (N, ndims)
            pdata.append(parray)
        return pdata

    def _save(self, ffile):
        for name in self.fields:
            # If a is an empty numpy array, nothing will be written, so we
            # do not need to filter out empty arrays.
            arrays = [a for a in getattr(self, name) if a is not None]
            for a in arrays:
                if a.dtype != np.dtype(self._schema[name][0]):
                    message = "dtype incorrect for field %s" % name
                    raise SnapshotIOException(message)
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

        max_ptype = 0
        for (name, fmt) in self._schema.items():
            # So that these are defined even for an invalid formatter.
            dtype, ndims, ptypes = ('f4', 1, [None, ])
            if len(fmt) == 3:
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
            self._schema[name] = (dtype, ndims, ptypes)

        if max_ptype == 0:
            message = 'At least one block schema must have specified ptypes'
            raise SnapshotIOException(message)

        self._ptypes = max_ptype + 1
        for (name, fmt) in self._schema.items():
            _, _, ptype = fmt
            if ptypes == [None]:
                self._schema[name] = self.ptypes

        self._fields = self._schema.keys()
