from collections import OrderedDict

import numpy as np

from .snapshot import SnapshotBase, SnapshotIOException

# The following numpy shorthand types are used:
# 'i4' = integer          = 4 bytes.
# 'u4' = unsigned integer = 4 bytes.
# 'i8' = 64-bit integer   = 8 bytes.
# 'f4' = float            = 4 bytes.
# 'f8' = double           = 8 bytes.

# The below formats must be in the correct order!  That is,
# the ordering of the terms in header and blocks must match that of
# the corresponding binary file.

# header_entry_name, (type[, length]).
_g_header_schema = OrderedDict([
    ('npart', ('i4', 6)),
    ('mass', ('f8', 6)),
    ('time', ('f8', 1)),
    ('redshift', ('f8', 1)),
    ('flag_sfr', ('i4', 1)),
    ('flag_feedback', ('i4', 1)),
    ('npartTotal', ('u4', 6)),
    ('flag_cooling', ('i4', 1)),
    ('num_files', ('i4', 1)),
    ('BoxSize', ('f8', 1)),
    ('Omega0', ('f8', 1)),
    ('OmegaLambda', ('f8', 1)),
    ('HubbleParam', ('f8', 1)),
    ('flag_stellarage', ('i4', 1)),
    ('flag_metals', ('i4', 1)),
    ('npartTotalHighWord', ('u4', 6)),
    ('flag_entropy_instead_u', ('i4', 1)),
    ('_padding', ('i4', 15)),
])

# block_name, (type[, ndims[, particletype[, flag]]]).
# If present, flag may be boolean-like, or a string corresponding to a header
# schema entry, e.g. 'flag_metals'.
_g_blocks_schema = OrderedDict([
    ('pos', ('f4', 3, [0,1,2,3,4,5])),
    ('vel', ('f4', 3, [0,1,2,3,4,5])),
    ('ID', ('u4', 1, [0,1,2,3,4,5])),
    ('mass', ('f4', 1, [0,1,2,3,4,5])),
    ('u', ('f4', 1, [0,])),
    ('rho', ('f4', 1, [0,])),
    ('hsml', ('f4', 1, [0,])),
])


