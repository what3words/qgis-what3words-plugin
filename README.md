# What3words tools QGIS Plugin

[![License: GPL v2](https://img.shields.io/badge/License-GPLv2-blue.svg)](./LICENSE.md)

What3words tools is a plugin for QGIS that brings the functionality of the what3words API to the QGIS platform. You can use the plugin to convert from coordinates to 3 word addresses by adding a field to a shapefile as well as searching for 3 word addresses or inspecting the map to view the 3 word address for a location.

## Installation
The What3words tools plugin is currently available in the [QGIS Plugins server](https://plugins.qgis.org/plugins/what3words/). You can download or install it directly into your QGIS map.
Or you can install the latest version, using the [release page](https://github.com/what3words/qgis-what3words-plugin/releases), then open the QGIS Plugin manager and install the downloaded zip file.

This plugin is compatible with QGIS v3 or later.

## Usage

The plugin is documentated [here](https://developer.what3words.com/tools/gis-extensions/qgis)


## QT designer layout
To extract the UI from the QT designer, run the following command on the bash

```shell
pyuic5 what3words/ui/coorddialog.ui -o what3words/ui/coorddialog_ui.py
```

## License - GPLv2

Versions 1-3, Copyright  (C) 2016-2020 Planet Federal QGIS plugin [contributors](CONTRIBUTING.rst)

Version 4, Copyright (C) 2020-2022, what3words Limited

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

## Changelog

*2020 (v4.0)*
Update to API V3 and added language setting

    Update to latest version of what3words API (V3)
    Added language code field to change what3words language
    Updated what3words logo

*2022 (v4.1)*
Add a tracking method for QGIS plugin usage

    Add http headers in the plugin
    Update the metadata.txt
    Update the readme file

*2022 (v4.2)*
Add exceptions

    Add exceptions
    Fix small bugs
    Update logo
    Update metadata by signing up to what3words account

*2022 (v4.3)*
Remove tkinter library 
    
    Fix a bug on installing the widget on QGIS windows

*2024 (v4.4)*
Redesign the plugin
    
    Add a grid view
    Update the zoom to what3words 
    Update the map tool 
    Add the AutoSuggest component
    Add what3words Tools functions within Fields Calculator
    Allow to use other API base URL