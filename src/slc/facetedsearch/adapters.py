from zope.component import queryUtility
from zope.component import adapts
from zope.interface import implements
from zope.interface import Interface
from collective.solr.interfaces import ISolrConnectionConfig
import interfaces

class DefaultRangesGetter(object):

    implements(interfaces.IDefaultRangesGetter)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    def getDefaultRanges(self):
        """ """
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            # FIXME: the ranges must be configurable on the config...
            ranges = ['created', 'expires', 'modified'] #config.facetranges
            return ranges
