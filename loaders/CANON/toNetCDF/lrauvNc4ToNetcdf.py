#!/usr/bin/env python
import matplotlib
import matplotlib.pyplot as plt
import sys
import os
import errno
# Add grandparent dir to pythonpath so that we can see the CANON and toNetCDF modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../") )
import pdb
import numpy as np
import pandas as pd
import time
import datetime as dt
from time import mktime
from CANON.toNetCDF import BaseWriter
from pupynere import netcdf_file
import pydap.client 
import DAPloaders
import logging
import socket

class InterpolatorWriter(BaseWriter):

 logger = []
 logger = logging.getLogger('lrauvNc4ToNetcdf')
 fh = logging.StreamHandler()
 f = logging.Formatter("%(levelname)s %(asctime)sZ %(filename)s %(funcName)s():%(lineno)d %(message)s")
 fh.setFormatter(f)
 logger.addHandler(fh)
 logger.setLevel(logging.DEBUG)

 def write_netcdf(self, out_file, inUrl):
    
        # Check parent directory and create if needed
        dirName = os.path.dirname(out_file)
        try:
               os.makedirs(dirName)
        except OSError, e:
               if e.errno != errno.EEXIST:
                      raise

        # Create the NetCDF file
        self.ncFile = netcdf_file(out_file, 'w')

        # If specified on command line override the default generic title with what is specified
        self.ncFile.title = 'LRAUV interpolated data'

        # Combine any summary text specified on command line with the generic summary stating the original source file
        self.ncFile.summary = 'Observational oceanographic data translated with modification from original data file %s' % inUrl

        # add in time dimensions first
        ts_key = []
        for key in self.all_sub_ts.keys():
            if key.find('time') != -1:
                ts = self.all_sub_ts[key]

                if not ts.empty:
                       v = self.initRecordVariable(key)
                       v[:] = self.all_sub_ts[key]
            else:
                ts_key.append(key)

        # add in other remaining time series
        for key in ts_key:
            ts = self.all_sub_ts[key]

            if not ts.empty:
                   v = self.initRecordVariable(key)
                   v[:] = self.all_sub_ts[key]

        self.add_global_metadata()

        self.ncFile.close()

        # End write_netcdf()


 def interpolate(self, data, times):
     x = np.asarray(times,dtype=np.float64)
     xp = np.asarray(data.index,dtype=np.float64)
     fp = np.asarray(data)
     ts = pd.Series(index=times)
     # interpolate to get data onto spacing of datetimes in times variable
     # this can be irregularly spaced
     ts[:] = np.interp(x,xp,fp)
     return ts
     # End interpolate

 def createSeriesPydap(self, name, tname):
     v = self.df[name]
     v_t = self.df[tname]
     data = np.asarray(v_t)
     data[data/1e10 < -1.] = 'NaN'
     data[data/1e10 > 1.] ='NaN'
     v_time_epoch = data
     v_time = pd.to_datetime(v_time_epoch[:],unit='s')
     v_time_series = pd.Series(v[:],index=v_time)
     return v_time_series
     # End createSeriesPydap

 def initRecordVariable(self, key, units=None):
     # Create record variable to store in nc file   
     v = self.all_sub_ts[key]

     if key.find('time') != -1:
        # convert time to epoch seconds
        esec_list = v.index.values.astype(float)/1E9
        # Trajectory dataset, time is the only netCDF dimension
        self.ncFile.createDimension(key, len(esec_list))
        rc = self.ncFile.createVariable(key, 'float64', (key,))
        rc.standard_name = key
        rc.units = 'seconds since 1970-01-01'
        # Used in global metadata
        if key == 'time':
            self.time = rc
        return rc

     elif key.find('latitude') != -1:
        # Record Variables - coordinates for trajectory - save in the instance and use for metadata generation
        c = self.all_coord[key]
        rc = self.ncFile.createVariable(key, 'float64', (c['time'],))
        rc.long_name = 'LATITUDE'
        rc.standard_name = key
        rc.units = 'degree_north'
        rc[:] = self.all_sub_ts[key]
        # Used in global metadata
        if key == 'latitude':
            self.latitude = rc
        return rc

     elif key.find('longitude') != -1:
        c = self.all_coord[key]
        rc = self.ncFile.createVariable(key, 'float64', (c['time'],))
        rc.long_name = 'LONGITUDE'
        rc.standard_name = 'longitude'
        rc.units = 'degree_east'
        rc[:] = self.all_sub_ts[key]
        # Used in global metadata
        if key == 'longitude':
            self.longitude = rc
        return rc

     elif key.find('depth') != -1:
        c = self.all_coord[key]
        rc = self.ncFile.createVariable(key, 'float64', (c['time'],))
        rc.long_name = 'DEPTH'
        rc.standard_name = key
        rc.units = 'm'
        rc[:] = self.all_sub_ts[key]
        # Used in global metadata
        if key == 'depth':
            self.depth = rc
        return rc

     else:
        a = self.all_attrib[key]
        c = self.all_coord[key]
        rc = self.ncFile.createVariable(key, 'float64', (c['time'],))
        if 'long_name' in a:
            rc.long_name = a['long_name']
        if 'standard_name' in a:
            rc.standard_name = a['standard_name']
            rc.coordinates = ' '.join(c.values())

        if units is None:
            rc.unit = a['units']
        else:
            rc.units = units

        return rc
     # End initRecordVariable

 def getValidTimeRange(self, ts):
     start = ts.index[0]
     end = ts.index[-1]

     if pd.isnull(start) or pd.isnull(end):
            self.logger.info('Invalid starting or ending time found. Searching for valid time range')
            selector = np.where(~pd.isnull(ts.index))

            if len(selector) > 2:
                   start = ts[selector[0]]
                   end = ts[selector[-1]]
            
            # If still can't find a valid time, then raise exception here
            if pd.isnull(start) or pd.isnull(end):
                   raise Exception('Cannot find a valid time range')
            return (start, end)

     return(start, end)
     # End getValidTimeRange


 def process(self, url, out_file, parm, interp_key):
     self.df = []
     self.all_sub_ts = {}
     self.all_coord = {}
     self.all_attrib = {}
     coord =  ['latitude','longitude','depth']
     all_ts = {}

     try:
            self.df = pydap.client.open_url(url)
     except socket.error,e:
            self.logger.error('Failed in attempt to open_url(%s)', url)
            raise e
    
     # Create pandas time series for each parameter and store attributes
     for key in parm:
        try:
            ts = self.createSeriesPydap(key, key + '_time')
            self.all_attrib[key] = self.df[key].attributes
            self.all_attrib[key + '_i'] = self.df[key].attributes
            self.all_coord[key] = {'time':'time','depth':'depth','latitude':'latitude','longitude':'longitude'}
        except KeyError, e:
            ts = pd.Series()
            self.logger.info('Key error on ' + key)
            raise e

        all_ts[key] = ts

     # Create another pandas time series for each coordinate and store coordinates
     for key in coord:
        try:
            ts = self.createSeriesPydap(key, key + '_time')
        except KeyError, e:
            ts = pd.Series()
            self.logger.info('Key error on ' + key)
            raise e

        all_ts[key] = ts

     # create independent lat/lon/depth profiles for each parameter
     for key in parm:
        # TODO: add try catch block on this
        # Get independent parameter to interpolate on
        t = pd.Series(index = all_ts[key].index)

        # Store the parameter as-is - this is the raw data
        self.all_sub_ts[key] = pd.Series(all_ts[key])
        self.all_coord[key] = { 'time': key+'_time', 'depth': key+' _depth', 'latitude': key+'_latitude', 'longitude':key+'_longitude'}

        # interpolate each coordinate to the time of the parameter
        # key looks like sea_water_temperature_depth, sea_water_temperature_lat, sea_water_temperature_lon, etc.
        for c in coord:

            # get coordinate
            ts = all_ts[c]

            # and interpolate using parameter time
            if not ts.empty:
                i = self.interpolate(ts, t.index)
                self.all_sub_ts[key + '_' + c] = i
                self.all_coord[key + '_' + c] = { 'time': key+'_time', 'depth': key+' _depth', 'latitude': key+'_latitude', 'longitude':key+'_longitude'}

        # add in time coordinate separately
        v_time = all_ts[key].index
        esec_list = v_time.values.astype(float)/1E9
        self.all_sub_ts[key + '_time'] = pd.Series(esec_list,index=v_time)

     # TODO: add try catch block on this
     # Get independent parameter to interpolate on
     t = pd.Series(index = all_ts[interp_key].index)

     # store time using interpolation parameter
     v_time = all_ts[interp_key].index
     esec_list = v_time.values.astype(float)/1E9
     self.all_sub_ts['time'] = pd.Series(esec_list,index=v_time)

     # interpolate all parameters and coordinates
     for key in parm:
        value = all_ts[key]
        if not value.empty :
           i = self.interpolate(value, t.index)
           self.all_sub_ts[key + '_i'] = i
        else:
           self.all_sub_ts[key + '_i'] = value

        self.all_coord[key + '_i'] = { 'time': 'time', 'depth': 'depth', 'latitude':'latitude', 'longitude':'longitude'}

     for key in coord:
        value = all_ts[key]
        self.all_sub_ts[key] = value
        if not value.empty :
           i = self.interpolate(value, t.index)
           self.all_sub_ts[key] = i
        else:
           self.all_sub_ts[key] = value

        self.all_coord[key] = { 'time': 'time', 'depth': 'depth', 'latitude':'latitude', 'longitude':'longitude'}


     self.logger.info("%s", self.all_sub_ts.keys())

     # Write data to the file
     self.write_netcdf(out_file, url)
     self.logger.info('Wrote ' + out_file)

     # End processSingleParm

 def processResample(self, url, out_file, parm, interpFreq, resampleFreq):
     esec_list = []
     self.df = []
     self.all_sub_ts = {}
     self.parm =  ['latitude','longitude','depth'] + parm
     all_ts = {}
     start_times = []
     end_times = []

     try:
            self.df = pydap.client.open_url(url)
     except socket.error,e:
            self.logger.error('Failed in attempt to open_url(%s)', url)
            raise e
     except ValueError,e: 
            self.logger.error('Value error when opening open_url(%s)', url)
            raise e 
    
    # Create pandas time series and get sampling metric for each
     for key, value in parm.items():
            try:
                   p_ts = self.createSeriesPydap(key)
            except KeyError, e:
                   p_ts = pd.Series()
                   self.logger.info('Key error on ' + key)
                   raise e

            all_ts[key] = p_ts
            try:
                   (start,end) = self.getValidTimeRange(p_ts)   
                   start_times.append(start)
                   end_times.append(end)
            except:
                   self.logger.info('Start/end ' + parm + ' time range invalid')   

     # the full range should span all the time series data to store
     start_time = min(start_times)
     end_time = max(end_times)
     full_range = pd.date_range(start_time,end_time,freq=interpFreq)
     t = pd.Series(index = full_range)
     ts = t.index.values

     # convert time to epoch seconds
     esec_list = t.resample(resampleFreq).index.values.astype(float)/1E9

     for key, value in all_ts.items():
            if not value.empty :

                   # swap byte order and create a new series
                   values = value
                   newvalues = values.byteswap().newbyteorder()
                   pr = pd.Series(newvalues, index=value.index)

                   # reindex to the full range that covers all data
                   # forward fill
                   pr.reindex(index = full_range, method='ffill')

                   # interpolate onto regular time scale
                   i = self.interpolate(pr, ts)
                   try:                     
                       isub = i.resample(resampleFreq)[:]

                       # plotting for debugging
                       '''fig, axes = plt.subplots(4)
                       plt.legend(loc='best')
                       axes[0].set_title('raw ' + self.parm[j] + ' data') 
                       p.plot(ax=axes[0],color='r')
                       axes[1].set_title('reindexed') 
                       pr.plot(ax=axes[1],color='g')
                       axes[2].set_title('interpolated') 
                       i.plot(ax=axes[2],color='b')
                       axes[3].set_title('resampled') 
                       isub.plot(ax=axes[3],color='y')
                       plt.show()'''
                   except IndexError as e:
                       self.logger.error(e)
                       raise e
                   self.all_sub_ts[key] = isub
            else:
                   self.all_sub_ts[key] = pd.Series()

     # Write data to the file
     self.write_netcdf(out_file, url)
     self.logger.info('Wrote ' + out_file)
            
     # End process

if __name__ == '__main__':

    pw = InterpolatorWriter()
    pw.process_command_line()
    url = 'http://elvis.shore.mbari.org/thredds/dodsC/LRAUV/daphne/realtime/hotspotlogs/20140412T004330/hotspot-Normal_201404120043_201404120147.nc4'
    #untested url = 'http://dods.mbari.org/opendap/hyrax/data/lrauv/daphne/realtime/hotspotlogs/20140313T233828/hotspot-Normal_201403140010_201403140044.nc4'
    outDir = '/tmp/'

    # Formulate new filename from the url. Should be the same name as the .nc4 specified in the url
    # with _i.nc appended to indicate it has interpolated data and is now in .nc format
    f = url.rsplit('/',1)[1]
    out_file = outDir + '.'.join(f.split('.')[:-1]) + '_i.nc'
    pw.process(url,out_file)

    print 'Done.'
