#!/usr/bin/env python
__author__    = 'Mike McCann'
__copyright__ = '2013'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'

__doc__ = '''

Master loader for all October 2013 SIMZ activities.  

Mike McCann
MBARI 24 October 2013

@var __date__: Date of last svn commit
@undocumented: __doc__ parser
@status: production
@license: GPL
'''

import os
import sys
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))      # So that CANON is found

from CANON import CANONLoader

cl = CANONLoader('stoqs_simz_oct2013', 'Sampling and Identification of Marine Zooplankton - October 2013')
startDatetime = datetime.datetime(2013, 10, 22)
endDatetime = datetime.datetime(2013, 10, 29)

# Aboard the Carson use zuma:
##cl.tdsBase = 'http://zuma.rc.mbari.org/thredds/'       
# On shore, use the odss server:
cl.tdsBase = 'http://odss.mbari.org/thredds/'
cl.dodsBase = cl.tdsBase + 'dodsC/'       

# 2-second decimated dorado data
cl.dorado_base = 'http://dods.mbari.org/opendap/data/auvctd/surveys/2013/netcdf/'   # Dorado archive
cl.dorado_files = [ 
                    'Dorado389_2013_295_00_295_00_decim.nc', 
                    'Dorado389_2013_295_01_295_01_decim.nc', 
                    'Dorado389_2013_296_00_296_00_decim.nc', 
                    'Dorado389_2013_296_01_296_01_decim.nc', 
                    'Dorado389_2013_297_01_297_01_decim.nc', 
                    'Dorado389_2013_297_02_297_02_decim.nc', 
                    'Dorado389_2013_298_00_298_00_decim.nc',
                    'Dorado389_2013_298_01_298_01_decim.nc',
                    'Dorado389_2013_301_02_301_02_decim.nc',
                    'Dorado389_2013_301_03_301_03_decim.nc',
                    'Dorado389_2013_301_04_301_04_decim.nc',
                  ]

# Spray glider - for just the duration of the campaign
cl.l_662_base = 'http://www.cencoos.org/thredds/dodsC/gliders/Line66/'
cl.l_662_files = ['OS_Glider_L_662_20130711_TS.nc']
cl.l_662_parms = ['TEMP', 'PSAL', 'FLU2']
cl.l_662_startDatetime = startDatetime
cl.l_662_endDatetime = endDatetime


# Rachel Carson Underway CTD
cl.rcuctd_base = cl.dodsBase + 'SIMZ_august2013/carson/uctd/'
cl.rcuctd_files = [ 
                    'simz2013plm06.nc', 'simz2013plm07.nc', 'simz2013plm08.nc', 'simz2013plm09.nc', 'simz2013plm10.nc',
                  ]
cl.rcuctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'wetstar' ]

# Rachel Carson Profile CTD
cl.pctdDir = 'CANON_october2013/Platforms/Ships/Rachel_Carson/pctd/'
cl.rcpctd_base = cl.dodsBase + cl.pctdDir
cl.rcpctd_files = [ 
                                                      'simz2013c19.nc', 'simz2013c20.nc',
'simz2013c21.nc', 'simz2013c22.nc', 'simz2013c23.nc', 'simz2013c24.nc', 'simz2013c25.nc',
'simz2013c26.nc', 'simz2013c27.nc', 'simz2013c28.nc', 'simz2013c29.nc', 'simz2013c30.nc',
'simz2013c31.nc', 'simz2013c32.nc', 'simz2013c33.nc', 'simz2013c34.nc', 'simz2013c35.nc', 'simz2013c35a.nc',
'simz2013c36.nc',
                      ]
cl.rcpctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'wetstar', 'oxygen' ]

# Mooring M1 Combined file produced by DPforSSDS processing - for just the duration of the campaign
cl.m1_base = 'http://dods.mbari.org/opendap/data/ssdsdata/deployments/m1/201309/'
cl.m1_files = ['OS_M1_20130918hourly_CMSTV.nc']
cl.m1_parms = [ 'eastward_sea_water_velocity_HR', 'northward_sea_water_velocity_HR', 
                     'SEA_WATER_SALINITY_HR', 'SEA_WATER_TEMPERATURE_HR', 'SW_FLUX_HR', 'AIR_TEMPERATURE_HR', 
                     'EASTWARD_WIND_HR', 'NORTHWARD_WIND_HR', 'WIND_SPEED_HR'
                   ]
cl.m1_startDatetime = startDatetime
cl.m1_endDatetime = endDatetime

# SubSample data files from /mbari/BOG_Archive/ReportsForSTOQS/GOC12/ copied to local GOC12 dir
cl.subsample_csv_base = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'SIMZAug2013')
cl.subsample_csv_files = [
                            '2013_Aug_SIMZ_Niskin_microscopy_STOQS.csv',
                         ]


# Execute the load
cl.process_command_line()

if cl.args.test:
    ##cl.loadL_662(stride=1)
    cl.loadDorado(stride=2)
    cl.loadRCuctd(stride=10)
    cl.loadRCpctd(stride=1)
    cl.loadM1(stride=1)
    ##cl.loadSubSamples()

elif cl.args.optimal_stride:
    ##cl.loadL_662(stride=1)
    cl.loadDorado(stride=1)
    cl.loadRCuctd(stride=1)
    cl.loadRCpctd(stride=1)
    cl.loadM1(stride=1)
    ##cl.loadSubSamples()

else:
    cl.stride = cl.args.stride
    ##cl.loadL_662()
    cl.loadDorado()
    cl.loadRCuctd()
    cl.loadRCpctd()
    cl.loadM1()
    ##cl.loadSubSamples()

