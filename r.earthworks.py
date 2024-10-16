#!/usr/bin/env python

##############################################################################
# MODULE:    r.earthworks
#
# AUTHOR(S): Brendan Harmon <brendan.harmon@gmail.com>
#
# PURPOSE:   Earthworks
#
# COPYRIGHT: (C) 2024 by Brendan Harmon and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Earthworks"""

# %module
# % description: Earthworks
# % keyword: raster
# % keyword: algebra
# % keyword: random
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % description: Input elevation raster
# % label: Input elevation raster
# %end

# %option G_OPT_R_OUTPUT
# % key: earthworks
# % description: Output elevation raster
# % label: Earthworks
#% answer: earthworks
# %end

# %option
# % key: operation
# % type: string
# % answer: absolute
# % options: relative,absolute
# % description: Earthworking operation
# % descriptions: relative;Operation relative to exisiting topography;absolute;Operation at given elevation
# % required: yes
#%end

# %option
# % key: function
# % type: string
# % answer: linear
# % options: linear,exponential
# % description: Earthworking function
# % descriptions: linear;linear decay function;exponential;Exponential decay function
# % required: yes
#%end

# %option G_OPT_R_INPUT
# % key: raster
# % description: Raster
# % label: Input raster spot elevations
# % required: no
# % guisection: Input
# %end

# %option G_OPT_M_COORDS
# % label: Seed point coordinates
# % description: Coordinates
# % required: no
# % guisection: Input
# %end

# %option G_OPT_V_INPUT
# % key: points
# % label: Input points
# % description: Input points
# % required: no
# % guisection: Input
# %end

# %option G_OPT_V_INPUT
# % key: lines
# % label: Input lines
# % description: Input lines
# % required: no
# % guisection: Input
# %end

#%option
#% key: z
#% type: double
#% description: Elevation value
#% label: Elevation value
#% answer: 1.0
#% multiple: no
#% guisection: Input
#%end

#%option
#% key: rate
#% type: double
#% description: Rate of decay
#% label: Rate of decay
#% answer: 0.1
#% multiple: no
#% guisection: Function
#%end

import sys
import atexit
import grass.script as grass

def clean(name):
    grass.run_command(
        'g.remove',
        type='raster',
        name=name,
        flags='f',
        superquiet=True)

def convert_raster(raster):

    # parse raster
    stats = grass.parse_command(
        'r.stats',
        input=raster,
        flags=['xn']
        )

    # write each cell to raster
    attractors = []
    i = 0
    for stat in stats:
        data = stat.split(' ')
        col = data[0]
        row = data[1]
        cell = grass.append_node_pid(f'cell_{i}')
        grass.mapcalc(
        f'{cell} = if(col() == {col} && row() == {row}, {raster}, null())',
        overwrite=True
        )
        i = i + 1
        attractors.append(cell)

    return attractors

def convert_coordinates(coordinates, z):

    # create list
    attractors = []

    # parse input coordinates
    coordinates = coordinates.split(',')
    cx = coordinates[::2]
    cy = coordinates[1::2]
    cz = z.split(',')
    coordinates = (
        [f'{x},{y},{z}' for x, y, z in zip(cx, cy, cz)]
        )
    if len(cz) > 1 and len(cz) != len(cx):
        grass.warning(
            'Number of z-values does not match xy-coordinates!'
            )
 
    # convert each coordinate to raster
    n = len(coordinates)    
    for index in range(n):
        attractor = grass.append_node_pid(f'attractor_{index + 1}')
        atexit.register(clean, attractor)
        grass.write_command(
            'r.in.xyz',
            input='-',
            output=attractor,
            separator='comma',
            stdin=coordinates[index],
            overwrite=True
            )

        # append to list
        attractors.append(attractor)

    return attractors

def convert_points(points, z):

    # create list
    attractors = []

    # get info
    info = grass.parse_command(
        'v.info',
        map=points,
        flags='t'
        )

    # convert to 3D
    points_3d = grass.append_node_pid('points_3d')
    atexit.register(clean, points_3d)
    if info['map3d'] == '0':
        grass.run_command(
            'v.to.3d',
            input=points,
            output=points_3d,
            height=z,
            overwrite=True,
            superquiet=True
            )
        points = points_3d

    # convert each point to raster
    n = info['points']
    for index in range(1, int(n)+1):
        attractor = f'attractor_{index}'
        attractor = grass.append_node_pid(attractor)
        atexit.register(clean, attractor)
        grass.run_command(
            'v.to.rast',
            input=points,
            cats=index,
            output=attractor,
            use='z',
            overwrite=True,
            superquiet=True
            )
    
        # append to list
        attractors.append(attractor)
    
    return attractors

