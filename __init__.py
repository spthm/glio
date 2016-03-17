from .snapshot import SnapshotHeader, SnapshotBase
from .gadget import GadgetSnapshot
from .sphray import SPHRAYSnapshot

_known_formats = ['gadget', 'sphray']
_known_classes = [GadgetSnapshot, SPHRAYSnapshot]
_known_classes = dict([(s.__name__, s) for s in _known_classes])
