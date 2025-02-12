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

#%flag
#% key: p
#% description: Print volume
#%end

import grass.script as grass
import sys
import atexit
import math
import time
start_time = time.time()

def colors():

    gradient = """\
    0.0% 126:23:0
    0.4% 127:26:1
    0.4% 127:26:1
    0.8% 128:29:2
    0.8% 128:29:2
    1.2% 129:32:3
    1.2% 129:32:3
    1.6% 130:34:4
    1.6% 130:34:4
    2.0% 131:37:4
    2.0% 131:37:4
    2.4% 132:39:5
    2.4% 132:39:5
    2.7% 133:42:6
    2.7% 133:42:6
    3.1% 134:44:6
    3.1% 134:44:6
    3.5% 135:46:7
    3.5% 135:46:7
    3.9% 136:48:8
    3.9% 136:48:8
    4.3% 138:50:8
    4.3% 138:50:8
    4.7% 139:52:9
    4.7% 139:52:9
    5.1% 140:54:10
    5.1% 140:54:10
    5.5% 141:56:11
    5.5% 141:56:11
    5.9% 142:58:11
    5.9% 142:58:11
    6.3% 143:60:12
    6.3% 143:60:12
    6.7% 144:62:13
    6.7% 144:62:13
    7.1% 144:64:14
    7.1% 144:64:14
    7.5% 145:66:15
    7.5% 145:66:15
    7.8% 146:68:15
    7.8% 146:68:15
    8.2% 147:70:16
    8.2% 147:70:16
    8.6% 148:71:17
    8.6% 148:71:17
    9.0% 149:73:18
    9.0% 149:73:18
    9.4% 150:75:18
    9.4% 150:75:18
    9.8% 151:77:19
    9.8% 151:77:19
    10.2% 152:78:20
    10.2% 152:78:20
    10.6% 153:80:20
    10.6% 153:80:20
    11.0% 153:82:21
    11.0% 153:82:21
    11.4% 154:83:22
    11.4% 154:83:22
    11.8% 155:85:23
    11.8% 155:85:23
    12.2% 156:87:23
    12.2% 156:87:23
    12.5% 157:88:24
    12.5% 157:88:24
    12.9% 158:90:25
    12.9% 158:90:25
    13.3% 158:92:25
    13.3% 158:92:25
    13.7% 159:93:26
    13.7% 159:93:26
    14.1% 160:95:27
    14.1% 160:95:27
    14.5% 161:97:28
    14.5% 161:97:28
    14.9% 162:98:28
    14.9% 162:98:28
    15.3% 162:100:29
    15.3% 162:100:29
    15.7% 163:101:30
    15.7% 163:101:30
    16.1% 164:103:30
    16.1% 164:103:30
    16.5% 165:104:31
    16.5% 165:104:31
    16.9% 166:106:32
    16.9% 166:106:32
    17.3% 166:108:32
    17.3% 166:108:32
    17.6% 167:109:33
    17.6% 167:109:33
    18.0% 168:111:34
    18.0% 168:111:34
    18.4% 169:112:35
    18.4% 169:112:35
    18.8% 169:114:35
    18.8% 169:114:35
    19.2% 170:115:36
    19.2% 170:115:36
    19.6% 171:117:37
    19.6% 171:117:37
    20.0% 172:119:38
    20.0% 172:119:38
    20.4% 173:120:38
    20.4% 173:120:38
    20.8% 173:122:39
    20.8% 173:122:39
    21.2% 174:124:40
    21.2% 174:124:40
    21.6% 175:125:41
    21.6% 175:125:41
    22.0% 176:127:42
    22.0% 176:127:42
    22.4% 176:128:43
    22.4% 176:128:43
    22.7% 177:130:44
    22.7% 177:130:44
    23.1% 178:132:45
    23.1% 178:132:45
    23.5% 179:134:46
    23.5% 179:134:46
    23.9% 180:135:47
    23.9% 180:135:47
    24.3% 181:137:48
    24.3% 181:137:48
    24.7% 181:139:49
    24.7% 181:139:49
    25.1% 182:140:50
    25.1% 182:140:50
    25.5% 183:142:51
    25.5% 183:142:51
    25.9% 184:144:52
    25.9% 184:144:52
    26.3% 185:146:53
    26.3% 185:146:53
    26.7% 186:148:55
    26.7% 186:148:55
    27.1% 186:149:56
    27.1% 186:149:56
    27.5% 187:151:57
    27.5% 187:151:57
    27.8% 188:153:59
    27.8% 188:153:59
    28.2% 189:155:60
    28.2% 189:155:60
    28.6% 190:157:62
    28.6% 190:157:62
    29.0% 191:159:64
    29.0% 191:159:64
    29.4% 192:161:65
    29.4% 192:161:65
    29.8% 193:163:67
    29.8% 193:163:67
    30.2% 193:165:69
    30.2% 193:165:69
    30.6% 194:166:71
    30.6% 194:166:71
    31.0% 195:168:72
    31.0% 195:168:72
    31.4% 196:170:74
    31.4% 196:170:74
    31.8% 197:172:76
    31.8% 197:172:76
    32.2% 198:174:79
    32.2% 198:174:79
    32.5% 199:176:81
    32.5% 199:176:81
    32.9% 199:178:83
    32.9% 199:178:83
    33.3% 200:180:85
    33.3% 200:180:85
    33.7% 201:182:88
    33.7% 201:182:88
    34.1% 202:184:90
    34.1% 202:184:90
    34.5% 203:186:93
    34.5% 203:186:93
    34.9% 203:188:95
    34.9% 203:188:95
    35.3% 204:190:98
    35.3% 204:190:98
    35.7% 205:192:100
    35.7% 205:192:100
    36.1% 206:194:103
    36.1% 206:194:103
    36.5% 206:196:106
    36.5% 206:196:106
    36.9% 207:198:109
    36.9% 207:198:109
    37.3% 207:200:111
    37.3% 207:200:111
    37.6% 208:202:114
    37.6% 208:202:114
    38.0% 208:204:117
    38.0% 208:204:117
    38.4% 209:205:120
    38.4% 209:205:120
    38.8% 209:207:123
    38.8% 209:207:123
    39.2% 210:209:126
    39.2% 210:209:126
    39.6% 210:211:129
    39.6% 210:211:129
    40.0% 210:212:132
    40.0% 210:212:132
    40.4% 210:214:135
    40.4% 210:214:135
    40.8% 210:215:138
    40.8% 210:215:138
    41.2% 210:217:141
    41.2% 210:217:141
    41.6% 210:218:144
    41.6% 210:218:144
    42.0% 210:220:147
    42.0% 210:220:147
    42.4% 210:221:150
    42.4% 210:221:150
    42.7% 210:222:152
    42.7% 210:222:152
    43.1% 209:223:155
    43.1% 209:223:155
    43.5% 209:225:158
    43.5% 209:225:158
    43.9% 209:226:161
    43.9% 209:226:161
    44.3% 208:227:163
    44.3% 208:227:163
    44.7% 208:228:166
    44.7% 208:228:166
    45.1% 207:229:168
    45.1% 207:229:168
    45.5% 206:229:171
    45.5% 206:229:171
    45.9% 205:230:173
    45.9% 205:230:173
    46.3% 204:231:176
    46.3% 204:231:176
    46.7% 204:231:178
    46.7% 204:231:178
    47.1% 203:232:180
    47.1% 203:232:180
    47.5% 201:233:182
    47.5% 201:233:182
    47.8% 200:233:184
    47.8% 200:233:184
    48.2% 199:233:186
    48.2% 199:233:186
    48.6% 198:234:188
    48.6% 198:234:188
    49.0% 196:234:190
    49.0% 196:234:190
    49.4% 195:234:192
    49.4% 195:234:192
    49.8% 193:234:194
    49.8% 193:234:194
    50.2% 192:234:195
    50.2% 192:234:195
    50.6% 190:234:197
    50.6% 190:234:197
    51.0% 189:234:198
    51.0% 189:234:198
    51.4% 187:234:200
    51.4% 187:234:200
    51.8% 185:234:201
    51.8% 185:234:201
    52.2% 183:234:202
    52.2% 183:234:202
    52.5% 181:234:204
    52.5% 181:234:204
    52.9% 179:233:205
    52.9% 179:233:205
    53.3% 177:233:206
    53.3% 177:233:206
    53.7% 175:232:207
    53.7% 175:232:207
    54.1% 173:232:208
    54.1% 173:232:208
    54.5% 171:231:209
    54.5% 171:231:209
    54.9% 169:231:210
    54.9% 169:231:210
    55.3% 166:230:210
    55.3% 166:230:210
    55.7% 164:229:211
    55.7% 164:229:211
    56.1% 162:229:212
    56.1% 162:229:212
    56.5% 159:228:212
    56.5% 159:228:212
    56.9% 157:227:213
    56.9% 157:227:213
    57.3% 155:226:213
    57.3% 155:226:213
    57.6% 152:225:214
    57.6% 152:225:214
    58.0% 149:224:214
    58.0% 149:224:214
    58.4% 147:223:214
    58.4% 147:223:214
    58.8% 144:222:215
    58.8% 144:222:215
    59.2% 142:221:215
    59.2% 142:221:215
    59.6% 139:220:215
    59.6% 139:220:215
    60.0% 137:218:215
    60.0% 137:218:215
    60.4% 134:217:215
    60.4% 134:217:215
    60.8% 131:216:215
    60.8% 131:216:215
    61.2% 129:215:215
    61.2% 129:215:215
    61.6% 126:213:215
    61.6% 126:213:215
    62.0% 123:212:215
    62.0% 123:212:215
    62.4% 121:210:215
    62.4% 121:210:215
    62.7% 118:209:215
    62.7% 118:209:215
    63.1% 116:207:214
    63.1% 116:207:214
    63.5% 113:206:214
    63.5% 113:206:214
    63.9% 110:204:214
    63.9% 110:204:214
    64.3% 108:203:214
    64.3% 108:203:214
    64.7% 105:201:213
    64.7% 105:201:213
    65.1% 103:199:213
    65.1% 103:199:213
    65.5% 100:198:213
    65.5% 100:198:213
    65.9% 98:196:212
    65.9% 98:196:212
    66.3% 96:195:212
    66.3% 96:195:212
    66.7% 93:193:211
    66.7% 93:193:211
    67.1% 91:191:211
    67.1% 91:191:211
    67.5% 89:189:210
    67.5% 89:189:210
    67.8% 87:188:210
    67.8% 87:188:210
    68.2% 85:186:209
    68.2% 85:186:209
    68.6% 83:184:209
    68.6% 83:184:209
    69.0% 81:183:208
    69.0% 81:183:208
    69.4% 79:181:208
    69.4% 79:181:208
    69.8% 77:179:207
    69.8% 77:179:207
    70.2% 75:178:206
    70.2% 75:178:206
    70.6% 73:176:206
    70.6% 73:176:206
    71.0% 71:174:205
    71.0% 71:174:205
    71.4% 70:172:204
    71.4% 70:172:204
    71.8% 68:171:204
    71.8% 68:171:204
    72.2% 67:169:203
    72.2% 67:169:203
    72.5% 65:167:203
    72.5% 65:167:203
    72.9% 64:166:202
    72.9% 64:166:202
    73.3% 62:164:201
    73.3% 62:164:201
    73.7% 61:162:201
    73.7% 61:162:201
    74.1% 60:161:200
    74.1% 60:161:200
    74.5% 58:159:199
    74.5% 58:159:199
    74.9% 57:157:199
    74.9% 57:157:199
    75.3% 56:156:198
    75.3% 56:156:198
    75.7% 55:154:197
    75.7% 55:154:197
    76.1% 54:152:197
    76.1% 54:152:197
    76.5% 53:151:196
    76.5% 53:151:196
    76.9% 52:149:195
    76.9% 52:149:195
    77.3% 51:148:195
    77.3% 51:148:195
    77.6% 50:146:194
    77.6% 50:146:194
    78.0% 49:144:193
    78.0% 49:144:193
    78.4% 48:143:193
    78.4% 48:143:193
    78.8% 48:141:192
    78.8% 48:141:192
    79.2% 47:140:191
    79.2% 47:140:191
    79.6% 46:138:191
    79.6% 46:138:191
    80.0% 45:136:190
    80.0% 45:136:190
    80.4% 45:135:189
    80.4% 45:135:189
    80.8% 44:133:189
    80.8% 44:133:189
    81.2% 43:132:188
    81.2% 43:132:188
    81.6% 43:130:187
    81.6% 43:130:187
    82.0% 42:129:187
    82.0% 42:129:187
    82.4% 41:127:186
    82.4% 41:127:186
    82.7% 41:126:185
    82.7% 41:126:185
    83.1% 40:124:185
    83.1% 40:124:185
    83.5% 40:122:184
    83.5% 40:122:184
    83.9% 39:121:183
    83.9% 39:121:183
    84.3% 38:119:183
    84.3% 38:119:183
    84.7% 38:118:182
    84.7% 38:118:182
    85.1% 37:116:181
    85.1% 37:116:181
    85.5% 37:115:181
    85.5% 37:115:181
    85.9% 36:113:180
    85.9% 36:113:180
    86.3% 36:111:179
    86.3% 36:111:179
    86.7% 35:110:179
    86.7% 35:110:179
    87.1% 35:108:178
    87.1% 35:108:178
    87.5% 34:106:177
    87.5% 34:106:177
    87.8% 34:105:176
    87.8% 34:105:176
    88.2% 33:103:176
    88.2% 33:103:176
    88.6% 33:102:175
    88.6% 33:102:175
    89.0% 32:100:174
    89.0% 32:100:174
    89.4% 32:98:174
    89.4% 32:98:174
    89.8% 31:96:173
    89.8% 31:96:173
    90.2% 30:95:172
    90.2% 30:95:172
    90.6% 30:93:171
    90.6% 30:93:171
    91.0% 29:91:171
    91.0% 29:91:171
    91.4% 29:90:170
    91.4% 29:90:170
    91.8% 28:88:169
    91.8% 28:88:169
    92.2% 27:86:168
    92.2% 27:86:168
    92.5% 27:84:168
    92.5% 27:84:168
    92.9% 26:83:167
    92.9% 26:83:167
    93.3% 25:81:166
    93.3% 25:81:166
    93.7% 25:79:165
    93.7% 25:79:165
    94.1% 24:77:164
    94.1% 24:77:164
    94.5% 23:76:164
    94.5% 23:76:164
    94.9% 22:74:163
    94.9% 22:74:163
    95.3% 21:72:162
    95.3% 21:72:162
    95.7% 20:70:161
    95.7% 20:70:161
    96.1% 19:68:160
    96.1% 19:68:160
    96.5% 18:66:160
    96.5% 18:66:160
    96.9% 17:64:159
    96.9% 17:64:159
    97.3% 15:63:158
    97.3% 15:63:158
    97.6% 14:61:157
    97.6% 14:61:157
    98.0% 12:59:156
    98.0% 12:59:156
    98.4% 11:57:156
    98.4% 11:57:156
    98.8% 9:55:155
    98.8% 9:55:155
    99.2% 7:53:154
    99.2% 7:53:154
    99.6% 5:51:153
    99.6% 5:51:153
    100.0% 3:49:152
    """
    return gradient

