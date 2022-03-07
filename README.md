[![Build Status](https://travis-ci.org/boundlessgeo/qgis-what3words-plugin.svg?branch=master)](https://travis-ci.org/boundlessgeo/qgis-what3words-plugin)

# What3words tools

What3words tools is a plugin for QGIS that brings the functionality of the what3words API to the QGIS platform. You can use the plugin to convert from coordinates to 3 word addresses by adding a field to a shapefile as well as searching for 3 word addresses or inspecting the map to view the 3 word address for a location.

## Documentation

The plugin is documentated [here](https://developer.what3words.com/tools/gis-extensions/qgis)

## Cloning this repository

This repository uses external repositories as submodules. Therefore in order to include the external repositories during cloning you should use the *--recursive* option:

`git clone --recursive https://github.com/what3words/qgis-what3words-plugin.git`

Also, to update the submodules whenever there are changes in the remote repositories one should do:

`git submodule update --remote`
