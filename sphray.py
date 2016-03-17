from collections import OrderedDict
from itertools import chain

from .gadget import GadgetSnapshot
from .gadget import _header_schema as _gadget_header_schema

# See gadget.py
# Additional to gadget._header_schema.
_sphray_header_schema = OrderedDict([
    ('OmegaB', ('f8', 1)),
    ('rays_traced', ('i8', 1)),
    ('flag_Hmf', ('i4', 1)),
    ('flag_Hemf', ('i4', 1)),
    ('flag_helium', ('i4', 1)),
    ('flag_gammaHI', ('i4', 1)),
    ('flag_cloudy', ('i4', 1)),
    ('flag_eos', ('i4', 1)),
    ('flag_incsfr', ('i4', 1)),
    ('time_gyr', ('f8', 1))
])

_header_schema = OrderedDict()
for (key, value) in chain(_gadget_header_schema.items(),
                          _sphray_header_schema.items()):
    _header_schema[key] = value

# See gadget.py
# Replaces gadget._blocks_schema.
_blocks_schema = OrderedDict([
    ('pos', ('f4', 3)),
    ('vel', ('f4', 3)),
    ('ID', ('i4', 1)),
    ('mass', ('f4', 1)),
    ('u', ('f4', 1)),
    ('rho', ('f4', 1)),
    ('ye', ('f4', 1)),
    ('xHI', ('f4', 1)),
    ('hsml', ('f4', 1)),
    ('T', ('f4', 1)),
    ('Hmf', ('f4', 1)),
    ('Hemf', ('f4', 1)),
    ('xHeI', ('f4', 1)),
    ('xHeII', ('f4', 1)),
    ('gammaHI', ('f4', 1)),
    ('time', ('f4', 1)),
    ('xHI_cloudy', ('f4', 1)),
    ('eos', ('f4', 1)),
    ('sfr', ('f4', 1)),
    ('lasthit', ('i8', 1))
])


class SPHRAYSnapshot(GadgetSnapshot):
    """
    A class for SPHRAY snapshots.

    See also GadgetSnapshot and SnapshotBase.


    To read in a snapshot file:

        >>> s = SPHRAYSnapshot('file_name')
        >>> s.load()
    """

    def __init__(self, fname):
        """Initializes an SPHRAY snapshot."""
        super(SPHRAYSnapshot, self).__init__(fname, _header_schema,
                                             _blocks_schema)
