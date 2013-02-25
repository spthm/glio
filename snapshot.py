import numpy as np
from __future__ import print_function

class Snap(object):

    """A base class for a single Gadget-like simulation snapshot.
    
    This class defines general attributes, properties and methods for
    snapshot classes.  All snapshot types derive from this class.
    
    In general, an instance of this class should be initialized using the
    helper functions glio.load or glio.create.
    
    -- Acessing Arrays --
    
    An array may be acessed from an instantiated Snap object, s, as,
    
        s['block_name'].
    
    'block_name' can be any of the strings acting as keys of the block
    OrderedDict object defined for this snapshot type.  A numpy array is
    returned.
    
    -- Acessing metadata --
    
    The file name and location are both properties of the snapshot, accessed
    as,
        
        s.file_name
        s.file_loc
    
    """
    
    def __init__(self):
        """Initializes an empty Snap object."""
        self._blocks = {}
        self.file_name = None
        self.file_loc = None
        
    def __getitem__(self, name):
        """Return a particular array block."""
        if self._check_name(name):
            return self._blocks[name]
            
    def __setitem__(self, name, new_block):
        """Set a particular array block"""
        if self._check_name(name):
            self._blocks[name] = new_block
        
    def __delitem__(self, name):
        """Delete a particular array block."""
        if self._check_name(name):
            del self._blocks[name]
            
    def _check_name(key):
        """Check if a given key refers to a valid block."""
        if not isinstance(name, str):
            raise TypeError("Array key is not a string.")
        elif not self._blocks.has_key(name):
            raise KeyError("'%s' is not a valid key" % name)
        else:
            return True
