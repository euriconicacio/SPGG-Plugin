# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SPGG
                                 A QGIS plugin
 Single-Point GEM Generator
                             -------------------
        begin                : 2016-10-03
        copyright            : (C) 2016 by Eurico Nicacio - EB/UFPR
        email                : euriconicacio@ufpr.br
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SPGG class from file SPGG.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .spgg import SPGG
    return SPGG(iface)
