[![DOI](https://joss.theoj.org/papers/10.21105/joss.09270/status.svg)](https://doi.org/10.21105/joss.09270)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

![Elevation](paper/figure_1.png)

# r.earthworks

An add-on tool for computational terrain modeling in GRASS.
This is the repository for development version. 
The stable release is in the 
[GRASS Addons Repository](https://github.com/OSGeo/grass-addons).
To learn more see the 
[paper](https://raw.githubusercontent.com/baharmon/r.earthworks/main/paper/paper.pdf),
[documentation](https://grass.osgeo.org/grass85/manuals/addons/r.earthworks.html),
and [tutorials](https://grass-tutorials.osgeo.org/content/tutorials/earthworks/earthworks.html).

## Installation

Install the stable release:
```bash
g.extension  extension=r.earthworks
```

Install the development version:
```bash
g.extension  extension=r.earthworks url=https://github.com/baharmon/r.earthworks
```

## Example

To grade a road crossing over a valley in the
[North Carolina](https://grass.osgeo.org/sampledata/north_carolina/nc_basic_spm_grass7.zip)
sample dataset, run:

```bash
g.region n=217700 s=216200 w=639200 e=640700 res=10
r.earthworks elevation=elevation earthworks=earthworks lines=roadsmajor z=95 function=linear linear=0.25 operation=fill flat=25
r.contour input=earthworks output=contours step=2
```

| Elevation | Earthworks |
| --------- | ---------- |
| ![Elevation](r_earthworks_07.png) | ![Earthworks](r_earthworks_08.png) |

## Tutorials

Learn how model terrain with r.earthworks. 
With this tool you can generate new terrain
or modify existing terrain using cut and fill operations
inspired by earthworking.
The first tutorial on the basics of terrain modeling
introduces key concepts such as cut and fill operations.
The subsequent tutorials introduce more advanced concepts
such as relative operations and growth and decay functions.
These tutorials demonstrate how to generate terrain,
model natural landforms,
and model anthropogenic landforms - i.e. earthworks -
such as roads, dams, and levees.
Read our [paper](https://doi.org/10.21105/joss.09270) to learn more.

### [Basic earthworks](https://grass-tutorials.osgeo.org/content/tutorials/earthworks/basics.html)

Learn the basics of terrain modeling with r.earthworks.

![Basic earthworks](tutorials/images/basics_05.webp)

### [Gully modeling](https://grass-tutorials.osgeo.org/content/tutorials/earthworks/gullies.html)

Model gullies using relative cut operations.

![Gully modeling](tutorials/images/gullies_03.webp)

### [Coastal infrastructure](https://grass-tutorials.osgeo.org/content/tutorials/earthworks/levees.html)

Model coastal infrastructure projects including levees and restored alluvial ridges.

![Coastal infrastructure](tutorials/images/levees_08.webp)

### [Terrain synthesis](https://grass-tutorials.osgeo.org/content/tutorials/earthworks/synthesis.html)

Synthesize terrain by applying landforms from one landscape to another.

![Terrain synthesis](tutorials/images/synthesis_07.webp)