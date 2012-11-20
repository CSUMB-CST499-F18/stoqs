__author__    = 'Mike McCann'
__copyright__ = '2012'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'

__doc__ = '''

STOQS Query manager for building ajax responces to selections made for QueryUI

@undocumented: __doc__ parser
@status: production
@license: GPL
'''

from django.conf import settings
from django.db import connections
from django.db.models import Q, Max, Min, Sum
from django.contrib.gis.geos import fromstr
from django.db.models import Avg
from django.http import HttpResponse
from stoqs import models
from utils import round_to_n
from coards import to_udunits
from datetime import datetime
import logging
import pprint
import calendar
import re
import locale
import time
import os
import tempfile

logger = logging.getLogger(__name__)

class STOQSQManager(object):
    '''
    This class is designed to handle building and managing queries against the STOQS database.
    Chander Ganesan <chander@otg-nc.com>
    '''
    def __init__(self, request, response, dbname):
        '''
        This object should be created by passing in an HTTPRequest Object, an HTTPResponse object
        and the name of the database to be used.
        '''
        self.request = request
        self.dbname = dbname
        self.response = response
        
    def buildQuerySet(self, *args, **kwargs):
        '''
        Build the query set based on any selections form the UI. For the first time through  kwargs will be empty 
        and self.qs will be built of a join of activities, parameters, and platforms with no constraints.

        Right now supported keyword arguments are the following:
            parametername - a list of parameter names to include
            parameterstandardname - a list of parameter styandard_names to include
            platforms - a list of platform names to include
            time - a two-tuple consisting of a start and end time, if either is None, the assumption is no start (or end) time
            depth - a two-tuple consisting of a range (start/end depth, if either is None, the assumption is no start (or end) depth

        These are all called internally - so we'll assume that all the validation has been done in advance,
        and the calls to this method meet the requirements stated above.
        '''
        if 'qs' in args:
            logger.debug('Using query string passed in to make a non-activity based query')
            qs = args['qs']
        else:
            logger.debug('Making default activity based query')
            if (not kwargs):
                qs = models.Activity.objects.using(self.dbname).select_related(depth=3).filter( activityparameter__parameter__pk__isnull=False,
                                                                                                activityparameter__activity__pk__isnull=False,
                                                                                                simpledepthtime__pk__isnull=False,
                                                                                                platform__pk__isnull=False)
            else:
                qs = models.Activity.objects.using(self.dbname).select_related(depth=3).all()   # To receive filters constructed below from kwargs
    
        self.kwargs = kwargs
        for k, v in kwargs.iteritems():
            '''
            Check to see if there is a "builder" for a Q object using the given parameters.
            '''
            if not v:
                continue
            if hasattr(self, '_%sQ' % (k,)):
                # Call the method if it exists, and add the resulting Q object to the filtered
                # queryset.
                q = getattr(self,'_%sQ' % (k,))(v)
                logger.debug('k = %s, v = %s, q = %s', k, v, q)
                qs = qs.filter(q)
        self.qs = qs
        
    def generateOptions(self):
        '''
        Generate a dictionary of all the selectable parameters by executing each of the functions
        to generate those parameters.  In this case, we'll simply do it by defining the dictionary and it's associated
        function, then iterate over that dictionary calling the function(s) to get the value to be returned.
        Note that in the case of parameters and platforms the result is a list of 2-tuples, with the UUID
        and NAME of the associated element.  For time and depth, the result is a single 2-tuple with the
        min and max value (respectively.)  
        These objects are "simple" dictionaries using only Python's built-in types - so conversion to a
        corresponding JSON object should be trivial.
        '''
        options_functions={'parameters': self.getParameters,
                           'parameterminmax': self.getParameterMinMax,
                           'platforms': self.getPlatforms,
                           'time': self.getTime,
                           'depth': self.getDepth,
                           'simpledepthtime': self.getSimpleDepthTime,
                           'sampledepthtime': self.getSampleDepthTime,
                           'count': self.getCount,
                           'ap_count': self.getAPCount,
                           'sql': self.getMeasuredParametersPostgreSQL,
                           'activitymaptrackextent': self.getActivityMaptrackExtent,
                           'activityparameterhistograms': self.getActivityParameterHistograms,
                           'parameterplatformdatavaluepng': self.getParameterPlatformDatavaluePNG,
                           ##'activityparamhistrequestpngs': self.getActivityParamHistRequestPNGs,
                           }
        
        results = {}
        for k,v in options_functions.iteritems():
            results[k] = v()
        
        ##logger.info('qs.query = %s', pprint.pformat(str(self.qs.query)))
        ##logger.info('results = %s', pprint.pformat(results))
        return results
    
    #
    # Methods that generate summary data, based on the current query criteria.
    #

    def getGet_Actual_Count(self):
        '''
        return state of Get Actual Count checkbox from query UI
        '''
        get_actual_count_state = False
        if self.kwargs.has_key('get_actual_count'):
            if self.kwargs['get_actual_count']:
                get_actual_count_state = True
        logger.debug('get_actual_count = %s', get_actual_count_state)

        return get_actual_count_state
        
    def getShow_Sigmat_Parameter_Values(self):
        '''
        return state of showsigmatparametervalues checkbox from query UI
        '''
        show_sigmat_parameter_values_state = False
        if self.kwargs.has_key('showsigmatparametervalues'):
            if self.kwargs['showsigmatparametervalues']:
                show_sigmat_parameter_values_state = True
        logger.debug('show_sigmat_parameter_values_state = %s', show_sigmat_parameter_values_state)

        return show_sigmat_parameter_values_state

    def getShow_StandardName_Parameter_Values(self):
        '''
        return state of showstandardnameparametervalues checkbox from query UI
        '''
        show_standardname_parameter_values_state = False
        if self.kwargs.has_key('showstandardnameparametervalues'):
            if self.kwargs['showstandardnameparametervalues']:
                show_standardname_parameter_values_state = True
        logger.debug('show_standardname_parameter_values_state = %s', show_standardname_parameter_values_state)

        return show_standardname_parameter_values_state

    def getShow_All_Parameter_Values(self):
        '''
        return state of showallparametervalues checkbox from query UI
        '''
        show_all_parameter_values_state = False
        if self.kwargs.has_key('showallparametervalues'):
            if self.kwargs['showallparametervalues']:
                show_all_parameter_values_state = True
        logger.debug('show_all_parameter_values_state = %s', show_all_parameter_values_state)

        return show_all_parameter_values_state

    def getDisplay_Parameter_Platform_Data(self):
        '''
        return state of Display Parameter-Platform data checkbox from quiry UI
        '''
        display_parameter_platform_data_state = False
        if self.kwargs.has_key('displayparameterplatformdata'):
            if self.kwargs['displayparameterplatformdata']:
                display_parameter_platform_data_state = True
        logger.debug('display_parameter_platform_data_state = %s', display_parameter_platform_data_state)

        return display_parameter_platform_data_state
        

    def getCount(self):
        '''
        Get the count of measured parameters giving the exising query
        '''

        locale.setlocale(locale.LC_ALL, 'en_US')
        qs_ap = self.getActivityParametersQS()                  # Approximate count from ActivityParameter
        if qs_ap:
            ap_count = qs_ap.count()
            logger.debug('ap_count = %d', ap_count)
            approximate_count = qs_ap.aggregate(Sum('number'))['number__sum']
            logger.debug('approximate_count = %d', approximate_count)
            if approximate_count == 0:
                logger.warn('actual_count == 0')
            if self.getGet_Actual_Count():
                logger.info('>>>> get_actual_count selected.  Switching to getting actual count.')
                qs_mp = self.getMeasuredParametersQS()          # Actual count from MeasuredParameter - needs to do seq scan on large table
                actual_count = qs_mp.count()
                logger.debug('actual_count = %d', actual_count)
                if actual_count == 0:
                    logger.warn('actual_count == 0')
                return locale.format("%d", actual_count, grouping=True)
            else:
                return locale.format("%d", approximate_count, grouping=True)
        else:
            return 0
      
    def getAPCount(self):
        '''
        Return count of ActivityParameters given the current constraints
        ''' 
        qs_ap = self.getActivityParametersQS()                  # Approximate count from ActivityParameter
        if qs_ap:
            return qs_ap.count()
        else:
            return 0
        
    def getActivityParametersQS(self):
        '''
        Return query set of ActivityParameters given the current constraints. 
        '''
        qparams = {}

        qs_ap = models.ActivityParameter.objects.using(self.dbname).all()
        if self.kwargs.has_key('parametername'):
            if self.kwargs['parametername']:
                qs_ap = qs_ap.filter(Q(parameter__name__in=self.kwargs['parametername']))
        if self.kwargs.has_key('parameterstandardname'):
            if self.kwargs['parameterstandardname']:
                qs_ap = qs_ap.filter(Q(parameter__standard_name__in=self.kwargs['parameterstandardname']))
        if self.kwargs.has_key('platforms'):
            if self.kwargs['platforms']:
                qs_ap = qs_ap.filter(Q(activity__platform__name__in=self.kwargs['platforms']))
        if self.kwargs.has_key('time'):
            if self.kwargs['time'][0] is not None:
                q1 = Q(activity__startdate__lte=self.kwargs['time'][0]) & Q(activity__enddate__gte=self.kwargs['time'][0])
            if self.kwargs['time'][1] is not None:
                q2 = Q(activity__startdate__lte=self.kwargs['time'][1]) & Q(activity__enddate__gte=self.kwargs['time'][1])
            if self.kwargs['time'][0] is not None and self.kwargs['time'][1] is not None:
                q3 = Q(activity__startdate__gte=self.kwargs['time'][0]) & Q(activity__startdate__lte=self.kwargs['time'][1]
                    ) & Q(activity__enddate__gte=self.kwargs['time'][0]) & Q(activity__enddate__lte=self.kwargs['time'][1])

                qs_ap = qs_ap.filter(q1 | q2 | q3)

                logger.debug('ORing Q objects %s, %s, %s', q1, q2, q3)

        if self.kwargs.has_key('depth'):
            if self.kwargs['depth'][0] is not None:
                q1 = Q(activity__mindepth__lte=self.kwargs['depth'][0]) & Q(activity__maxdepth__gte=self.kwargs['depth'][0])
            if self.kwargs['depth'][1] is not None:
                q2 = Q(activity__mindepth__lte=self.kwargs['depth'][1]) & Q(activity__maxdepth__gte=self.kwargs['depth'][1])
            if self.kwargs['depth'][0] is not None and self.kwargs['depth'][1] is not None:
                q3 = Q(activity__mindepth__gte=self.kwargs['depth'][0]) & Q(activity__mindepth__lte=self.kwargs['depth'][1]
                    ) & Q(activity__maxdepth__gte=self.kwargs['depth'][0]) & Q(activity__maxdepth__lte=self.kwargs['depth'][1])
                qs_ap = qs_ap.filter(q1 | q2 | q3)

        if qs_ap:
            logger.debug(pprint.pformat(str(qs_ap.query)))
        else:
            logger.debug("No queryset returned for ")
        return qs_ap

    def getActivityParameterHistogramsQS(self):
        '''
        Return query set of ActivityParameterHistograms given the current constraints. 
        If a parameter kwargs exists then constrain to platform(s) that have that parameter.
        '''
        qparams = {}

        logger.info(pprint.pformat(self.kwargs))
        qs_aph = models.ActivityParameterHistogram.objects.using(self.dbname).all()
        if self.kwargs.has_key('platforms'):
            if self.kwargs['platforms']:
                qs_aph = qs_aph.filter(Q(activityparameter__activity__platform__name__in=self.kwargs['platforms']))
        if self.kwargs.has_key('parameters'):
            if self.kwargs['parameters']:
                # Need to do some kind of sub-query here: get all the platforms that have these parameters then restrict to the returned platforms
                logger.debug('Finding out which platforms have parameter = %s', self.kwargs['parameters'])
                qs_plat = models.Platform.objects.using(self.dbname).all()
                qs_plat = qs_plat.filter(Q(activity__activityparameter__parameter__name__in=self.kwargs['parameters']))
                platHash = {}       # Use a hash to get a unique list of platform names with .keys()
                for plat in qs_plat:
                    platHash[plat] = 1
                qs_aph = qs_aph.filter(Q(activityparameter__activity__platform__name__in=platHash.keys()))
        if self.kwargs.has_key('time'):
            if self.kwargs['time'][0] is not None:
                q1 = Q(activityparameter__activity__startdate__lte=self.kwargs['time'][0]) & Q(activityparameter__activity__enddate__gte=self.kwargs['time'][0])
            if self.kwargs['time'][1] is not None:
                q2 = Q(activityparameter__activity__startdate__lte=self.kwargs['time'][1]) & Q(activityparameter__activity__enddate__gte=self.kwargs['time'][1])
            if self.kwargs['time'][0] is not None and self.kwargs['time'][1] is not None:
                q3 = Q(activityparameter__activity__startdate__gte=self.kwargs['time'][0]) & Q(activityparameter__activity__startdate__lte=self.kwargs['time'][1]
                    ) & Q(activityparameter__activity__enddate__gte=self.kwargs['time'][0]) & Q(activityparameter__activity__enddate__lte=self.kwargs['time'][1])

                qs_aph = qs_aph.filter(q1 | q2 | q3)

                logger.debug('ORing Q objects %s, %s, %s', q1, q2, q3)

        if self.kwargs.has_key('depth'):
            if self.kwargs['depth'][0] is not None:
                q1 = Q(activityparameter__activity__mindepth__lte=self.kwargs['depth'][0]) & Q(activityparameter__activity__maxdepth__gte=self.kwargs['depth'][0])
            if self.kwargs['depth'][1] is not None:
                q2 = Q(activityparameter__activity__mindepth__lte=self.kwargs['depth'][1]) & Q(activityparameter__activity__maxdepth__gte=self.kwargs['depth'][1])
            if self.kwargs['depth'][0] is not None and self.kwargs['depth'][1] is not None:
                q3 = Q(activityparameter__activity__mindepth__gte=self.kwargs['depth'][0]) & Q(activityparameter__activity__mindepth__lte=self.kwargs['depth'][1]
                    ) & Q(activityparameter__activity__maxdepth__gte=self.kwargs['depth'][0]) & Q(activityparameter__activity__maxdepth__lte=self.kwargs['depth'][1])
                qs_aph = qs_aph.filter(q1 | q2 | q3)

        if qs_aph:
            logger.debug(pprint.pformat(str(qs_aph.query)))
        else:
            logger.debug("No queryset returned for kwargs = %s", self.kwargs)
        return qs_aph

    def getMeasuredParametersQS(self):
        '''
        Return query set of MeasuremedParameters given the current constraints.  If no parameter is selected return None.
        '''
        qparams = {}

        logger.info(pprint.pformat(self.kwargs))
        if self.kwargs.has_key('parametername'):
            if self.kwargs['parametername']:
                qparams['parameter__name__in'] = self.kwargs['parametername']
        if self.kwargs.has_key('parameterstandardname'):
            if self.kwargs['parameterstandardname']:
                qparams['parameter__standard_name__in'] = self.kwargs['parameterstandardname']
        if self.kwargs.has_key('platforms'):
            if self.kwargs['platforms']:
                qparams['measurement__instantpoint__activity__platform__name__in'] = self.kwargs['platforms']
        if self.kwargs.has_key('time'):
            if self.kwargs['time'][0] is not None:
                qparams['measurement__instantpoint__timevalue__gte'] = self.kwargs['time'][0]
            if self.kwargs['time'][1] is not None:
                qparams['measurement__instantpoint__timevalue__lte'] = self.kwargs['time'][1]
        if self.kwargs.has_key('depth'):
            if self.kwargs['depth'][0] is not None:
                qparams['measurement__depth__gte'] = self.kwargs['depth'][0]
            if self.kwargs['depth'][1] is not None:
                qparams['measurement__depth__lte'] = self.kwargs['depth'][1]

        ##logger.debug(pprint.pformat(qparams))
        qs_mp = models.MeasuredParameter.objects.using(self.dbname).filter(**qparams)
        if qs_mp:
            logger.debug(pprint.pformat(str(qs_mp.query)))
        else:
            logger.debug("No queryset returned for qparams = %s", pprint.pformat(qparams))
        return qs_mp

    def getMeasuredParametersPostgreSQL(self):
        '''
        Return SQL string that can be executed agaisnt the postgres database
        '''
        sql = 'Check "Get actual count" checkbox to see the SQL for your data selection'
        qs_ap = self.getActivityParametersQS()
        if qs_ap:
            if self.getGet_Actual_Count():
                # Return query only if a platform and a parameter have been selected
                qs_mp = self.getMeasuredParametersQS()
                qs_mp = qs_mp.values(   'measurement__instantpoint__activity__platform__name', 'measurement__instantpoint__timevalue', 
                                        'measurement__geom', 'parameter__name', 'datavalue')
                if qs_mp:
                    sql = '\c %s\n' % settings.DATABASES[self.request.META['dbAlias']]['NAME']
                    sql +=  self.postgresifySQL(str(qs_mp.query)) + ';'
        return sql

    def getSampleQS(self):
        '''
        Return query set of Samples given the current constraints. 
        '''
        qparams = {}

        if self.kwargs.has_key('platforms'):
            if self.kwargs['platforms']:
                qparams['instantpoint__activity__platform__name__in'] = self.kwargs['platforms']
        if self.kwargs.has_key('time'):
            if self.kwargs['time'][0] is not None:
                qparams['instantpoint__timevalue__gte'] = self.kwargs['time'][0]
            if self.kwargs['time'][1] is not None:
                qparams['instantpoint__timevalue__lte'] = self.kwargs['time'][1]
        if self.kwargs.has_key('depth'):
            if self.kwargs['depth'][0] is not None:
                qparams['depth__gte'] = self.kwargs['depth'][0]
            if self.kwargs['depth'][1] is not None:
                qparams['depth__lte'] = self.kwargs['depth'][1]

        logger.debug(pprint.pformat(qparams))
        qs_sample = models.Sample.objects.using(self.dbname).filter(**qparams)
        if qs_sample:
            logger.debug(pprint.pformat(str(qs_sample.query)))
            self.qs_sample = qs_sample
        else:
            logger.debug("No queryset returned for qparams = %s", pprint.pformat(qparams))
        return qs_sample

    def getActivities(self):
        '''
        Get a list of the unique activities based on the current query criteria.  
        return the UUID's of those, since we need to return those to perform the query later.
        Lastly, we assume here that the uuid's and name's have a 1:1 relationship - this should be enforced
        somewhere in the database hopefully.  If not, we'll return the duplicate name/uuid pairs as well.
        '''
        qs = self.qs.values('uuid', 'name').distinct()
        results=[]
        for row in qs:
            name = row['name']
            uuid = row['uuid']
            if name is not None and uuid is not None:
                results.append((name,uuid,))
        return results

    def getParameters(self):
        '''
        Get a list of the unique parameters that are left based on the current query criteria.  Also
        return the UUID's of those, since we need to return those to perform the query later.
        Lastly, we assume here that the name is unique and is also used for the id - this is enforced on 
        data load.
        '''
        qs = self.qs.values('activityparameter__parameter__name','activityparameter__parameter__standard_name').distinct()

        results=[]
        for row in qs:
            name = row['activityparameter__parameter__name']
            standard_name = row['activityparameter__parameter__standard_name']
            if not standard_name:
                standard_name = ''
            if name is not None:
                results.append((name,standard_name,))
        return results

    def getParameterMinMax(self):
        '''
        If a single parameter has been selected return the average 2.5 and 97.5 percentiles of the
        data and call them min and max for purposes of plotting
        '''
        results = []
        if len(self.kwargs['parametername']) == 1:
            qs = self.getActivityParametersQS().aggregate(Avg('p025'), Avg('p975'))
            results = [self.kwargs['parametername'][0], round_to_n(qs['p025__avg'],3), round_to_n(qs['p975__avg'],3)]
        if len(self.kwargs['parameterstandardname']) == 1:
            qs = self.getActivityParametersQS().aggregate(Avg('p025'), Avg('p975'))
            results = [self.kwargs['parameterstandardname'][0], round_to_n(qs['p025__avg'],3), round_to_n(qs['p975__avg'],3)]
        return results

    
    def getPlatforms(self):
        '''
        Get a list of the unique platforms that are left based on the current query criteria.  Also
        return the UUID's of those, since we need to return those to perform the query later.
        Lastly, we assume here that the name is unique and is also used for the id - this is enforced on 
        data load.
        '''
        qs=self.qs.values('platform__uuid', 'platform__name', 'platform__color').distinct()
        results=[]
        for row in qs:
            name=row['platform__name']
            id=row['platform__name']
            color=row['platform__color']
            if name is not None and id is not None:
                results.append((name,id,color,))
        return results
    
    def getTime(self):
        '''
        Based on the current selected query criteria, determine the available time range.  That'll be
        returned as a 2-tuple as the min and max values that are selectable.
        '''

        # Documentation of some query optimization (tested with dorado & tethys data from June 2010 loaded with a stide of 100)
        # =====================================================================================================================
        # The statements:
        #   qs=self.qs.aggregate(Max('instantpoint__timevalue'), Min('instantpoint__timevalue'))
        #   return (qs['instantpoint__timevalue__min'], qs['instantpoint__timevalue__max'],)
        # produce this SQL which takes 75.2 ms to execute:

        # stoqs_june2011=# explain analyze SELECT DISTINCT MAX("stoqs_instantpoint"."timevalue") AS "instantpoint__timevalue__max", MIN("stoqs_instantpoint"."timevalue") AS "instantpoint__timevalue__min" FROM "stoqs_activity" LEFT OUTER JOIN "stoqs_instantpoint" ON ("stoqs_activity"."id" = "stoqs_instantpoint"."activity_id");
        #                                                                                    QUERY PLAN                                                                                    
        # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  HashAggregate  (cost=738.13..738.14 rows=1 width=8) (actual time=75.154..75.154 rows=1 loops=1)
        #    ->  Aggregate  (cost=738.11..738.12 rows=1 width=8) (actual time=75.144..75.145 rows=1 loops=1)
        #          ->  Merge Left Join  (cost=0.00..629.34 rows=21755 width=8) (actual time=0.032..51.337 rows=21726 loops=1)
        #                Merge Cond: (stoqs_activity.id = stoqs_instantpoint.activity_id)
        #                ->  Index Scan using stoqs_activity_pkey on stoqs_activity  (cost=0.00..17.58 rows=45 width=4) (actual time=0.008..0.058 rows=36 loops=1)
        #                ->  Index Scan using stoqs_instantpoint_activity_id on stoqs_instantpoint  (cost=0.00..707.58 rows=21755 width=12) (actual time=0.016..19.982 rows=21726 loops=1)
        #  Total runtime: 75.231 ms
        # (7 rows)
        # 
        # The statements:
        #   qs=self.qs.aggregate(Max('enddate'), Min('startdate'))
        #   return (qs['startdate__min'], qs['enddate__max'],)
        # take 0.22 ms 
        # stoqs_june2011=# explain analyze SELECT DISTINCT MIN("stoqs_activity"."startdate") AS "startdate__min", MAX("stoqs_activity"."enddate") AS "enddate__max" FROM "stoqs_activity";
        #                                                      QUERY PLAN                                                       
        # -----------------------------------------------------------------------------------------------------------------------
        #  HashAggregate  (cost=5.69..5.70 rows=1 width=16) (actual time=0.154..0.156 rows=1 loops=1)
        #    ->  Aggregate  (cost=5.67..5.69 rows=1 width=16) (actual time=0.143..0.144 rows=1 loops=1)
        #          ->  Seq Scan on stoqs_activity  (cost=0.00..5.45 rows=45 width=16) (actual time=0.009..0.064 rows=36 loops=1)
        #  Total runtime: 0.219 ms
        # (4 rows)
        #
        # While only a fraction of a second different, it is 342 times faster!

        qs=self.qs.aggregate(Max('enddate'), Min('startdate'))
        return (time.mktime(qs['startdate__min'].timetuple())*1000, time.mktime(qs['enddate__max'].timetuple())*1000,)
    
    def getDepth(self):
        '''
        Based on the current selected query criteria, determine the available depth range.  That'll be
        returned as a 2-tuple as the min and max values that are selectable.
        '''
        # Original query that dives into the measurment table via instantpoint
        ##qs=self.qs.aggregate(Max('instantpoint__measurement__depth'), Min('instantpoint__measurement__depth'))
        ##return (qs['instantpoint__measurement__depth__min'],qs['instantpoint__measurement__depth__max'])

        # Alternate query to use stats stored with the Activity
        qs=self.qs.aggregate(Max('maxdepth'), Min('mindepth'))
        return ('%.2f' % qs['mindepth__min'], '%.2f' % qs['maxdepth__max'])
        
    def getSimpleDepthTime(self):
        '''
        Based on the current selected query criteria for activities, return the associated SimpleDepth time series
        values as a 2-tuple list inside a 2 level hash of platform__name (with its color) and activity__name.
        '''
        sdt = {}
        colors = {}
        for p in self.getPlatforms():
            qs = self.qs.filter(platform__name = p[0]).values_list(
                                    'simpledepthtime__epochmilliseconds', 
                                    'simpledepthtime__depth',
                                    'name'
                                ).order_by('simpledepthtime__epochmilliseconds')
            sdt[p[0]] = {}
            colors[p[0]] = p[2]
            # Create hash with date-time series organized by activity__name key within a platform__name key
            # This will let flot plot the series with gaps between the surveys -- not connected
            for s in qs:
                try:
                    ##logger.debug('s[2] = %s', s[2])
                    sdt[p[0]][s[2]].append( [s[0], '%.2f' % s[1]] )
                except KeyError:
                    sdt[p[0]][s[2]] = []                                    # First time seeing activity__name, make it a list
                    if s[1]:
                        sdt[p[0]][s[2]].append( [s[0], '%.2f' % s[1]] )     # Append first value
                except TypeError:
                    continue                                                # Likely "float argument required, not NoneType"

        return({'sdt': sdt, 'colors': colors})

    def getSampleDepthTime(self):
        '''
        Based on the current selected query criteria for activities, return the associated SampleDepth time series
        values as a 2-tuple list.  The name similarity to getSimpleDepthTime name is a pure coincidence.
        '''
        samples = []
        qs = self.getSampleQS().values_list(
                                    'instantpoint__timevalue', 
                                    'depth',
                                    'instantpoint__activity__name',
                                    'name'
                                ).order_by('instantpoint__timevalue')
        for s in qs:
            ems = 1000 * to_udunits(s[0], 'seconds since 1970-01-01')
            # Kludgy handling of activity names - flot needs 2 items separated by a space to handle sample event clicking
            if (s[2].find('_decim') != -1):
                label = '%s %s' % (s[2].split('_decim')[0], s[3],)              # Lop off '_decim.nc (stride=xxx)' part of name
            elif (s[2].find(' ') != -1):
                label = '%s %s' % (s[2].split(' ')[0], s[3],)                   # Lop off everything after a space in the activity name
            else:
                label = '%s %s' % (s[2], s[3],)                                 # Show entire Activity name & sample name

            rec = {'label': label, 'data': [[ems, '%.2f' % s[1]]]}
            ##logger.debug('Appending %s', rec)
            samples.append(rec)

        return(samples)

    def getActivityParameterHistograms(self):
        '''
        Based on the current selected query criteria for activities, return the associated histograms of the selected
        parameters as a list of hashes, one hash per parameter with pairs of binlo and bincount for flot to make bar charts.
        Order in a somewhat complicated nested structure of hashes of hashes that permit the jQuery client to properly
        color and plot the data.
        '''
        aphHash = {}
        showAllParameterValuesFlag = self.getShow_All_Parameter_Values()
        showSigmatParameterValuesFlag = self.getShow_Sigmat_Parameter_Values()
        showStandardnameParameterValuesFlag = self.getShow_StandardName_Parameter_Values()
        for pa in models.Parameter.objects.using(self.dbname).all():

            # Apply (negative) logic on whether to continue with creating histograms based on checkboxes checked in the queryUI
            if not showAllParameterValuesFlag:
                if not showStandardnameParameterValuesFlag:
                    if not showSigmatParameterValuesFlag:
                        continue
                    elif pa.standard_name != 'sea_water_sigma_t':
                        continue
                elif not pa.standard_name:
                        continue

            histList = {}
            binwidthList = {}
            platformList = {}
            activityList = {}
            # Collect histograms organized by activity and platform names.  The SQL execution is sequential, a query
            # is executed for each parameter and here we organize by platform and activity.
            for aph in self.getActivityParameterHistogramsQS().select_related().filter(
                                activityparameter__parameter=pa).values('activityparameter__activity__name', 
                                'activityparameter__activity__platform__name', 'binlo', 'binhi', 'bincount').order_by(
                                'activityparameter__activity__platform__name', 'activityparameter__activity__name', 'binlo'):
                # Save histogram data by activity name
                try:
                    histList[aph['activityparameter__activity__name']].append([aph['binlo'], aph['bincount']])
                except KeyError:
                    # First time seeing this activity name, create a list and add the first histogram point
                    histList[aph['activityparameter__activity__name']] = []
                    histList[aph['activityparameter__activity__name']].append([aph['binlo'], aph['bincount']])
                    binwidthList[aph['activityparameter__activity__name']] = []
                    binwidthList[aph['activityparameter__activity__name']] = aph['binhi'] - aph['binlo']
                    platformList[aph['activityparameter__activity__name']] = []
                    platformList[aph['activityparameter__activity__name']].append(aph['activityparameter__activity__platform__name'])

                    logger.debug('pa.name = %s, aname = %s', pa.name, aph['activityparameter__activity__name'])

            # Unwind the platformList to get activities by platform name
            for an, pnList in platformList.iteritems():
                logger.debug('an = %s, pnList = %s', an, pnList)
                for pn in pnList:
                    try:
                        activityList[pn].append(an)
                    except KeyError:
                        activityList[pn] = []
                        activityList[pn].append(an)

            # Build the final data structure organized by platform -> activity
            plHash = {}
            for plat in activityList.keys():
                logger.debug('plat = %s', plat)
                for an in activityList[plat]:
                    try:
                        plHash[plat][an] = {'binwidth': binwidthList[an], 'hist': histList[an]}
                    except KeyError:
                        plHash[plat] = {}
                        plHash[plat][an] = {'binwidth': binwidthList[an], 'hist': histList[an]}

            # Assign histogram data to the hash keyed by parameter name
            if plHash:
                aphHash[pa.name] = plHash

        # Make RGBA colors from the hex colors - needed for opacity in flot bars
        rgbas = {}
        for p in self.getPlatforms():
            r,g,b = (p[2][:2], p[2][2:4], p[2][4:])
            rgbas[p[0]] = 'rgba(%d, %d, %d, 0.4)' % (int(r,16), int(g,16), int(b,16))

        return {'histdata': aphHash, 'rgbacolors': rgbas}

    def getActivityParamHistRequestPNGs(self):
        '''
        Return list of URLs that return a PNG image for the histograms of paramters contained in
        the Activity queryset.  The client can display these with an <img src=".." /> tag.
        '''
        urlList = []
        for qs in self.getActivityParameterHistogramsQS():
            pass

        return urlList

    def getParameterPlatformDatavaluePNG(self):
        '''
        Called when user interface has selected just one Parameter and just one Platform, in which case
        produce a depth-time section plot for overlay on the flot plot.  Return a png image file name for inclusion
        in the AJAX response.
        '''
        if not self.getDisplay_Parameter_Platform_Data():
            return
        if len(self.kwargs['parametername']) != 1:
            return
        if len(self.kwargs['platforms']) != 1:
            return

        # Setup Matplotlib for running on the server
        os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
        import matplotlib
        matplotlib.use('Agg')               # Force matplotlib to not use any Xwindows backend
        import matplotlib.pyplot as plt

        from matplotlib.mlab import griddata
        from matplotlib import mpl
        import numpy as np
        import string
        import random
        from stoqs.views.KML import readCLT

        # griddata parameters
        tgrid_max = 1000            # Reasonable maximum width for time-depth-flot plot is about 1000 pixels
        dgrid_max = 100             # Height of time-depth-flot plot area is 335 pixels
        dinc = 0.5                  # Average vertical resolution of AUV Dorado

        # Use session ID so that different users don't stomp on each other with their section plots
        if self.request.session.has_key('sessionID'):
            sessionID = self.request.session['sessionID']
        else:
            sessionID = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(7))
            self.request.session['sessionID'] = sessionID
        sectionPngFile = self.kwargs['parametername'][0] + '_' + self.kwargs['platforms'][0] + '_' + sessionID + '.png'
        sectionPngFileFullPath = os.path.join(settings.MEDIA_ROOT, 'sections', sectionPngFile)
        colorbarPngFile = self.kwargs['parametername'][0] + '_' + self.kwargs['platforms'][0] + '_colorbar_' + sessionID + '.png'
        colorbarPngFileFullPath = os.path.join(settings.MEDIA_ROOT, 'sections', colorbarPngFile)
        
        # Estimate horizontal (time) grid spacing by number of points in selection, expecting that simplified depth-time
        # query has salient points, typically in the vertices of the yo-yos.  
        xi = None
        if self.kwargs.has_key('time'):
            if self.kwargs['time'][0] is not None and self.kwargs['time'][1] is not None:
                dstart = datetime.strptime(self.kwargs['time'][0], '%Y-%m-%d %H:%M:%S') 
                dend = datetime.strptime(self.kwargs['time'][1], '%Y-%m-%d %H:%M:%S') 

                sdt_count = self.qs.filter(platform__name = self.kwargs['platforms'][0]).values_list('simpledepthtime__depth').count()
                sdt_count = int(sdt_count / 2)                 # 2 points define a line, take half the number of simpledepthtime points
                logger.debug('Half of sdt_count from query = %d', sdt_count)
                if sdt_count > tgrid_max:
                    sdt_count = tgrid_max

                tmin = time.mktime(dstart.timetuple())
                tmax = time.mktime(dend.timetuple())
                xi = np.linspace(tmin, tmax, sdt_count)
                logger.debug('xi = %s', xi)

        # Make depth spacing dinc m, limit to time-depth-flot resolution (dgrid_max)
        yi = None
        if self.kwargs.has_key('depth'):
            if self.kwargs['depth'][0] is not None and self.kwargs['depth'][1] is not None:
                dmin = float(self.kwargs['depth'][0])
                dmax = float(self.kwargs['depth'][1])
                y_count = int((dmax - dmin) / dinc )
                if y_count > dgrid_max:
                    y_count = dgrid_max
                yi = np.linspace(dmin, dmax, y_count)
                logger.debug('yi = %s', yi)

        # Collect the scattered datavalues(time, depth) and grid them
        if xi is not None and yi is not None:
            # Estimate a scale factor to apply to the x values on drid data so that x & y values are visually equal for the flot plot
            # which is assumed to be 3x wider than tall.  Approximate horizontal coverage by Dorado is 1 m/s.
            scale_factor = float(tmax -tmin) / (dmax - dmin) / 3.0
            logger.debug('scale_factor = %f', scale_factor)
            xi = xi / scale_factor

            try:
                os.remove(sectionPngFileFullPath)
            except Exception, e:
                logger.warn(e)

            logger.debug('Gridding data with sdt_count = %d, and y_count = %d', sdt_count, y_count)
            x = []
            y = []
            z = []
            qs_mp = self.getMeasuredParametersQS().values('measurement__instantpoint__timevalue', 'measurement__depth', 'datavalue')
            for mp in qs_mp:
                x.append(time.mktime(mp['measurement__instantpoint__timevalue'].timetuple()) / scale_factor)
                y.append(mp['measurement__depth'])
                z.append(mp['datavalue'])
           
            try:
                zi = griddata(x, y, z, xi, yi, interp='nn')
            except KeyError, e:
                logger.exception('Got KeyError: Could not grid the data')
                return None
            except Exception, e:
                logger.exception('Could not grid the data')
                return None

            parm_info = self.getParameterMinMax()
            try:
                # Make the plot
                # contour the gridded data, plotting dots at the nonuniform data points.
                # See http://scipy.org/Cookbook/Matplotlib/Django
                fig = plt.figure(figsize=(6,3))
                ax = fig.add_axes((0,0,1,1))
                ax.set_xlim(tmin / scale_factor, tmax / scale_factor)
                ax.set_ylim(dmax, dmin)
                clt = readCLT(os.path.join(settings.STATIC_ROOT, 'colormaps', 'jetplus.txt'))
                cm_jetplus = matplotlib.colors.ListedColormap(np.array(clt))
                ax.contourf(xi, yi, zi, clevs=np.linspace(parm_info[1], parm_info[2], 19), cmap=cm_jetplus)
                ax.scatter(x, y, marker='.', c='k', s=1, zorder=10)

                # Add sample locations and names
                xsamp = []
                ysamp = []
                sname = []
                for s in self.getSampleQS().values('instantpoint__timevalue', 'depth', 'name'):
                    xsamp.append(time.mktime(s['instantpoint__timevalue'].timetuple()))
                    ysamp.append(s['depth'])
                    sname.append(s['name'])
                ax.scatter(xsamp, ysamp, marker='o', c='w', s=15, zorder=10)
                for x,y,sn in zip(xsamp, ysamp, sname):
                    plt.annotate(sn, xy=(x,y), xytext=(5,-5), textcoords = 'offset points')

                fig.savefig(sectionPngFileFullPath, dpi=120, transparent=True)
                plt.close()
            except Exception,e:
                logger.exception('Could not plot the data')
                return None

            try:
                # Make colorbar as a separate figure
                cb_fig = plt.figure(figsize=(5, 0.8))
                cb_ax = cb_fig.add_axes([0.1, 0.8, 0.8, 0.2])
                logger.debug('parm_info = %s', parm_info)
                parm_units = models.Parameter.objects.filter(name=parm_info[0]).values_list('units')[0][0]
                logger.debug('parm_units = %s', parm_units)
                norm = mpl.colors.Normalize(vmin=parm_info[1], vmax=parm_info[2], clip=False)
                cb = mpl.colorbar.ColorbarBase( cb_ax, cmap=cm_jetplus,
                                                norm=norm,
                                                ticks=[parm_info[1], parm_info[2]],
                                                orientation='horizontal')
                cb.ax.set_xticklabels([str(parm_info[1]), str(parm_info[2])])
                cb.set_label('%s (%s)' % (parm_info[0], parm_units))
                logger.debug('ticklabels = %s', [str(parm_info[1]), str(parm_info[2])])
                cb_fig.savefig(colorbarPngFileFullPath, dpi=120, transparent=True)
                plt.close()
            except Exception,e:
                logger.exception('Could not plot the colormap')
                return None

            return sectionPngFile, colorbarPngFile


    #
    # Methods that generate Q objects used to populate the query.
    #    
        
    def _parametersQ(self, parameters):
        '''
        Build a Q object to be added to the current queryset as a filter.  This should 
        ensure that our result doesn't contain any parameters that were not selected.
        This the same function as _parameternameQ(), assume a query on parameters is a
        query on parameter.name.
        '''
        q=Q()
        if parameters is None:
            return q
        else:
            q=Q(activityparameter__parameter__name__in=parameters)
        return q
    
        
    def _parameternameQ(self, parametername):
        '''
        Build a Q object to be added to the current queryset as a filter.  This should 
        ensure that our result doesn't contain any parameter names that were not selected.
        '''
        q=Q()
        if parametername is None:
            return q
        else:
            q=Q(activityparameter__parameter__name__in=parametername)
        return q

    def _parameterstandardnameQ(self, parameterstandardname):
        '''
        Build a Q object to be added to the current queryset as a filter.  This should 
        ensure that our result doesn't contain any parameter standard_names that were not selected.
        '''
        q=Q()
        if parameterstandardname is None:
            return q
        else:
            q=Q(activityparameter__parameter__standard_name__in=parameterstandardname)
        return q




    def _platformsQ(self, platforms):
        '''
        Build a Q object to be added to the current queryset as a filter.  This will ensure that we
        only generate the other values/sets for platforms that were selected.
        '''
        q=Q()
        if platforms is None:
            return q
        else:
            q=Q(platform__name__in=platforms)
        return q    
    
    def _timeQ(self, times):
        '''
        Build a Q object to be added to the current queryset as a filter.  This ensures that we limit
        things down based on the time range selected by the user.
        '''
        q=Q()
        if not times:
            return q
        if times[0] is not None:
            q=Q(enddate__gte=times[0])
        if times[1] is not None:
            q=q & Q(startdate__lte=times[1])
        return q
    
    def _depthQ(self, depth):
        '''
        Build a Q object to be added to the current queryset as a filter.  Once again, we want
        to make sure that we only generate the "leftover" components based on the selected depth
        range.
        '''
        q=Q()
        if not depth:
            return q
        if depth[0] is not None:
            q=Q(maxdepth__gte=depth[0])
        if depth[1] is not None:
            q=q & Q(mindepth__lte=depth[1])
        return q
    
    #
    # Methods to get the query used based on the current Q object.
    #
    def getSQLWhere(self):
        '''
        This method will generate a pseudo-query, and then normalize it to a standard SQL query.  While for
        PostgreSQL this is usually the actual query, we might need to massage it a bit to handle quoting
        issues and such.  The string representation of the queryset's query attribute gives us the query.
        
        This is really useful when we want to generate a new mapfile based on the current query result.  We just want
        the WHERE clause of the query, since that's where the predicate exists.
        '''
        querystring = str(self.qs.query)
        
        return querystring

    def getActivityGeoQuery(self, Q_object = None):
        '''
        This method generates a string that can be put into a Mapserver mapfile DATA statment.
        It is for returning Activities.
        '''
        qs = self.qs

        # Add any more filters (Q objects) if specified
        if Q_object:
            qs = qs.filter(Q_object)

        # Query for mapserver
        geo_query = '''geom from (%s)
            as subquery using unique gid using srid=4326''' % self.postgresifySQL(qs.query)
        
        return geo_query

    def getSampleGeoQuery(self, Q_object = None):
        '''
        This method generates a string that can be put into a Mapserver mapfile DATA statment.
        It is for returning Samples.
        '''
        qs = self.getSampleQS()

        # Add any more filters (Q objects) if specified
        if Q_object:
            qs = qs.filter(Q_object)

        # Query for mapserver
        geo_query = '''geom from (%s)
            as subquery using unique gid using srid=4326''' % self.postgresifySQL(qs.query)
        
        return geo_query

    def getActivityMaptrackExtent(self, srid=4326):
        '''
        Return GEOSGeometry extent of all the maptracks contained in the Activity geoqueryset
        The result can be directly passed out for direct use in a OpenLayers
        '''
        extent = None
        try:
            geomstr = 'LINESTRING (%s %s, %s %s)' % self.qs.extent()
        except:
            logger.exception('Tried to get extent for self.qs.query =  %s, but failed', str(self.qs.query))
        try:
            extent = fromstr(geomstr, srid=srid)
        except:
            logger.exception('Could not get extent for geomstr = %s, srid = %d', geomstr, srid)
        try:
            extent.transform(900913)
        except:
            logger.exception('Cannot get transorm to 900913 for geomstr = %s, srid = %d', geomstr, srid)
        
        return extent


    #
    # Utility methods used just by this class
    #
    def postgresifySQL(self, query):
        '''
        Given a generic database agnostic Django query string modify it using regular expressions to work
        on a PostgreSQL server.
        '''
        # Get text of query to quotify for Postgresql
        q = str(query)

        # Remove double quotes from around all table and colum names
        q = q.replace('"', '')
        ##logger.debug('Before: %s', q)

        # Add aliases for geom and gid - Activity
        q = q.replace('stoqs_activity.id', 'stoqs_activity.id as gid', 1)
        q = q.replace('= stoqs_activity.id as gid', '= stoqs_activity.id', 1)           # Fixes problem with above being applied to Sample query join
        q = q.replace('stoqs_activity.maptrack', 'stoqs_activity.maptrack as geom')
        q = q.replace('stoqs_measurement.geom', 'ST_AsText(stoqs_measurement.geom)')    # For sql ajax response to decode lat & lon
        # Add aliases for geom and gid - Sample
        q = q.replace('stoqs_sample.id', 'stoqs_sample.id as gid', 1)
        q = q.replace('stoqs_sample.geom', 'stoqs_sample.geom as geom')

        # Quotify things that need quotes
        QUOTE_NAMEEQUALS = re.compile('name\s+=\s+(?P<argument>\S+)')
        QUOTE_DATES = re.compile('(?P<argument>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)')
        QUOTE_INS = re.compile('IN\s+\((?P<argument>[^\)]+)\)')

        q = QUOTE_NAMEEQUALS.sub(r"name = '\1'", q)
        q = QUOTE_DATES.sub(r"'\1'", q)
        q = QUOTE_INS.sub(r"IN ('\1')", q)

        ##logger.debug('After: %s', q)

        return q