class GadgetSnapshot(SnapshotBase):
    """
    A class for Gadget snapshots.

    See also SnapshotBase.

    To read in a snapshot file:

        >>> from glio import GadgetSnapshot
        >>> s = GadgetSnapshot('file_name')
        >>> s.load()


    Accessing simulation data
    -------------------------

    The simulation data associated with a snapshot, s, can be accessed as,

        >>> s.field_name[p]

    where 'field_name' is one of the strings in s.fields, p is the particle
    type index (in [0, 6] as defined in Gadget-2) and [0:N] implies we wish
    to access all particles from the first to the Nth.

    All fields may be iterated through using

        >>> for (name, field) in s.iterfields():
        >>>    # Do something

    Position (pos) and velocity (vel) data are (N, 3) shape numpy.ndarrays.
    For example, if s contains 128^3 gas particles, the (x, y, z) position of
    the first gas particle, p0, can be accessed as

        >>> gas_pos = s.pos[0]
        >>> gas_pos.shape
        (2097152, 3)
        >>> p0 = gas_pos[0]
        >>> p0.shape
        (3,)


    Acessing metadata
    -----------------

    The associated file name and header are both attributes of the snapshot,
    accessed as

        >>> s.fname
        'some_file_name'
        >>> s.header

    For the latter, see the SnapshotHeader class.
    """

    def __init__(self, fname, _header_schema=_g_header_schema,
                 _blocks_schema=_g_blocks_schema):
        """Initializes a Gadget snapshot."""
        super(GadgetSnapshot, self).__init__(fname, _header_schema,
                                             _blocks_schema)

    def update_header(self):
        """Update the header based on the current block data.

        raise a SnapshotIOException if an inconsistency is found.
        """
        self._update_npars()

    def _load_block(self, ffile, name, dtype):
        """
        Return the next block from the open FortranFile ffile as an ndarray.

        Take special care when loading the mass block, which may not exist
        (in which case, return an empty ndarray).
        """
        if name == 'mass':
            return self._load_mass_block(ffile, dtype)
        else:
            return super(GadgetSnapshot, self)._load_block(ffile, name, dtype)

    def _load_mass_block(self, ffile, dtype):
        """
        Load the mass block from the open FortranFile ffile.

        If all masses a specified in the header, do not read from ffile, and
        return an empty ndarray.

        Note that, immediately prior to calling this method, the next call to
        ffile.read_record() must return the mass data, if it is present.
        """
        if self._has_mass_block():
            return ffile.read_record(dtype)
        else:
            return np.empty(0, dtype=dtype)

    def _has_mass_block(self):
        """
        Return True if the mass block exists in the file, False otherwise.

        A value of False implies that all masses are specified in the header.
        The return value of this function may be inaccurate after .load() has
        been called.
        """
        n = np.logical_and(self.header.npart > 0, self.header.mass == 0).sum()
        return n > 0

    def _npars(self, pdata):
        """
        Return the list of particle counts for particle block data pdata.

        If the block is not valid for particles of a given type, the
        corresponding element in the returned list is None.
        """
        npars = [None for _ in self.ptypes]
        for p, array in enumerate(pdata):
            if array is None:
                continue
            npars[p] = len(array)
        return npars

    def _parse_block(self, block_data, name, dtype, ndims, ptypes):
        """
        Return a list of data for each particle type in the block.

        Interpret the raw data within block_data according to the schema,
        and apply the specified particle type and dimensionality operations.

        For the mass block, generate mass arrays from the header data where
        appropriate.
        """
        if name == 'mass':
            return self._parse_mass_block(block_data, dtype)
        begin = 0
        pdata = []
        for (p, np) in zip(self.ptypes, self.header.npart):
            if p not in ptypes:
                parray = None
            else:
                end = begin + np * ndims
                parray = block_data[begin:end]
                begin = end
                if ndims > 1:
                    parray.shape = (np, ndims)
            pdata.append(parray)
        return pdata

    def _parse_mass_block(self, file_data, dtype):
        """Return a list of mass-data ndarrays for each particle type.

        Generate mass-data arrays from the header where appropriate.
        """
        begin = 0
        pmasses = []
        for (n, mass) in zip(self.header.npart, self.header.mass):
            if n > 0 and mass == 0:
                # A zero in masses means mass is to be read in from file.
                end = begin + n
                parray = file_data[begin:end]
                begin = end
            else:
                parray = mass * np.ones(n, dtype=dtype)
            pmasses.append(parray)

        # FIXME: We're currently just reading-in, and then overwriting the
        # compacted mass representation. It would be better not to!
        self._zero_header_masses()
        return pmasses

    def _update_npars(self):
        """Update the header.npart list based on the current block data.

        raise a SnapshotIOException if an inconsistency is found.
        """
        npars = [None for _ in self.ptypes]
        for (name, fmt) in self._schema.items():
            pdata = getattr(self, name)
            npars2 = self._npars(pdata)
            for p, (n, n2) in enumerate(zip(npars, npars2)):
                # None value for n2 implies that particle type p is not valid
                # for block specified by name.
                # 0 value for n2 implies there are no particles of type p for
                # block specified by name.
                if (n != n2) and (n is not None) and (n2 is not None) and (n2 != 0):
                    message = "npart mismatch for particle type " + str(p)
                    raise SnapshotIOException(message)

                if n is not None and n2 is not None:
                    npars[p] = max(n, n2)
                elif n2 is not None:
                    # n is None
                    npars[p] = n2
                # else npars[p] = n, but that is already true.

        npars = [n if n is not None else 0 for n in npars]
        dtype, _ = self.header._schema['npart']
        self.header.npart = np.array(npars, dtype=dtype)

    def _zero_header_masses(self):
        new_masses = [0 for _ in self.header.mass]
        dtype = self.header._schema['mass'][0]
        self.header.mass = np.array(new_masses, dtype=dtype)
