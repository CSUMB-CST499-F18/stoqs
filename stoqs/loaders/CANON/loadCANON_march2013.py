#!/usr/bin/env python
__author__    = 'Mike McCann'
__copyright__ = '2013'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'

__doc__ = '''

Master loader for all March 2013 CANON-ECOHAB activities.  

Mike McCann
MBARI 13 March 2013

@var __date__: Date of last svn commit
@undocumented: __doc__ parser
@status: production
@license: GPL
'''

import os
import sys
import datetime

parentDir = os.path.join(os.path.dirname(__file__), "../")
sys.path.insert(0, parentDir)  # So that CANON is found

from CANON import CANONLoader
import timing

cl = CANONLoader('stoqs_march2013', 'CANON-ECOHAB - March 2013',
                    description = 'Spring 2013 ECOHAB in San Pedro Bay',
                    x3dTerrains = { 'https://stoqs.mbari.org/x3d/SanPedroBasin50/SanPedroBasin50_10x-pop.x3d': {
                                        'position': '-2523652.5 -4726093.2 3499413.2',
                                        'orientation': '0.96902 -0.20915 -0.13134 1.74597',
                                        'centerOfRotation': '-2505293.6 -4686937.5 3513055.2',
                                        'VerticalExaggeration': '10',
                                        }
                                  },
                    grdTerrain = os.path.join(parentDir, 'SanPedroBasin50.grd')
                )

# Aboard the Carson use zuma
##cl.tdsBase = 'http://zuma.rc.mbari.org/thredds/'       
cl.tdsBase = 'http://odss.mbari.org/thredds/'       # Use this on shore
cl.dodsBase = cl.tdsBase + 'dodsC/'       

# 2-second decimated dorado data
cl.dorado_base = 'http://dods.mbari.org/opendap/data/auvctd/surveys/2013/netcdf/'
cl.dorado_files = [ 
                    'Dorado389_2013_074_02_074_02_decim.nc',
                    'Dorado389_2013_075_05_075_06_decim.nc',
                    'Dorado389_2013_076_01_076_02_decim.nc',
                    'Dorado389_2013_079_04_079_04_decim.nc',
                    'Dorado389_2013_080_02_080_02_decim.nc',
                    'Dorado389_2013_081_05_081_05_decim.nc',
                    'Dorado389_2013_081_06_081_06_decim.nc',
                  ]
cl.dorado_parms = [ 'temperature', 'oxygen', 'nitrate', 'bbp420', 'bbp700', 
                    'fl700_uncorr', 'salinity', 'biolume',
                    'sepCountList', 'mepCountList']

# Realtime telemetered (_r_) daphne data - insert '_r_' to not load the files
##cl.daphne_base = 'http://aosn.mbari.org/lrauvtds/dodsC/lrauv/daphne/2012/'
daphne_r_base = cl.dodsBase + 'CANON_march2013/lrauv/daphne/realtime/sbdlogs/2013/201303/'
daphne_r_files = [ 
                    'shore_201303132226_201303140449.nc',
                    'shore_201303140708_201303140729.nc',
                    'shore_201303140729_201303141609.nc',
                    'shore_201303141631_201303151448.nc',
                    'shore_201303141631_201303181540.nc',
                  ]
cl.daphne_r_parms = [ 'sea_water_temperature', 'mass_concentration_of_chlorophyll_in_sea_water']

