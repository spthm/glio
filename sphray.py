from collections import OrderedDict
from itertools import chain

from .gadget import GadgetSnapshot
from .gadget import _g_header_schema

# See gadget.py
# Additional to gadget._header_schema.
_sphray_extra_header_schema = OrderedDict([
    ('OmegaB', ('f8', 1)),
    ('rays_traced', ('i8', 1)),
    ('flag_Hmf', ('i4', 1)),
    ('flag_Hemf', ('i4', 1)),
    ('flag_helium', ('i4', 1)),
    ('flag_gammaHI', ('i4', 1)),
    ('flag_cloudy', ('i4', 1)),
    ('flag_eos', ('i4', 1)),
    ('flag_sfr', ('i4', 1)),
    ('time_gyr', ('f8', 1)),
    ('_sphray_padding', ('i4', 2)),
])

_sphray_header_schema = OrderedDict()
for (key, value) in chain(_g_header_schema.items(),
                          _sphray_extra_header_schema.items()):
    if key != '_padding':
        _sphray_header_schema[key] = value

# See gadget.py
# Replaces gadget._g_blocks_schema.
_sphray_blocks_schema = OrderedDict([
    ('pos', ('f4', 3, [0,])),
    ('vel', ('f4', 3, [0,])),
    ('ID', ('i4', 1, [0,])),
    ('mass', ('f4', 1, [0,])),
    ('u', ('f4', 1, [0,])),
    ('rho', ('f4', 1, [0,])),
    ('ye', ('f4', 1, [0,])),
    ('xHI', ('f4', 1, [0,])),
    ('hsml', ('f4', 1, [0,])),
    ('T', ('f4', 1, [0,])),
    ('Hmf', ('f4', 1, [0,], 'flag_Hmf')),
    ('Hemf', ('f4', 1, [0,], 'flag_Hemf')),
    ('xHeI', ('f4', 1, [0,], 'flag_helium')),
    ('xHeII', ('f4', 1, [0,], 'flag_helium')),
    ('gammaHI', ('f4', 1, [0,], 'flag_gammaHI')),
    ('xHI_cloudy', ('f4', 1, [0,], 'flag_cloudy')),
    ('eos', ('f4', 1, [0,], 'flag_eos')),
    ('sfr', ('f4', 1, [0,], 'flag_sfr')),
    ('lasthit', ('i8', 1, [0,]))
])


class SPHRAYSnapshot(GadgetSnapshot):
    """
    A class for SPHRAY snapshots.

    See also GadgetSnapshot and SnapshotBase.


    To read in a snapshot file:

        >>> s = SPHRAYSnapshot('file_name')
        >>> s.load()
    """

    def __init__(self, fname, header_schema=_sphray_header_schema,
                 blocks_schema=_sphray_blocks_schema, **kwargs):
        """Initializes an SPHRAY snapshot."""
        super(SPHRAYSnapshot, self).__init__(fname,
                                             header_schema=header_schema,
                                             blocks_schema=blocks_schema,
                                             **kwargs)
