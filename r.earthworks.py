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
# % answer: earthworks
# %end

# %option G_OPT_R_OUTPUT
# % key: volume
# % description: Volumetric change
# % label: Volume
# % required: no
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

#%flag
#% key: p
#% description: Print volume
#%end

# import libraries
import grass.script as grass
import multiprocessing
from itertools import repeat
import sys
import atexit
import math

# set global variables
processes = multiprocessing.cpu_count()
temporary = []

def clean(temporary):

    # remove temporary rasters
    try:
        grass.run_command(
            'g.remove',
            type='raster',
            name=[temporary],
            flags='f',
            superquiet=True
            )
    except:
        pass

def convert_raster(raster):

    # parse raster
    data = grass.parse_command(
        'r.stats',
        input=raster,
        flags=['gn']
        )

    # find coordinates
    coordinates = []
    for datum in data.keys():
        xyz = datum.split(' ')
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        coordinate = [x, y, z]
        coordinates.append(coordinate)
    
    return coordinates

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
        coordinates = [
            [float(x), float(y), float(z)]
            for x, y
            in zip(cx, cy)
            ]

    # # convert coordinates with list of z values
    elif len(cz) > 1:
        coordinates = [
            [float(x), float(y), float(z)]
            for x, y, z
            in zip(cx, cy, cz)
            ]

    return coordinates
    
def convert_points(points, mode, z):

    # create list
    coordinates = []

    # get info
    info = grass.parse_command(
        'v.info',
        map=points,
        flags='t'
        )

    # convert 2D points
    if info['map3d'] == '0':

        # parse points
        data = grass.parse_command(
            'v.to.db',
            map=points,
            option='coor',
            separator='comma',
            flags='p',
            overwrite=True,
            superquiet=True
            )

        # find coordinates
        coordinates = []
        for datum in data.keys():
            xyz = datum.split(',')
            x = float(xyz[1])
            y = float(xyz[2])
            z = float(z)
            coordinate = [x, y, z]
            coordinates.append(coordinate)

    # convert 3D points
    elif info['map3d'] == '1':

        # parse points
        data = grass.parse_command(
            'v.to.db',
            map=points,
            option='coor',
            separator='comma',
            flags='p',
            overwrite=True,
            superquiet=True
            )

        # find coordinates
        coordinates = []
        for datum in data.keys():
            xyz = datum.split(',')
            x = float(xyz[1])
            y = float(xyz[2])
            z = float(xyz[3])
            coordinate = [x, y, z]
            coordinates.append(coordinate)
    
    return coordinates

def convert_lines(lines, z):

    # get info
    info = grass.parse_command(
        'v.info',
        map=lines,
        flags='t'
        )

    # convert 2D lines
    if info['map3d'] == '0':

        # convert lines to raster
        raster = grass.append_uuid('raster')
        temporary.append(raster)
        grass.run_command(
            'v.to.rast',
            input=lines,
            output=raster,
            use='value',
            value=z,
            overwrite=True,
            superquiet=True
            )

    # convert 3D lines
    elif info['map3d'] == '1':

        # convert 3D lines to raster
        points = grass.append_uuid('points')
        raster = grass.append_uuid('raster')
        temporary.extend([points, raster])
        region = grass.parse_command('g.region', flags=['g'])
        nsres = float(region['nsres'])
        ewres = float(region['ewres'])
        res = math.sqrt(nsres * ewres)
        grass.run_command(
            'v.to.points',
            input=lines,
            output=points,
            dmax=res,
            overwrite=True,
            superquiet=True
            )
        grass.run_command(
            'v.to.rast',
            input=points,
            output=raster,
            use='z',
            overwrite=True,
            superquiet=True
            )

    return raster

