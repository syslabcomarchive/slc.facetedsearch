from zope.interface import Interface


# XXX: This is not being used and should be removed. The browserlayer is in
# ../interfaces.py

# I'm leaving this here for now to not break existing installations that depend
# on this. On those sites, slc.facetedsearch need to be reinstalled.

class IThemeSpecific(Interface):
    """ marker interface that defines a zope3 browser layer """
