import os
import site

def classFactory(iface):
    from plugin import W3WTools
    return W3WTools(iface)