def earthworking(
    coordinate,
    elevation,
    flat,
    mode,
    function,
    rate,
    operation,
    earthworks,
    cut,
    fill
    ):

    # parse coordinate
    x = coordinate[0]
    y = coordinate[1]
    z = coordinate[2]

    # calculate distance
    dxy = (
        f'dxy'
        f'= sqrt(((x() - {x})'
        f'* (x() - {x}))'
        f'+ ((y() - {y})'
        f'* (y() - {y})))'
        )

    # calculate flats
    if flat > 0.0:
        flat = f'dxy = if(dxy <= {flat}, 0, dxy - {flat})'
    else:
        flat = f'dxy = {dxy}'

    # caclulate elevation relative to the surface
    if mode == 'relative':
        dz = f'dz = {z}'

    # caclulate absolute elevation above surface
    elif mode == 'absolute': 
        dz = f'dz = {z} - {elevation}'
    
    # calculate linear function
    if function == 'linear':
        # z = C - r * t
        growth = f'growth = dz - (-{rate}) * dxy'
        decay = f'decay = dz - {rate} * dxy'

    # calculate exponential function
    elif function == 'exponential':
        # z = z0 * e^(-lamba * t)
        growth = f'growth = dz * exp(2.71828, (-{rate} * dxy))'
        decay = f'decay = growth'

    # model cut operation
    if operation == 'cut':
        operation = (
            f'if({elevation} + growth <= {elevation},'
            f'{elevation} + growth,'
            f'{elevation})'
            )
        grass.mapcalc(
            f'{cut}'
            f'= eval('
            f'{dxy},'
            f'{flat},'
            f'{dz},'
            f'{growth},'
            f'{operation}'
            f')',
            overwrite=True
            )

    # model fill operation
    elif operation == 'fill':
        operation = (
            f'if({elevation} + decay >= {elevation},'
            f'{elevation} + decay,'
            f'{elevation})'
            )
        grass.mapcalc(
            f'{fill}'
            f'= eval('
            f'{dxy},'
            f'{flat},'
            f'{dz},'
            f'{decay},'
            f'{operation}'
            f')',
            overwrite=True
            )

    # model cut-fill operation
    elif operation == 'cutfill':

        # model cut
        operation = (
            f'if({elevation} + growth <= {elevation},'
            f'{elevation} + growth,'
            f'null())'
            )
        grass.mapcalc(
            f'{cut}'
            f'= eval('
            f'{dxy},'
            f'{flat},'
            f'{dz},'
            f'{growth},'
            f'{operation}'
            f')',
            overwrite=True
            )

        # model fill
        operation = (
            f'if({elevation} + decay >= {elevation},'
            f'{elevation} + decay,'
            f'null())'
            )
        grass.mapcalc(
            f'{fill}'
            f'= eval('
            f'{dxy},'
            f'{flat},'
            f'{dz},'
            f'{decay},'
            f'{operation}'
            f')',
            overwrite=True
            )

def operations(
    coordinate,
    elevation,
    flat,
    mode,
    function,
    rate,
    operation,
    earthworks,
    ids,
    cuts,
    fills
    ):

    # create temporary rasters
    if operation == 'cut':
        cut = grass.append_uuid('cut')
        fill = None
    elif operation == 'fill':
        fill = grass.append_uuid('fill')
        cut = None
    elif operation == 'cutfill':
        cut = grass.append_uuid('cut')
        fill = grass.append_uuid('fill')
    ids.extend([cut, fill])

    # model each operation
    earthworking(
        coordinate,
        elevation,
        flat,
        mode,
        function,
        rate,
        operation,
        earthworks,
        cut,
        fill
        )

    # append to lists of operations
    if operation == 'cut':
        cuts.append(cut)
    elif operation == 'fill':
        fills.append(fill)
    elif operation == 'cutfill':
        cuts.append(cut)
        fills.append(fill)

def series(operation, cuts, fills, elevation, earthworks):

    # model net cut
    if operation == 'cut':

        # calculate minimum cut
        grass.run_command(
            'r.series',
            input=cuts,
            output=earthworks,
            method='minimum',
            overwrite=True
            )

    # model net fill
    elif operation == 'fill':

        # calculate maximum fill
        grass.run_command(
            'r.series',
            input=fills,
            output=earthworks,
            method='maximum',
            overwrite=True
            )

    # model net cut and fill
    elif operation == 'cutfill':

        # calculate minimum cut
        cut = grass.append_uuid('cut')
        temporary.append(cut)
        grass.run_command(
            'r.series',
            input=cuts,
            output=cut,
            method='minimum',
            overwrite=True
            )

        # calculate maximum fill
        fill = grass.append_uuid('fill')
        temporary.append(fill)
        grass.run_command(
            'r.series',
            input=fills,
            output=fill,
            method='maximum',
            overwrite=True
            )

        # calculate sum of cut and fill
        cutfill = grass.append_uuid('cutfill')
        temporary.append(cutfill)
        grass.run_command(
            'r.series',
            input=[cut, fill],
            output=cutfill,
            method='sum',
            overwrite=True
            )

        # calculate net cut and fill
        grass.mapcalc(
            f'{earthworks}'
            f'= if(isnull({cutfill}),'
            f'{elevation},'
            f'{cutfill})',
            overwrite=True
            )

