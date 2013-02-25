import collections

# The following numpy shorthand types are used:
# 'i4' = integer          = 4 bytes.
# 'u4' = unsigned integer = 4 bytes.
# 'i8' = 64-bit integer   = 8 bytes.
# 'f4' = float            = 4 bytes.
# 'f8' = double           = 8 bytes.

# header_entry_name, (type[, length]).
header = collections.OrderedDict([
    ('npart', ('i4', 6)),
    ('mass', ('f8', 6)),
    ('time', ('f8', 1)),
    ('redshift', ('f8', 1)),
    ('flag_sfr', ('i4', 1)),
    ('flag_feedback', ('i4', 1)),
    ('npartTotal', ('i4', 6)),
    ('flag_cooling', ('i4', 1)),
    ('nfiles', ('i4', 1)),
    ('BoxSize', ('f8', 1)),
    ('OmegaM', ('f8', 1)),
    ('OmegaL', ('f8', 1)),
    ('HubbleParam', ('f8', 1)),
    ('flag_stellarage', ('i4', 1)),
    ('flag_metals', ('i4', 1)),
    ('npartTotalHW', ('i4', 6)),
    ('flag_S_instead_u', ('i4', 1),
    
    # Additional to Gadget.
    ('OmegaB', ('f8', 1)),
    ('rays_traced', ('i8', 1)),
    ('flag_Hmf', ('i4', 1)),
    ('flag_Hemf', ('i4', 1)),
    ('flag_helium', ('i4', 1)),
    ('flag_gammaHI', ('i4', 1)),
    ('flag_cloudy', ('i4', 1)),
    ('flag_eos', ('i4', 1)),
    ('flag_incsfr', ('i4', 1)),
    ('time_gyr', ('f8', 1)) ])
                
data = collections.OrderedDict([
    # block_name, (type, ndims).
    ('pos', ('f4', 3)),
    ('vel', ('f4', 3)),
    ('ID', ('i4', 1)),
    ('mass', ('f4', 1)),
    ('u', ('f4', 1)),
    ('rho', ('f4', 1)),
    ('ye', ('f4', 1)),
    ('xHI', ('f4', 1)),
    ('h', ('f4', 1)),
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
    ('lasthit', ('i8', 1)) ])