def convert_lines(lines):

    # convert lines to points
    region = grass.parse_command('g.region', flags=['g'])
    res = region['nsres']
    points = grass.append_node_pid('points')
    atexit.register(clean, points)
    grass.run_command(
        'v.to.points',
        input=lines,
        output=points,
        use='vertex',
        dmax=res,
        flags='i',
        overwrite=True
        )

    return points

def distance(attractor, elevation, operation):

    # assign variables
    dxy = 'dxy'
    dz = 'dz'    

    # set relative or absolute attractors
    if operation == 'relative':
        grass.mapcalc(
            f'{attractor} = if(isnull({attractor}), null(), {elevation} + {attractor})',
            overwrite=True
            )

    # calculate distance field
    grass.run_command(
        'r.grow.distance',
        input=attractor,
        distance=dxy,
        value=dz,
        overwrite=True,
        superquiet=True
        )

    # determine operation
    if operation == 'absolute':
        grass.mapcalc(
            f'{dz} = {dz} - {elevation}',
            overwrite=True
            )

        return dxy, dz

def linear_decay(dz, dxy, rate, decay):

    # f(t) = C - r * t
    # z = A - 1/R * r
    grass.mapcalc(
        f'{decay} = {dz} - {rate} * {dxy}',
        overwrite=True
        )
    return decay

def exponential_decay(dz, dxy, rate, decay):
    
    # z = z0 * e^(-lamba * t)
    grass.mapcalc(
        f'{decay} = {dz} * exp(2.71828, (-{rate} * {dxy}))',
        overwrite=True
        )
    return decay

def decay_fuction(function, dz, dxy, rate):

    # assign variables
    decay = 'decay'

    # determine decay function
    if function == 'linear':
        decay = linear_decay(dz, dxy, rate, decay)
    if function == 'exponential':
        decay = exponential_decay(dz, dxy, rate, decay)
        
    return decay

def earthworking(earthwork, elevation, decay):

    # model earthworks
    grass.mapcalc(
        f'{earthwork}'
        f'= if({elevation} + {decay} >= {elevation},'
        f'{elevation} + {decay},'
        f'{elevation})',
        overwrite=True
        )

def series(landforms, earthworks):

    # merge rasters
    grass.run_command(
        'r.series',
        input=landforms,
        output=earthworks,
        method='maximum',
        overwrite=True
        )

    # set colors
    grass.run_command(
        'r.colors',
        map=earthworks,
        color='viridis'
        )

    # save history
    grass.raster_history(
        earthworks,
        overwrite=True
        )

def main():

    # get input options
    options, flags = grass.parser()
    elevation = options['elevation']
    earthworks = options['earthworks']
    operation = options['operation']
    function = options['function']
    rate = options['rate']
    raster = options['raster']
    points = options['points']
    lines = options['lines']
    coordinates = options['coordinates']
    z = options['z']

    # convert inputs
    if raster:
        attractors = convert_raster(raster)
    elif coordinates:
        attractors = convert_coordinates(coordinates, z)
    elif points:
        attractors = convert_points(points, z)
    elif lines:
        points = convert_lines(lines)
        attractors = convert_points(points, z)
    else:
        grass.error(
            'An input raster, set of coordinates, or point is required!'
            )

    # iterate through inputs
    landforms = []
    for attractor in attractors:

        # create temporary rasters
        index = attractor.split('_', 2)
        earthwork = f'earthwork_{index[1]}'
        earthwork = grass.append_node_pid(earthwork)
        atexit.register(clean, earthwork)

        # model each earthwork
        dxy, dz = distance(attractor, elevation, operation)
        decay = decay_fuction(function, dz, dxy, rate)
        earthworking(earthwork, elevation, decay)
        landforms.append(earthwork)

    # model earthworks
    series(landforms, earthworks)

if __name__ == "__main__":
    sys.exit(main())
