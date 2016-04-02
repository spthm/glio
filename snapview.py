class SnapshotView(object):
    """
    A view into some subset of a snapshot instance.

    The attributes of the view depend on the snapshot from which it was derived,
    and the kind of view requested. All available attributes from the snapshot
    are available via the fields property, which returns a tuple.

    Modifying elements of the view in-place will modify the elements in the
    associated snapshot. Similarly, modifying elements of the snapshot in-place
    will modify them in the view. However, it is not possible to reassign
    attributes of the view. Further, reassignment of attributes of the original
    snapshot will not be propagated to the view.

    To clarify,

        >>> g = GadgetSnapshot('filename')
        >>> hsml = g.gas.hsml
        >>> hsml is g.hsml[0]
        True
        >>> hsml[0] = 2 * hsml[0]
        >>> hsml is g.hsml[0]
        True
        >>> hsml = 2 * hsml
        TypeError: 'SnapsotView' object does not support item assignment
        >>> hsml *= 2
        TypeError: 'SnapsotView' object does not support item assignment
        >>> g.hsml[0] = 2 * g.hsml[0]
        >>> hsml is g.hsml[0]
        False
        >>> g.gas.hsml is g.hsml[0]
        True
    """

    def __init__(self, _parent_snapshot, _data):
        super(SnapshotView, self).__setattr__('_parent', _parent_snapshot)
        super(SnapshotView, self).__setattr__('_fields', set())
        for (name, value) in _data:
            self._fields.add(name)
            super(SnapshotView, self).__setattr__(name, value)

    # TODO: We should be able to change attributes of the view, and these
    # changes should be propagated to the parent snapshot.
    def __setattr__(self, name, value):
        raise TypeError("'SnapsotView' object does not support item assignment")

    @property
    def fields(self):
        return tuple(self._fields)
