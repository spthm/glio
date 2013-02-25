from __future__ import print_function

import gadget, sphray, psphray, massiveblack, generic

# TODO: Generate snapshot lists automagically from the contents of
# ./snapformats.
# Try:
# https://live.gnome.org/Gedit/PythonPluginHowTo
# http://www.luckydonkey.com/2008/01/02/python-style-plugins-made-easy/
# http://stackoverflow.com/questions/932069/building-a-minimal-plugin-architecture-in-python
# http://stackoverflow.com/questions/6233447/implementing-a-plugin-system-in-python?lq=1
# http://stackoverflow.com/questions/3964681/find-all-files-in-directory-with-extension-txt-with-python
# http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/

known_formats = ['gadget', 'sphray', 'psphray', 'massiveblack']
known_classes = [gadget.GadgetSnap, sphray.SphraySnap, psphray.PsphraySnap, 
                 massiveblack.MassiveBlackSnap]
known_classes = dict([(s.__name__, s) for s in known_classes])

def load(file_loc, snap_type, **kwargs):
    """Loads a gadget-like snapshot and returns a Snapshot instance.
    
    Arguments:
    file_loc  -- a string giving the snapshot file location.  
    
    snap_type -- the snapshot type, which should be one of those defined 
                 in glio/snapformats.  Case insensitive.  If the snapshot is 
                 defined there but has no associated class, a generic type is 
                 assumed.  In this case, the file is read exactly as 
                 prescribed by the format file.
    
    """
    
    if snap_type in known_classes:
        snap = known_classes[snap_type](file_loc, **kwargs)
        print("Loading using", snap.__name__)
        return snap
    elif snap_type in known_formats:
        # TODO: Implelemt this.
        snap = generic.GenericSnap(file_loc, **kwargs)
        print("Snapshot type", snap_type, "recognized as format-only."
        print("Loading as generic snapshot.")
        return snap
    else:
        raise IOError("Snapshot type: '%s' not recognized." % snap_type)