# Postrecovery full-resolution (_d_) daphne data - insert '_d_' for delayed-mode to not load the data
daphne_d_base = 'http://dods.mbari.org/opendap/hyrax/data/lrauv/daphne/missionlogs/2013/'
daphne_d_files = [ 
                    '20130313_20130318/20130313T195025/201303131950_201303132226.nc',
                    '20130313_20130318/20130313T222616/201303132226_201303140321.nc',
                    '20130313_20130318/20130313T222616/201303132226_201303140705.nc',
                    '20130313_20130318/20130314T070622/201303140706_201303140729.nc',
                    '20130313_20130318/20130314T072813/201303140728_201303140846.nc',
                    '20130313_20130318/20130314T072813/201303140728_201303141601.nc',
                    '20130313_20130318/20130314T072813/201303141601_201303141629.nc',
                    '20130313_20130318/20130314T162843/201303141628_201303141901.nc',
                    '20130313_20130318/20130314T162843/201303141628_201303141924.nc',
                    '20130313_20130318/20130314T162843/201303141901_201303150303.nc',
                    '20130313_20130318/20130314T162843/201303150303_201303151019.nc',
                    '20130313_20130318/20130314T162843/201303151019_201303151821.nc',
                    '20130313_20130318/20130314T162843/201303151821_201303151901.nc',
                    '20130313_20130318/20130314T162843/201303151901_201303160253.nc',
                    '20130313_20130318/20130314T162843/201303160253_201303161024.nc',
                    '20130313_20130318/20130314T162843/201303161024_201303161826.nc',
                    '20130313_20130318/20130314T162843/201303161826_201303161900.nc',
                    '20130313_20130318/20130314T162843/201303161900_201303162301.nc',
                    '20130313_20130318/20130314T162843/201303162301_201303170637.nc',
                    '20130313_20130318/20130314T162843/201303170637_201303171444.nc',
                    '20130313_20130318/20130314T162843/201303171444_201303171701.nc',
                    '20130313_20130318/20130314T162843/201303171701_201303180033.nc',
                    '20130313_20130318/20130314T162843/201303180033_201303180835.nc',
                    '20130313_20130318/20130314T162843/201303180835_201303180904.nc',
                    '20130313_20130318/20130314T162843/201303180904_201303181637.nc',
                    '20130313_20130318/20130314T162843/201303181637_201303181649.nc',
                    '20130313_20130318/20130318T165540/201303181655_201303182034.nc',
                    '20130313_20130318/20130318T165540/201303181655_201303182153.nc',
                    '20130319_20130325/20130319T213509/201303192135_201303200025.nc',
                    '20130319_20130325/20130320T002513/201303200025_201303200103.nc',
                    '20130319_20130325/20130320T002513/201303200025_201303200117.nc',
                    '20130319_20130325/20130320T002513/201303200103_201303201612.nc',
                    '20130319_20130325/20130320T002513/201303201612_201303201612.nc',
                    '20130319_20130325/20130320T002513/201303201613_201303201903.nc',
                    '20130319_20130325/20130320T002513/201303201903_201303210202.nc',
                    '20130319_20130325/20130320T002513/201303210202_201303211003.nc',
                    '20130319_20130325/20130320T002513/201303211003_201303211011.nc',
                    '20130319_20130325/20130321T100747/201303211008_201303211210.nc',
                    '20130319_20130325/20130321T100747/201303211008_201303211557.nc',
                    '20130319_20130325/20130321T155349/201303211554_201303211718.nc',
                    '20130319_20130325/20130321T155349/201303211554_201303211804.nc',
                    '20130319_20130325/20130321T155349/201303211804_201303220301.nc',
                    '20130319_20130325/20130321T155349/201303220301_201303221106.nc',
                    '20130319_20130325/20130321T155349/201303221106_201303221201.nc',
                    '20130319_20130325/20130321T155349/201303221201_201303222301.nc',
                    '20130319_20130325/20130321T155349/201303222301_201303222313.nc',
                    '20130319_20130325/20130322T231504/201303222315_201303222324.nc',
                    '20130319_20130325/20130322T232523/201303222325_201303230002.nc',
                    '20130319_20130325/20130322T232523/201303222325_201303230018.nc',
                    '20130319_20130325/20130322T232523/201303230002_201303230824.nc',
                    '20130319_20130325/20130322T232523/201303230824_201303231619.nc',
                    '20130319_20130325/20130322T232523/201303231619_201303231702.nc',
                    '20130319_20130325/20130322T232523/201303231702_201303240113.nc',
                    '20130319_20130325/20130322T232523/201303240113_201303240206.nc',
                    '20130319_20130325/20130322T232523/201303240206_201303240916.nc',
                    '20130319_20130325/20130322T232523/201303240916_201303241000.nc',
                    '20130319_20130325/20130322T232523/201303241000_201303241723.nc',
                    '20130319_20130325/20130322T232523/201303241725_201303242002.nc',
                    '20130319_20130325/20130322T232523/201303242002_201303250425.nc',
                    '20130319_20130325/20130322T232523/201303250425_201303250518.nc',
                    '20130319_20130325/20130322T232523/201303250518_201303250848.nc',
                    '20130319_20130325/20130325T084507/201303250845_201303251544.nc',
                  ]
