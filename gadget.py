import collections
import numpy as np

from __future__ import print_function

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
header = collections.OrderedDict([
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
    ('flag_entropy_instead_u', ('i4', 1)) ])

# block_name, (type[, ndims, particletype]).
# TODO:  Allow generic float and use getPrecision to find actual value.
blocks = collections.OrderedDict([
    ('pos', ('f4', 3, [0,1,2,3,4,5])),
    ('vel', ('f4', 3, [0,1,2,3,4,5])),
    ('ID', ('u4', 1, [0,1,2,3,4,5])),
    ('mass', ('f4', 1, [0,1,2,3,4,5])),
    ('u', ('f4', 1, [0,])),
    ('rho', ('f4', 1, [0,])),
    ('hsml', ('f4', 1, [0,])) ])

# Gadget-2 has 6 different particle types.
ptypes = [0, 1, 2, 3, 4, 5]

class GadgetSnap(snapshots.Snap):

    """The main class for Gadget snapshots.
    
    If initialized with a file name, it reads in the snapshot data.  Can also
    be used for creating Gadget output snapshots from generic input.


    Accessing simulation data
    -------------------------
    
    The simulation data associated with a snapshot, s, can be accessed as,
        
        >>> s['field_name'][p][0:N]

    where 'field_name' is one of s.get_block_names(), p is the particle type,
    one of [0, 1, 2, 3, 4, 5] as defined in Gadget-2 and [0:N] implies we wish
    to access all particles from the first to the Nth.
    
    
    Acessing metadata
    -----------------
    
    The header information associated with a snapshot, s, can be accessed as,
    
        s.header['header_entry_name'].
        
    where 'header_entry_name' is one of s.get_header_names.  s.header is a
    Python dictionary, and the above returns an integer, float or numpy array
    as appropriate for the header element.
    
    """
    
    def __init__(self, file_loc, mode='load'):
        """Initializes a Gadget snapshot.
        
        To read in a snapshot:
            
            >>> s = glio.GadgetSnap("file_name")

        """
        super(GadgetSnap,self).__init__()
        self.file_loc = file_loc
        # Remove any directories from file location.
        # FIXME: Doesn't work on Windows.
        self.file_name = self.file_loc.split('/')
        
        self._all_particle_types = ptypes
        # Use copies so that gadget.header and gadget.blocks are not changed
        # when updating the header formatters.
        self._header_formatter = copy.copy(header)
        self._blocks_formatter = copy.copy(blocks)
        self.check_header_formatter()
        self.check_blocks_formatter()

        self.header = {}
        self._blocks = {}
                
        if mode == 'load':
            self._load_header()
            self._load_blocks()
        elif mode == 'create':
            pass
        else:
            raise ValueError("Initialization mode '%s' not recognized." % mode)

    def check_header_formatter(self, header=None, perror=True):
        
        """Verifies the header formatter, and updates it if necessary.

        For incomplete formatting, e.g. when an element size is not supplied,
        an element length of one is assumed and added to the formatter.
        
        When called with no arguments, the internal header formatter is used.
        Optionally, the method may be called with a header format dictionary
        for checking.

        Returns a valid header formatter if possible, else prints the issues
        and returns false.  If perror evaluates to False, issues are not
        printed.
        """
        
        valid = True

        if header == None:
            # header and self._header_formatter refer to the same dictionary!
            header = self._header_formatter
        
        for (name, fmt) in header.iteritems():
            # So that these are defined even for an invalid formatter
            dtype, size = ('f4', 1)
            try:
                if len(fmt) == 2:
                    dtype, size = fmt
                # If the size of the header element is not given, assume = 1.
                elif len(fmt) == 1:
                    dtype, size = (fmt[0], 1)
                else:
                    valid = False
                    if perror:
                        print("Formatter for header element '%s' " \
                              "is invalid." % name)
            except TypeError:
                valid = False
                if perror:
                    print("Formatter for header element '%s' is " \
                          "not iterable (should be e.g. tuple)." % name)
            
            try:
                dtype = np.dtype(dtype)
            # Given dtype does not correspond to a numpy dtype.
            except TypeError:
                valid = False
                if perror:
                    print("Data type for header element '%s' is invalid."
                          % name)
            
            try:
                size = int(size)
            except TypeError:
                valid = False
                if perror:
                    print("Data size for header element '%s' is invalid."
                          % name)
            
            header[name] = (dtype, size)
        
        if valid:
            return header
        else:
            return False

    def check_blocks_formatter(self, blocks=None):
        
        """Verifies the blocks formatter, and updates it if necessary.

        For incomplete formatting:
        - when a block particle type is not supplied, it is assumed to be 
          'all' (all particle types).
        - when a block N-dimesions is not supplied, it is assumed to be 1.
        
        When called with no arguments, the internal block formatter is used.
        Optionally, the method may be called with a block format dictionary
        for checking.

        Returns a valid block formatter if possible, else prints the issues
        and returns false.
        """

        valid = True

        if blocks == None:
            # blocks and self._blocks_formatter refer to the same dictionary!
            blocks = self._blocks_formatter
        
        for (name, fmt) in blocks.iteritems():
            # So that these are defined even for an invalid formatter.
            dtype, ndims, ptypes = ('f8', 1, [0,])
            try:
                if len(fmt) == 3:
                    dtype, ndims, ptypes = fmt
                elif len(fmt) == 2:
                    dtype, ndims  = fmt
                    # Assume attribute of all particles, e.g. position.
                    ptypes = self._all_particle_types
                elif len(fmt) == 1:
                    dtype, size = (fmt[0], 1, self._all_particle_types)
                else:
                    valid = False
                    print("Formatter for block '%s' is invalid." % name)
            except TypeError:
                valid = False
                print("Formatter for block '%s' is " \
                      "not iterable (should be e.g. tuple)." % name)
            
            try:
                np.dtype(dtype)
            # Given dtype does not correspond to a numpy dtype.
            except TypeError:
                valid = False
                print("Data type for block '%s' is invalid."  % name)
            
            try:
                ndims = int(ndims)
            except TypeError:
                valid = False
                print("Ndims for block '%s' is invalid." % name)
            
            # TODO: Make this tuple an instance attribute.
            for p in ptypes:
                if p not in self._all_particle_types:
                    valid = False
                    print("Particle type(s) for block '%s' is (are) invalid." % name)

        blocks[name] = (dtype, ndims, ptypes)
        
        if valid:
            return blocks
        else:
            return False

    def get_block_names(self):
        return self._blocks.keys()

    def get_header_names(self):
        return self.header.keys()

    def _load_header(self):
        with open(self.file_loc) as f:
            self._header_size = self._read_blocksize(f)
            self._header_start = f.tell()
            for (name, fmt) in header.iteritems():
                # If only one element to be read.
                if fmt[1] == 1:
                    self.header[name] = np.fromfile(f, *fmt)[0]
                # Multiple elements, so header[name] is an array.
                else:
                    self.header[name] = np.fromfile(f, *fmt)
            # Read header footer.
            self._header_end = f.tell()
            self._read_blocksize(f)
            
    def _load_blocks(self):
        npart = self.header['npart']
        mass = self.header['mass']
        # FIXME: Doesn't work if npartTotHW is non-zero (i.e. for Huge Sims).
        # A zero in mass[6] array => mass is to be read in from block.
        Nmassive = npart[(npart > 0) * (mass == 0)].sum()
        
        with open(self.file_loc) as f:
            # self._read_array_block handles the special case of mass.
            for name in blocks.iterkeys():
                self._blocks[name] = self._read_array_block(name, f)

    def _read_blocksize(self, f):
        return np.fromfile(f, 'u4', 1)[0]
        
    def _read_array_block(self, name, f):
        npart = self.header[name]
        # Empty block data for each particle, to be filled with the read data.
        block = self._all_particle_types[:]

        # Special case of mass where all data is in the header, and there is no
        # mass block.
        if name == 'mass':
            N_with_mass = npart[(npart > 0) * (mass == 0)].sum()
            if N_with_mass == 0:
                for p in block:
                    block[p] = mass[p] * np.ones(npart[p])
            return block
        
        dtype, ndims, ptypes = self._blocks_formatter[name]
        blocksize = self._read_blocksize(f)
        for p in block:
            # The case that particle type p is in this block.
            if p in ptypes:
                # Mass is a special case, since some data may have to be
                # generated from the header.
                N = npart[p]
                if name == "mass":
                    pmass = mass[p]
                    if N > 0 and pmass > 0:
                        block[p] = np.fromfile(f, dtype, Nmass)
                    elif N > 0 and pmass == 0:
                        block[p] = pmass * np.ones(N)
                    else:
                        block[p] = 0
                else:
                    block[p] = np.fromfile(f, dtype, N*ndims)
                    if ndims > 1:
                        self._blocks[name].reshape((N,ndims))
            else:
                # We want to know that there are zero particles of this type.
                block[p] = 0
        blocksize_end = self._read_blocksize(f)
        assert blocksize == blocksize_end, \
            "blocksize (%g) != (%g) blocksize_end in block %s", \
            % (blocksize, blocksize_end, name)
        return block

    def _seek_block_start(self, f):
        # TODO: Use self._header_end if set.  Default it to None in init?
        f.seek(0)
        self._read_blocksize(f)
        f.seek(self._header_size)
        self._read_blocksize(f)


    def __getitem__(self, name):
        if index in self._blocks:
            return self._blocks[name]
        else:
            raise ValueError("Data type %s does no exist in this snapshot.", \
                             % (name, )
