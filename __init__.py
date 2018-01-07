# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KharifModelPoint
                                 A QGIS plugin
 Evaluate Kharif Model at a Location
                             -------------------
        begin                : 2018-01-07
        copyright            : (C) 2018 by IITB
        email                : sohoni@cse.iitb.ac.in
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
    """Load KharifModelPoint class from file KharifModelPoint.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .kharif_model_location import KharifModelPoint
    return KharifModelPoint(iface)
