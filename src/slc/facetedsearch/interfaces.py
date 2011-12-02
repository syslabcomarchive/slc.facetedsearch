from zope.interface import Interface

class IProductLayer(Interface):
    """ Marker interface for requests indicating the staralliance.theme
        package has been installed.
    """

class IDefaultRangesGetter(Interface):
    """ Adapter to get the default ranges for faceted searching.
    """

    def getDefaultRanges(self):
        """ """