def clean(name):
    grass.run_command(
        'g.remove',
        type='raster,vector',
        name=name,
        flags='f',
        superquiet=True)

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

    # convert 2D line
    if info['map3d'] == '0':

        # convert lines to raster
        raster = grass.append_node_pid('raster')
        atexit.register(clean, raster)
        grass.run_command(
            'v.to.rast',
            input=lines,
            output=raster,
            use='value',
            value=z,
            overwrite=True,
            superquiet=True
            )

    # convert 2D line
    elif info['map3d'] == '1':

        # convert lines to raster
        raster = grass.append_node_pid('raster')
        atexit.register(clean, raster)
        grass.run_command(
            'v.to.rast',
            input=lines,
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
    procedure,
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
#        dz = f'dz = (-{z}*0.1) - {elevation}'
    
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
        if procedure == '2D':
            output = earthworks
        elif procedure == '3D':
            output = cut
        operation = (
            f'if({elevation} + growth <= {elevation},'
            f'{elevation} + growth,'
            f'{elevation})'
            )
        grass.mapcalc(
            f'{output}'
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
        if procedure == '2D':
            output = earthworks
        elif procedure == '3D':
            output = fill
        operation = (
            f'if({elevation} + decay >= {elevation},'
            f'{elevation} + decay,'
            f'{elevation})'
            )
        grass.mapcalc(
            f'{output}'
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
   
        if procedure == '2D':

            # model cut and fill
            operation = (
                f'if({elevation} + decay >= {elevation},'
                f'{elevation} + decay,'
                f'if({elevation} + growth <= {elevation},'
                f'{elevation} + growth,'
                f'{elevation}))'
                )

            # model earthworks
            grass.mapcalc(
                f'{earthworks}'
                f'= eval('
                f'{dxy},'
                f'{flat},'
                f'{dz},'
                f'{growth},'
                f'{decay},'
                f'{operation}'
                f')',
                overwrite=True
                )

        elif procedure == '3D': 

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

def series(operation, cuts, fills, elevation, earthworks):

    # model net fill
    if operation == 'fill':

        # calculate maximum fill
        fill = grass.append_node_pid('fill')
        atexit.register(clean, fill)
        grass.run_command(
            'r.series',
            input=fills,
            output=fill,
            method='maximum',
            overwrite=True
            )

        # calculate net fill
        grass.mapcalc(
            f'{earthworks}'
            f'= if(isnull({fill}),'
            f'{elevation},'
            f'{fill})',
            overwrite=True
            )

    # model net cut
    elif operation == 'cut':

        # calculate minimum cut
        cut = grass.append_node_pid('cut')
        atexit.register(clean, cut)
        grass.run_command(
            'r.series',
            input=cuts,
            output=cut,
            method='minimum',
            overwrite=True
            )

        # calculate net cut
        grass.mapcalc(
            f'{earthworks}'
            f'= if(isnull({cut}),'
            f'{elevation},'
            f'{cut})',
            overwrite=True
            )

    # model net cut and fill
    elif operation == 'cutfill':

        # calculate minimum cut
        cut = grass.append_node_pid('cut')
        atexit.register(clean, cut)
        grass.run_command(
            'r.series',
            input=cuts,
            output=cut,
            method='minimum',
            overwrite=True
            )

        # calculate maximum fill
        fill = grass.append_node_pid('fill')
        atexit.register(clean, fill)
        grass.run_command(
            'r.series',
            input=fills,
            output=fill,
            method='maximum',
            overwrite=True
            )

        # calculate net cut and fill
        grass.mapcalc(
            f'{earthworks}'
            f'= if(isnull({cut}) &&& isnull({fill}),'
            f'{elevation},'
            f'if(isnull({cut}),'
            f'{fill},'
            f'{cut}))',
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

def difference(elevation, earthworks, volume, gradient):

    # create temporary raster
    if not volume:
        volume = grass.append_node_pid('volume')
        atexit.register(clean, volume)

    # model earthworks
    grass.mapcalc(
        f'{volume} = {earthworks} - {elevation}',
        overwrite=True
        )

    # set color gradient
    grass.write_command(
        "r.colors",
        map=volume,
        rules="-",
        stdin=gradient,
        superquiet=True
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
        fill = grass.append_node_pid('fill')
        atexit.register(clean, fill)
        grass.mapcalc(
            f'{fill} = if({volume} > 0, volume, null())',
            overwrite=True
            )
        univar = grass.parse_command('r.univar',
            map=fill,
            separator='newline',
            flags='g')
        net = nsres * ewres * float(univar['sum'])
        if math.isnan(net):
            net = 0
        grass.info(f'Net fill: {net} cubic {units.lower()}')

    # print cut
    if operation in {'cutfill', 'cut'}:
        cut = grass.append_node_pid('cut')
        atexit.register(clean, cut)
        grass.mapcalc(
            f'{cut} = if({volume} < 0, volume, null())',
            overwrite=True
            )
        univar = grass.parse_command('r.univar',
            map=cut,
            separator='newline',
            flags='g')
        net = nsres * ewres * float(univar['sum'])
        if math.isnan(net):
            net = 0
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
    smooth = float(options['smooth'])
    spacing = options['spacing']
    print_volume = flags['p']

    # define color gradient
    gradient = colors()

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

    # model earthworks for 2D attractors
    if len(coordinates) == 1:

        # set 2D mode
        procedure = '2D'
        grass.message('2D Mode')
        
        # set variables
        coordinate = coordinates[0]

        # create temporary rasters
        cut = grass.append_node_pid('cut')
        atexit.register(clean, cut)
        fill = grass.append_node_pid('fill')
        atexit.register(clean, fill)

        # model earthwork
        earthworking(
            coordinate,
            elevation,
            flat,
            mode,
            function,
            rate,
            operation,
            procedure,
            earthworks,
            cut,
            fill
            ) 

    # model earthworks for 3D attractors
    elif len(coordinates) > 1:

        # set mode
        procedure = '3D'
        grass.message('3D Mode')
        
        # iterate through inputs
        cuts = []
        fills = [] 
        index = 0
        for coordinate in coordinates:

            # create temporary rasters
            cut = f'cut_{index}'
            cut = grass.append_node_pid(cut)
            atexit.register(clean, cut)
            fill = f'fill_{index}'
            fill = grass.append_node_pid(fill)
            atexit.register(clean, fill)
            index = index + 1

            # model each operation
            earthworking(
                coordinate,
                elevation,
                flat,
                mode,
                function,
                rate,
                operation,
                procedure,
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

        # model earthworks
        series(operation, cuts, fills, elevation, earthworks)

    # calculate volume
    if volume or print_volume:
        volume = difference(elevation, earthworks, volume, gradient)

    # print volume
    if print_volume:
        print_difference(operation, volume)

    # postprocessing
    postprocess(earthworks)

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    sys.exit(main())