daphne_d_parms = [ 'sea_water_temperature', 'sea_water_salinity', 'sea_water_density', 'volume_scattering_470_nm', 
                    'volume_scattering_650_nm', 'mass_concentration_of_oxygen_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'mass_concentration_of_chlorophyll_in_sea_water']

# Binned Daphne data
daphne_b_base = 'http://odss.mbari.org/thredds/dodsC/CANON_march2013/lrauv/daphne/'
daphne_b_files = ['Daphne_ECOHAB_March2013.nc']
daphne_b_parms = ['temperature', 'salinity', 'chlorophyll', 'bb470', 'bb650']

cl.daphne_base = daphne_b_base
cl.daphne_files = daphne_b_files
cl.daphne_parms = daphne_b_parms


# Realtime telemetered (_r_) tethys data - insert '_r_' to not load the files
tethys_r_base = cl.dodsBase + 'CANON_march2013/lrauv/tethys/realtime/sbdlogs/2013/201303/'
tethys_r_files = [ 
                    'shore_201303140812_201303141247.nc',
                    'shore_201303141252_201303141329.nc',
                    'shore_201303141331_201303150644.nc',
                    'shore_201303150645_201303151308.nc',
                    'shore_201303151312_201303151339.nc',
                    'shore_201303151333_201303151334.nc',
                    'shore_201303151337_201303151503.nc',
                    'shore_201303151504_201303151706.nc',
                    'shore_201303151714_201303151730.nc',
                    'shore_201303151728_201303151747.nc',
                    'shore_201303151748_201303151947.nc',
                    'shore_201303151950_201303152001.nc',
                    'shore_201303152003_201303152011.nc',
                    'shore_201303152013_201303152026.nc',
                    'shore_201303152027_201303160953.nc',
                    'shore_201303160958_201303161025.nc',
                    'shore_201303161027_201303161039.nc',
                    'shore_201303161041_201303170254.nc',
                    'shore_201303170334_201303170607.nc',
                    'shore_201303170616_201303170638.nc',
                    'shore_201303170641_201303170646.nc',
                    'shore_201303170647_201303171828.nc',
                    'shore_201303171835_201303171849.nc',
                    'shore_201303171851_201303171856.nc',
                    'shore_201303171857_201303172034.nc',
                    'shore_201303172042_201303172051.nc',
                    'shore_201303172055_201303172058.nc',
                    'shore_201303172059_201303180702.nc',
                    'shore_201303180717_201303180736.nc',
                    'shore_201303180733_201303180742.nc',
                    'shore_201303180743_201303181632.nc',       # Incomplete list of shore files
                                                                # Put effort into loading full-resolution data
                  ]
tethys_r_parms = [ 'sea_water_temperature', 'mass_concentration_of_chlorophyll_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'platform_x_velocity_current', 'platform_y_velocity_current', 'platform_z_velocity_current']

# Postrecovery full-resolution tethys data - insert '_d_' for delayed-mode to not load the data
tethys_d_base = 'http://dods.mbari.org/opendap/hyrax/data/lrauv/tethys/missionlogs/2013/'
tethys_d_files = [ 
                    '20130313_20130320/20130313T203723/201303132037_201303132240.nc',
                    '20130313_20130320/20130313T224020/201303132240_201303140239.nc',
                    '20130313_20130320/20130314T023827/201303140238_201303140547.nc',
                    '20130313_20130320/20130314T023827/201303140238_201303140715.nc',
                    '20130313_20130320/20130314T071458/201303140715_201303140731.nc',
                    '20130313_20130320/20130314T073047/201303140731_201303140803.nc',
                    '20130313_20130320/20130314T080454/201303140805_201303140811.nc',
                    '20130313_20130320/20130314T081138/201303140811_201303141248.nc',
                    '20130313_20130320/20130314T125102/201303141251_201303141329.nc',
                    '20130313_20130320/20130314T133105/201303141331_201303141424.nc',
                    '20130313_20130320/20130314T133105/201303141331_201303141602.nc',
                    '20130313_20130320/20130314T133105/201303141602_201303142309.nc',
                    '20130313_20130320/20130314T133105/201303142309_201303150644.nc',
                    '20130313_20130320/20130315T064246/201303150643_201303150802.nc',
                    '20130313_20130320/20130315T064246/201303150643_201303150909.nc',
                    '20130313_20130320/20130315T064246/201303150802_201303151102.nc',
                    '20130313_20130320/20130315T064246/201303151102_201303151308.nc',
                    '20130313_20130320/20130315T131039/201303151310_201303151331.nc',
                    '20130313_20130320/20130315T133305/201303151333_201303151335.nc',
                    '20130313_20130320/20130315T133635/201303151336_201303151503.nc',
                    '20130313_20130320/20130315T150400/201303151504_201303151601.nc',
                    '20130313_20130320/20130315T150400/201303151504_201303151706.nc',
                    '20130313_20130320/20130315T150400/201303151601_201303151706.nc',
                    '20130313_20130320/20130315T170914/201303151709_201303151725.nc',
                    '20130313_20130320/20130315T172729/201303151727_201303151747.nc',
                    '20130313_20130320/20130315T174744/201303151747_201303151947.nc',
                    '20130313_20130320/20130315T195016/201303151950_201303152002.nc',
                    '20130313_20130320/20130315T200217/201303152002_201303152011.nc',
                    '20130313_20130320/20130315T201305/201303152013_201303152027.nc',
                    '20130313_20130320/20130315T202717/201303152027_201303152201.nc',
                    '20130313_20130320/20130315T202717/201303152027_201303160254.nc',
                    '20130313_20130320/20130315T202717/201303152201_201303160004.nc',
                    '20130313_20130320/20130315T202717/201303160004_201303160651.nc',
                    '20130313_20130320/20130315T202717/201303160651_201303160953.nc',
                    '20130313_20130320/20130316T095712/201303160957_201303161025.nc',
                    '20130313_20130320/20130316T102632/201303161026_201303161040.nc',
                    '20130313_20130320/20130316T104017/201303161040_201303161302.nc',
                    '20130313_20130320/20130316T104017/201303161040_201303161529.nc',
                    '20130313_20130320/20130316T104017/201303161302_201303162011.nc',
                    '20130313_20130320/20130316T104017/201303162011_201303170333.nc',
                    '20130313_20130320/20130317T033239/201303170332_201303170602.nc',
                    '20130313_20130320/20130317T033239/201303170332_201303170608.nc',
                    '20130313_20130320/20130317T033239/201303170602_201303170608.nc',
                    '20130313_20130320/20130317T061040/201303170610_201303170639.nc',
                    '20130313_20130320/20130317T064112/201303170641_201303170646.nc',
                    '20130313_20130320/20130317T064639/201303170646_201303170802.nc',
                    '20130313_20130320/20130317T064639/201303170646_201303170944.nc',
                    '20130313_20130320/20130317T064639/201303170802_201303171511.nc',
                    '20130313_20130320/20130317T064639/201303171511_201303171828.nc',
                    '20130313_20130320/20130317T183135/201303171831_201303171849.nc',
                    '20130313_20130320/20130317T185106/201303171851_201303171856.nc',
                    '20130313_20130320/20130317T185723/201303171857_201303171956.nc',
                    '20130313_20130320/20130317T185723/201303171857_201303172006.nc',
                    '20130313_20130320/20130317T185723/201303172006_201303172034.nc',
                    '20130313_20130320/20130317T203717/201303172037_201303172051.nc',
                    '20130313_20130320/20130317T205336/201303172053_201303172058.nc',
                    '20130313_20130320/20130317T205906/201303172059_201303172202.nc',
                    '20130313_20130320/20130317T205906/201303172059_201303172244.nc',
                    '20130313_20130320/20130317T205906/201303172202_201303180512.nc',
                    '20130313_20130320/20130317T205906/201303180512_201303180702.nc',
                    '20130313_20130320/20130318T070527/201303180705_201303180731.nc',
                    '20130313_20130320/20130318T073303/201303180733_201303180742.nc',
                    '20130313_20130320/20130318T074256/201303180743_201303180902.nc',
                    '20130313_20130320/20130318T074256/201303180743_201303180903.nc',
                    '20130313_20130320/20130318T074256/201303180903_201303181606.nc',
                    '20130313_20130320/20130318T074256/201303181606_201303182352.nc',
                    '20130313_20130320/20130318T074256/201303182352_201303190101.nc',
                    '20130313_20130320/20130318T074256/201303190101_201303190235.nc',
                    '20130313_20130320/20130319T023834/201303190238_201303190257.nc',
                    '20130313_20130320/20130319T025944/201303190300_201303190302.nc',
                    '20130313_20130320/20130319T030324/201303190303_201303190703.nc',
                    '20130313_20130320/20130319T030324/201303190303_201303190721.nc',
                    '20130313_20130320/20130319T030324/201303190703_201303190817.nc',
                    '20130313_20130320/20130319T081955/201303190820_201303190845.nc',
                    '20130313_20130320/20130319T084718/201303190847_201303190849.nc',
                    '20130313_20130320/20130319T085014/201303190850_201303191101.nc',
                    '20130313_20130320/20130319T085014/201303190850_201303192307.nc',
                    '20130313_20130320/20130319T085014/201303191101_201303191804.nc',
                    '20130313_20130320/20130319T085014/201303191804_201303192307.nc',
                    '20130313_20130320/20130319T231047/201303192311_201303192333.nc',
                    '20130313_20130320/20130319T233504/201303192335_201303200004.nc',
                    '20130313_20130320/20130320T000452/201303200005_201303200056.nc',
                    '20130313_20130320/20130320T005923/201303200059_201303200132.nc',
                    '20130313_20130320/20130320T013358/201303200134_201303200136.nc',
                    '20130313_20130320/20130320T014500/201303200145_201303200203.nc',
                    '20130313_20130320/20130320T014500/201303200145_201303200228.nc',
                    '20130313_20130320/20130320T014500/201303200203_201303200916.nc',
                    '20130313_20130320/20130320T091648/201303200918_201303201726.nc',
                    '20130313_20130320/20130320T172551/201303201726_201303201854.nc',
                    '20130321_20130325/20130321T220027/201303212200_201303220305.nc',
                    '20130321_20130325/20130321T220027/201303220305_201303220547.nc',
                    '20130321_20130325/20130322T054706/201303220547_201303220804.nc',
                    '20130321_20130325/20130322T054706/201303220804_201303221510.nc',
                    '20130321_20130325/20130322T054706/201303221510_201303222301.nc',
                    '20130321_20130325/20130322T054706/201303222301_201303230404.nc',
                    '20130321_20130325/20130322T054706/201303230404_201303231114.nc',
                    '20130321_20130325/20130322T054706/201303231114_201303231852.nc',
                    '20130321_20130325/20130322T054706/201303231852_201303240302.nc',
                    '20130321_20130325/20130322T054706/201303240302_201303241003.nc',
                    '20130321_20130325/20130322T054706/201303241003_201303241732.nc',
                    '20130321_20130325/20130322T054706/201303241732_201303250203.nc',
                    '20130321_20130325/20130322T054706/201303250203_201303250902.nc',
                    '20130321_20130325/20130322T054706/201303250902_201303251600.nc',
                    '20130321_20130325/20130325T155211/201303251552_201303252211.nc',
                  ]

tethys_d_parms = [ 'sea_water_temperature', 'sea_water_salinity', 'sea_water_density', 'volume_scattering_470_nm', 
                    'volume_scattering_650_nm', 'mass_concentration_of_oxygen_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'mass_concentration_of_chlorophyll_in_sea_water']

# Binned Tethys data
tethys_b_base = 'http://odss.mbari.org/thredds/dodsC/CANON_march2013/lrauv/tethys/'
tethys_b_files = ['Tethys_ECOHAB_March2013.nc']
tethys_b_parms = ['temperature', 'salinity', 'chlorophyll', 'bb470', 'bb650']

cl.tethys_base = tethys_b_base
cl.tethys_files = tethys_b_files
cl.tethys_parms = tethys_b_parms

# Webb gliders
cl.hehape_base = cl.dodsBase + 'CANON_march2013/usc_glider/HeHaPe/processed/'
cl.hehape_files = [
                        'OS_Glider_HeHaPe_20130305_TS.nc',
                        'OS_Glider_HeHaPe_20130310_TS.nc',
                   ]
cl.hehape_parms = [ 'TEMP', 'PSAL', 'BB532', 'CDOM', 'CHLA', 'DENS' ]

cl.rusalka_base = cl.dodsBase + 'CANON_march2013/usc_glider/Rusalka/processed/'
cl.rusalka_files = [
                        'OS_Glider_Rusalka_20130301_TS.nc',
                   ]
cl.rusalka_parms = [ 'TEMP', 'PSAL', 'BB532', 'CDOM', 'CHLA', 'DENS' ]

# Spray glider - for just the duration of the campaign
cl.l_662_base = 'http://legacy.cencoos.org/thredds/dodsC/gliders/Line66/'
cl.l_662_files = ['OS_Glider_L_662_20120816_TS.nc']
cl.l_662_parms = ['TEMP', 'PSAL', 'FLU2']
cl.l_662_startDatetime = datetime.datetime(2012, 9, 10)
cl.l_662_endDatetime = datetime.datetime(2012, 9, 20)


# MBARI ESPs Mack and Bruce
cl.espmack_base = cl.dodsBase + 'CANON_march2013/esp/instances/Mack/data/processed/'
cl.espmack_files = [ 
                        'ctd.nc',
                      ]
cl.espmack_parms = [ 'TEMP', 'PSAL', 'chl', 'chlini', 'no3' ]

# Rachel Carson Underway CTD
cl.rcuctd_base = cl.dodsBase + 'CANON_march2013/carson/uctd/'
cl.rcuctd_files = [ 
                        '07413plm01.nc', '07513plm02.nc', '07613plm03.nc', '07913plm04.nc',
                        '08013plm05.nc', '08113plm06.nc',
                      ]
cl.rcuctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'wetstar' ]

# Rachel Carson Profile CTD
cl.pctdDir = 'CANON_march2013/carson/pctd/'
cl.rcpctd_base = cl.dodsBase + cl.pctdDir
cl.rcpctd_files = [ 
                    '07413c01.nc', '07413c02.nc', '07413c03.nc', '07413c04.nc', '07413c05.nc', '07413c06.nc', '07413c07.nc',
                    '07413c08.nc', '07413c09.nc', '07413c10.nc', '07413c11.nc', '07513c12.nc', '07513c13.nc', '07513c14.nc',
                    '07513c15.nc', '07513c16.nc', '07513c17.nc', '07513c18.nc', '07513c19.nc', '07613c20.nc', '07613c21.nc',
                    '07613c22.nc', '07613c23.nc', '07613c24.nc', '07613c25.nc', '07613c26.nc', '07913c27.nc', '07913c28.nc',
                    '07913c29.nc', '07913c30.nc', '07913c31.nc', '08013c32.nc', '08013c33.nc', '08013c34.nc', '08013c35.nc',
                    '08013c36.nc', '08113c37.nc', '08113c38.nc', '08113c39.nc', '08113c40.nc', '08113c41.nc', '08113c42.nc',
                    '08113c43.nc',
                      ]
cl.rcpctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'ecofl', 'oxygen' ]

# Spray glider - for just the duration of the campaign
##cl.l_662_base = 'http://legacy.cencoos.org/thredds/dodsC/gliders/Line66/'
##cl.l_662_files = ['OS_Glider_L_662_20120816_TS.nc']
##cl.l_662_parms = ['TEMP', 'PSAL', 'FLU2']
##cl.l_662_startDatetime = datetime.datetime(2012, 9, 1)
##cl.l_662_endDatetime = datetime.datetime(2012, 9, 21)


# Execute the load
cl.process_command_line()

if cl.args.test:
    cl.loadDorado(stride=10)
    cl.loadDaphne(stride=10)
    cl.loadTethys(stride=10)
    ##cl.loadESPmack()
    ##cl.loadESPbruce()
    cl.loadRCuctd(stride=2)
    cl.loadRCpctd(stride=1)
    ##cl.loadHeHaPe()
    ##cl.loadRusalka()
    ##cl.loadYellowfin()

elif cl.args.optimal_stride:
    cl.loadDorado(stride=2)
    cl.loadDaphne(stride=2)
    cl.loadTethys(stride=2)
    ##cl.loadESPmack()
    ##cl.loadESPbruce()
    cl.loadRCuctd(stride=1)
    cl.loadRCpctd(stride=1)
    ##cl.loadHeHaPe(stride=10)      # As of 3/18/2013 - Bad Lat & Lon
    ##cl.loadRusalka(stride=10)     # As of 3/18/2013 - no good data in file http://zuma.rc.mbari.org/thredds/dodsC/CANON_march2013/usc_glider/Rusalka/processed/OS_Glider_Rusalka_20130301_TS.nc.html
    ##cl.loadYellowfin()

else:
    cl.stride = cl.args.stride
    cl.loadDorado()
    cl.loadDaphne()
    cl.loadTethys()
    ##cl.loadESPmack()
    ##cl.loadESPbruce()
    cl.loadRCuctd()
    cl.loadRCpctd()
    ##cl.loadHeHaPe()
    ##cl.loadRusalka()
    ##cl.loadYellowfin()

# Add any X3D Terrain information specified in the constructor to the database
cl.addTerrainResources()
print("All done.")
