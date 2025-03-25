[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# r.earthworks
An add-on module for computational terrain modeling in GRASS GIS.

## Installation
`g.extension  extension=r.earthworks url=https://github.com/baharmon/r.earthworks`

## Example
In the [North Carolina](https://grass.osgeo.org/sampledata/north_carolina/nc_spm_08_grass7.zip) sample dataset:
```
g.region n=223500 s=221500 w=637000 e=641000 res=10
r.earthworks elevation=elevation earthworks=earthworks function=linear lines=roadsmajor z=90 flat=30 spacing=10
r.colors -e map=elevation,earthworks color=elevation
```

![Elevation](elevation.png)

![Earthworks](earthworks.png)