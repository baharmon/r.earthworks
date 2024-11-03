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
# % key: mode
# % type: string
# % answer: absolute
# % options: relative,absolute
# % description: Earthworking mode
# % descriptions: relative;Relative to exisiting topography;absolute;At given elevation
# % required: yes
#%end

# %option
# % key: operation
# % type: string
# % answer: cutfill
# % options: cut,fill,cutfill
# % description: Earthworking operation
# % descriptions: cut;Cut into topography;fill;Fill ontop topography;cutfill;Cut and fill
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

#%option
#% key: flat
#% type: double
#% description: Radius of flats
#% label: Radius of flats
#% answer: 0.0
#% multiple: no
#% guisection: Input
#%end

#%option
#% key: smooth
#% type: double
#% description: Smoothing radius
#% label: Smoothing radius
#% answer: 0.0
#% multiple: no
#% guisection: Input
#%end

#%option
#% key: spacing
#% type: double
#% description: Point spacing along lines
#% label: Point spacing along lines
#% answer: 1.0
#% multiple: no
#% guisection: Input
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

    # parse input coordinates
    coordinates = coordinates.split(',')
    cx = coordinates[::2]
    cy = coordinates[1::2]
    cz = z.split(',')
    if len(cz) > 1 and len(cz) != len(cx):
        grass.warning(
            'Number of z-values does not match xy-coordinates!'
            )

    # convert coordinates with constant z value
    if len(cz) == 1:
        coordinates = (
            "\n".join([f'{x},{y},{z}' for x, y in zip(cx, cy)])
            )
        attractors = coordinates2D(coordinates)

    # convert coordinates with list of z values
    elif len(cz) > 1:
        coordinates = (
            [f'{x},{y},{z}' for x, y, z in zip(cx, cy, cz)]
            )
        attractors = coordinates3D(coordinates)

    return attractors

def coordinates2D(coordinates):

    # create list
    attractors = []

    # create temporary raster
    attractor = grass.append_node_pid(f'attractor')
    atexit.register(clean, attractor)

    # convert to raster
    grass.write_command(
        'r.in.xyz',
        input='-',
        output=attractor,
        separator='comma',
        stdin=coordinates,
        overwrite=True
        )

    # append to list
    attractors.append(attractor)

    return attractors

def coordinates3D(coordinates):

    # create list
    attractors = []

    # convert each coordinate to raster
    n = len(coordinates)    
    for index in range(n):

        # create temporary raster
        attractor = grass.append_node_pid(f'attractor_{index + 1}')
        atexit.register(clean, attractor)
        
        # convert to raster
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
    
def convert_points(points, mode, z , layer):

    # create list
    attractors = []

    # get info
    info = grass.parse_command(
        'v.info',
        map=points,
        flags='t'
        )

    # convert 2D points
    if info['map3d'] == '0' and mode != 'relative':
        
        # create temporary raster
        attractor = grass.append_node_pid(f'attractor')
        atexit.register(clean, attractor)
        
        # convert to raster
        grass.run_command(
            'v.to.rast',
            input=points,
            output=attractor,
            use='val',
            value=z,
            overwrite=True,
            superquiet=True
            )

        # append to list
        attractors.append(attractor)

    # convert relative points
    elif info['map3d'] == '0' and mode == 'relative':

        # convert each point to raster
        n = info['points']
        for index in range(1, int(n)+1):
            attractor = f'attractor_{index}'
            attractor = grass.append_node_pid(attractor)
            atexit.register(clean, attractor)
            grass.run_command(
                'v.to.rast',
                input=points,
                layer=layer,
                cats=index,
                output=attractor,
                use='val',
                value=z,
                overwrite=True,
                superquiet=True
                )

            # append to list
            attractors.append(attractor)

    # convert 3D points
    elif info['map3d'] == '1':

        # convert each point to raster
        n = info['points']
        for index in range(1, int(n)+1):
            attractor = f'attractor_{index}'
            attractor = grass.append_node_pid(attractor)
            atexit.register(clean, attractor)
            grass.run_command(
                'v.to.rast',
                input=points,
                layer=layer,
                cats=index,
                output=attractor,
                use='z',
                overwrite=True,
                superquiet=True
                )

            # append to list
            attractors.append(attractor)
    
    return attractors

def convert_lines(lines, spacing):

    # convert lines to points
    points = grass.append_node_pid('points')
    atexit.register(clean, points)
    grass.run_command(
        'v.to.points',
        input=lines,
        output=points,
        dmax=spacing,
        overwrite=True,
        superquiet=True
        )

    return points

def flats(attractor, flat):

    # create temporary raster
    buffer = grass.append_node_pid('buffer')
    atexit.register(clean, buffer)
    
    # grow attractor
    grass.run_command(
        'r.buffer',
        input=attractor,
        output=buffer,
        distances=flat,
        overwrite=True,
        superquiet=True
        )
    info = grass.parse_command(
        'r.info',
        map=attractor,
        flags=['s']
        )
    z = info['max']
    grass.mapcalc(
        f'{attractor} = if(isnull({buffer}), null(), {z})',
        overwrite=True,
        superquiet=True
        )

    return attractor

def distance(attractor, elevation, mode):

    # create temporary rasters
    dxy = grass.append_node_pid('dxy')
    dz = grass.append_node_pid('dz')
    atexit.register(clean, [dxy, dz])

    # set relative or absolute attractors
    if mode == 'relative':
        grass.mapcalc(
            f'{attractor}'
            f'= if(isnull({attractor}),'
            f'null(),'
            f'{elevation} + {attractor})',
            overwrite=True
            )

    # calculate horizontal distance field
    grass.run_command(
        'r.grow.distance',
        input=attractor,
        distance=dxy,
        value=dz,
        overwrite=True,
        superquiet=True
        )

    # calculate vertical distance field
    grass.mapcalc(
        f'{dz} = {dz} - {elevation}',
        overwrite=True
        )

    return dxy, dz