def difference(elevation, earthworks, volume):

    # create temporary raster
    if not volume:
        volume = grass.append_uuid('volume')
        temporary.append(volume)

    # model earthworks
    grass.mapcalc(
        f'{volume} = {earthworks} - {elevation}',
        overwrite=True
        )

    # set color gradient
    grass.run_command(
        'r.colors',
        map=volume,
        color='viridis',
        superquiet=True
        )

    # save history
    grass.raster_history(
        volume,
        overwrite=True
        )

    return volume

def print_difference(operation, volume):

    # find resolution
    region = grass.parse_command('g.region', flags=['g'])
    nsres = float(region['nsres'])
    ewres = float(region['ewres'])

    # find units
    projection = grass.parse_command('g.proj', flags=['g'])
    units = projection.get('units', 'units')

    # print net change
    if operation == 'cutfill':
        univar = grass.parse_command('r.univar',
            map=volume,
            separator='newline',
            flags='g')
        net = nsres * ewres * float(univar['sum'])
        if math.isnan(net):
            net = 0
        grass.info(f'Net change: {net} cubic {units.lower()}')

    # print fill
    if operation in {'cutfill', 'fill'}:
        fill = grass.append_uuid('fill')
        temporary.append(fill)
        grass.mapcalc(
            f'{fill} = if({volume} > 0, {volume}, null())',
            overwrite=True
            )
        univar = grass.parse_command('r.univar',
            map=fill,
            separator='newline',
            flags='g')
        net = nsres * ewres * float(univar['sum'])
        if math.isnan(net):
            net = 0.0
        grass.info(f'Net fill: {net} cubic {units.lower()}')

    # print cut
    if operation in {'cutfill', 'cut'}:
        cut = grass.append_uuid('cut')
        temporary.append(cut)
        grass.mapcalc(
            f'{cut} = if({volume} < 0, {volume}, null())',
            overwrite=True
            )
        univar = grass.parse_command('r.univar',
            map=cut,
            separator='newline',
            flags='g')
        net = nsres * ewres * float(univar['sum'])
        if math.isnan(net):
            net = 0.0
        grass.info(f'Net cut: {net} cubic {units.lower()}')

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
    volume = options['volume']
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
    print_volume = flags['p']

    # run processes
    try:

        # convert inputs
        if raster:
            coordinates = convert_raster(raster)
        elif coordinates:
            coordinates = convert_coordinates(coordinates, z)
        elif points:
            coordinates = convert_points(points, mode, z)
        elif lines:
            raster = convert_lines(lines, z)
            coordinates = convert_raster(raster)
        else:
            grass.error(
                'A raster, vector, or set of coordinates is required!'
                )

        # run earthworking operations in parallel
        with multiprocessing.Manager() as manager:

            # manage lists
            ids = manager.list()
            cuts = manager.list()
            fills = manager.list()

            # set iterables
            iterables = zip(
                coordinates,
                repeat(elevation),
                repeat(flat),
                repeat(mode),
                repeat(function),
                repeat(rate),
                repeat(operation),
                repeat(earthworks),
                repeat(ids),
                repeat(cuts),
                repeat(fills)
                )

            # run operations
            with multiprocessing.Pool(processes=processes) as pool:
                pool.starmap(operations, iterables)
            
            # register temporary maps
            temporary.extend(ids)

            # model earthworks
            series(operation, cuts, fills, elevation, earthworks)

            # calculate volume
            if volume or print_volume:
                volume = difference(elevation, earthworks, volume)

            # print volume
            if print_volume:
                print_difference(operation, volume)

            # postprocessing
            postprocess(earthworks)

    # clean up
    finally:
        atexit.register(clean, temporary)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