def linear_decay(dz, dxy, rate):

    """
    f(t) = C - r * t
    z = A - 1/R * r
    """
    
    # create temporary rasters
    decay = grass.append_node_pid('decay')
    atexit.register(clean, decay)
    growth = grass.append_node_pid('growth')
    atexit.register(clean, decay)

    # calculate growth
    growth = 'growth'
    grass.mapcalc(
        f'{growth} = {dz} - (-{rate}) * {dxy}',
        overwrite=True
        )

    # calculate decay
    grass.mapcalc(
        f'{decay} = {dz} - {rate} * {dxy}',
        overwrite=True
        )

    return growth, decay
  
def exponential_decay(dz, dxy, rate):
    
    """
    z = z0 * e^(-lamba * t)
    """

    # create temporary rasters
    decay = grass.append_node_pid('decay')
    atexit.register(clean, decay)
    growth = grass.append_node_pid('growth')
    atexit.register(clean, decay)

    # calculate decay and decay
    grass.mapcalc(
        f'{decay} = {dz} * exp(2.71828, (-{rate} * {dxy}))',
        overwrite=True
        )
    growth = decay

    return growth, decay

def decay_fuction(function, dz, dxy, rate):

    # determine decay function
    if function == 'linear':
        growth, decay = linear_decay(dz, dxy, rate)
    if function == 'exponential':
        growth, decay = exponential_decay(dz, dxy, rate)

    return growth, decay

def earthworking(earthwork, elevation, growth, decay, operation):

    # cut operation
    if operation == 'cut':

        # model earthworks
        grass.mapcalc(
            f'{earthwork}'
            f'= if({elevation} + {decay} <= {elevation},'
            f'{elevation} + {decay},'
            f'{elevation})',
            overwrite=True
            )

    # fill operation
    if operation == 'fill':

        # model earthworks
        grass.mapcalc(
            f'{earthwork}'
            f'= if({elevation} + {decay} >= {elevation},'
            f'{elevation} + {decay},'
            f'{elevation})',
            overwrite=True
            )

    # cut-fill operation
    if operation == 'cutfill':

        # model earthworks
        grass.mapcalc(
            f'{earthwork}'
            f'= if({elevation} + {decay} >= {elevation},'
            f'{elevation} + {decay},'
            f'if({elevation} + {growth} <= {elevation},'
            f'{elevation} + {growth},'
            f'{elevation}))',
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

def smoothing(raster, smooth):

    # set variables
    neighborhood = int(smooth * 2)
    if neighborhood % 2 == 0:
        neighborhood += 1

    # smooth raster
    grass.run_command(
        'r.neighbors',
        input=raster,
        output=raster,
        size=neighborhood,
        method='average',
        flags='c',
        overwrite=True,
        superquiet=True
        )

def postprocess(earthworks):

    # set colors
    grass.run_command(
        'r.colors',
        map=earthworks,
        color='viridis',
        superquiet=True
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
    mode = options['mode']
    operation = options['operation']
    function = options['function']
    rate = abs(float(options['rate']))
    raster = options['raster']
    points = options['points']
    lines = options['lines']
    coordinates = options['coordinates']
    z = options['z']
    flat = float(options['flat'])
    smooth = float(options['smooth'])
    spacing = options['spacing']

    # convert inputs
    if raster:
        attractors = convert_raster(raster)
    elif coordinates:
        attractors = convert_coordinates(coordinates, z)
    elif points:
        attractors = convert_points(points, mode, z, 1)
    elif lines:
        points = convert_lines(lines, spacing)
        attractors = convert_points(points, mode, z, 2)
    else:
        grass.error(
            'An input raster, vector, or set of coordinates is required!'
            )

    # model earthworks for 2D attractors
    if len(attractors) == 1:

        # print mode
        grass.message('2D Mode')
        
        # set variable
        attractor = attractors[0]

        # model earthwork
        if flat > 0.0:
            attractor = flats(attractor, flat)
        dxy, dz = distance(attractor, elevation, mode)
        growth, decay = decay_fuction(function, dz, dxy, rate)
        smoothing(growth, smooth)
        smoothing(decay, smooth)
        earthworking(earthworks, elevation, growth, decay, operation)
        
        # postprocessing
        postprocess(earthworks)

    # model earthworks for 3D attractors
    if len(attractors) > 1:

        # print mode
        grass.message('3D Mode')
        
        # iterate through inputs
        landforms = []
        for attractor in attractors:

            # create temporary rasters
            index = attractor.split('_', 2)
            earthwork = f'earthwork_{index[1]}'
            earthwork = grass.append_node_pid(earthwork)
            atexit.register(clean, earthwork)

            # model each earthwork
            if flat > 0.0:
                attractor = flats(attractor, flat)
            dxy, dz = distance(attractor, elevation, mode)
            growth, decay = decay_fuction(function, dz, dxy, rate)
            smoothing(growth, smooth)
            smoothing(decay, smooth)
            earthworking(earthwork, elevation, growth, decay, operation)
            landforms.append(earthwork)

        # model earthworks
        series(landforms, earthworks)
        
        # postprocessing
        postprocess(earthworks)


if __name__ == "__main__":
    sys.exit(main())
