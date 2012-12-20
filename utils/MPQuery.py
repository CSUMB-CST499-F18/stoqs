__author__    = 'Mike McCann'
__copyright__ = '2012'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'

__doc__ = '''

MeasuredParameter Query class for managing aspects of building requests for MeasuredParameter datavalues.
Intended to be used by utils/STOQSQManager.py for preventing multiple traversals of qs_mp and by
views/__init__.py to support query by parameter value for the REST responses.

@undocumented: __doc__ parser
@status: production
@license: GPL
'''
from django.conf import settings
from django.db.models.query import RawQuerySet, REPR_OUTPUT_SIZE
from datetime import datetime
from stoqs.models import MeasuredParameter
from utils import postgresifySQL
import logging
import pprint
import re
import locale
import time
import os
import tempfile
import sqlparse

logger = logging.getLogger(__name__)

ITER_HARD_LIMIT = 10000

class MPQuerySet(object):
    '''
    A duck-typed class to simulate a GeoQuerySet that's suitable for use everywhere a GeoQuerySet may be used.
    This special class supports adapting MeasuredParameter RawQuerySets to make them look like regular
    GeoQuerySets.  See: http://ramenlabs.com/2010/12/08/how-to-quack-like-a-queryset/.  (I looked at Google
    again to see if self-joins are possible in Django, and confirmed that they are probably not.  
    See: http://stackoverflow.com/questions/1578362/self-join-with-django-orm.)
    '''
    def __init__(self, rawsql):
        self.rawsql = rawsql
        self.mp_query = MeasuredParameter.objects.raw(rawsql)
 
    def __iter__(self):
        '''
        Main way to access data that is used by interators in templates, etc.
        Simulate behavior of regular GeoQuerySets.  Modify & format output as needed.
        '''
        for mp in self.mp_query[:ITER_HARD_LIMIT]:
            row = { 'parameter__name': mp.parameter__name,
                    'parameter__standard_name': mp.parameter__standard_name,
                    'measurement__depth': mp.measurement__depth,
                    'measurement__geom': 'POINT (%s %s)' % (mp.measurement.geom.x, mp.measurement.geom.y),
                    'measurement__instantpoint__timevalue': mp.measurement__instantpoint__timevalue,
                    'measurement__instantpoint__activity__platform__name': mp.measurement__instantpoint__activity__platform__name,
                    'datavalue': mp.datavalue,
                    'parameter__units': mp.parameter__units
                  }
            yield row
 
    def __repr__(self):
        data = list(self[:REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)
 
    def __getitem__(self, k):
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
                "Negative indexing is not supported."
 
        if isinstance(k, slice):
            ordering = tuple(field.lstrip('-') for field in self.ordering)
            reverse = (ordering != self.ordering)
            if reverse:
                assert (sum(1 for field in self.ordering
                            if field.startswith('-')) == len(ordering)), \
                        "Mixed sort directions not supported."




            mpq = self.mp_query
 
            if k.stop is not None:
                mpq = mpq[:k.stop]
 
            rows = ([row + (MeasuredParameter,)
                     for row in mpq.values_list(*(ordering + ('pk',)))])
 
            rows.sort()
            if reverse:
                rows.reverse()
            rows = rows[k]
 
            pk_idx = len(ordering)
            klass_idx = pk_idx + 1
            mp_pks = [row[pk_idx] for row in rows
                            if row[klass_idx] is MeasuredParameter]
            mps = MeasuredParameter.objects.in_bulk(mp_pks)
 
            results = []
            for row in rows:
                pk = row[-2]
                klass = row[-1]
                if klass is MeasuredParameter:
                    mps[pk].type = 'measuredparameter'
                    results.append(mps[pk])
            return results
        else:
            return self[k:k+1][0]





    def count(self):
        return sum(1 for mp in self.mp_query)
 
    def all(self):
        return self._clone()
 
    def filter(self, *args, **kwargs):
        qs = self._clone()
        qs.mp_query = qs.mp_query.filter(*args, **kwargs)
        qs.sprocket_query = qs.sprocket_query.filter(*args, **kwargs)
        return qs
 
    def exclude(self, *args, **kwargs):
        qs = self._clone()
        qs.mp_query = qs.mp_query.exclude(*args, **kwargs)
        qs.sprocket_query = qs.sprocket_query.exclude(*args, **kwargs)
        return qs
 
    def order_by(self, *ordering):
        qs = self._clone()
        qs.mp_query = qs.mp_query.order_by(*ordering)
        qs.sprocket_query = qs.sprocket_query.order_by(*ordering)
        qs.ordering = ordering
        return qs
 
    def _clone(self):
        qs = GearQuerySet()
        qs.mp_query = self.mp_query._clone()
        qs.sprocket_query = self.sprocket_query._clone()
        qs.ordering = self.ordering
        return qs 


 

class MPQuery(object):
    '''
    This class is designed to handle building and managing queries against the MeasuredParameter table of the STOQS database.
    Special tooling is needed to perform parameter value queries which require building raw sql statements in order to
    execute the self joins needed on the measuredparameter table.  The structure of RawQuerySet returned is harmonized
    with the normal GeoQuerySet returned through regular .filter() operations.
    '''
    rest_select_items = '''stoqs_parameter.name as parameter__name,
                         stoqs_parameter.standard_name as parameter__standard_name,
                         stoqs_measurement.depth as measurement__depth,
                         stoqs_measurement.geom as measurement__geom,
                         stoqs_instantpoint.timevalue as measurement__instantpoint__timevalue, 
                         stoqs_platform.name as measurement__instantpoint__activity__platform__name,
                         stoqs_measuredparameter.datavalue as datavalue,
                         stoqs_parameter.units as parameter__units'''

    kml_select_items = ''
    contour_select_items = ''

    def __init__(self, request):
        '''
        This object saves instances of the QuerySet and count so that get_() methods work like a singleton to 
        return the value for the object.  MPQuery objects are meant to be instantiated by the STOQSQManager 
        buildQuerySet() method and are unique for each AJAX request.  After buildMPQuerySet() is executed
        the member values below can be accessed.
        '''
        self.request = request
        self.qs_mp = None
        self.sql = None
        self._count = None
        self._MProws = []
        
    def buildMPQuerySet(self, *args, **kwargs):
        '''
        Build the query set based on selections from the UI. For the first time through kwargs will be empty 
        and self.qs_mp will have no constraints and will be all of the MeasuredParameters in the database.
        '''

        if self.qs_mp is None:
            self.kwargs = kwargs
            self.qs_mp = self.getMeasuredParametersQS()
            self.sql = self.getMeasuredParametersPostgreSQL()

    def getQueryParms(self):
        '''
        Extract constraints from the querystring kwargs to construct a dictionary of query parameters
        that can be used as a filter for MeasuredParameters.  Handles all constraints except parameter
        value constraints.
        '''
        qparams = {}

        logger.info('self.kwargs = %s', pprint.pformat(self.kwargs))
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

        logger.debug('qparams = %s', pprint.pformat(qparams))

        return qparams

    def getMeasuredParametersQS(self):
        '''
        Return query set of MeasuremedParameters given the current constraints.  If no parameter is selected return None.

        What KML generation expects:
            data = [(mp.measurement.instantpoint.timevalue, mp.measurement.geom.x, mp.measurement.geom.y,
                     mp.measurement.depth, pName, mp.datavalue, mp.measurement.instantpoint.activity.platform.name)
                     for mp in qs_mp]

        What Viz.py expects:
            if type(qs_mp) == RawQuerySet:
                # Most likely because it is a RawQuerySet from a ParameterValues query
                for mp in qs_mp:
                    ##logger.debug('mp = %s, %s, %s', mp.timevalue, mp.depth, mp.datavalue)
                    x.append(time.mktime(mp.timevalue.timetuple()) / scale_factor)
                    y.append(mp.depth)
                    z.append(mp.datavalue)
            else:
                for mp in qs_mp.values('measurement__instantpoint__timevalue', 'measurement__depth', 'datavalue'):
                    x.append(time.mktime(mp['measurement__instantpoint__timevalue'].timetuple()) / scale_factor)
                    y.append(mp['measurement__depth'])
                    z.append(mp['datavalue'])
        '''

        logger.debug('dbalias = %s', self.request.META['dbAlias'])

        qparams = self.getQueryParms()

        qs_mp = MeasuredParameter.objects.using(self.request.META['dbAlias']).filter(**qparams)
        qs_mp = qs_mp.values('measurement__instantpoint__timevalue', 'measurement__geom')

        if self.kwargs.has_key('parametervalues'):
            if self.kwargs['parametervalues']:
                sql = postgresifySQL(str(qs_mp.query))
                logger.debug('\n\nsql before query = %s\n\n', sql)
                # Modify sql to do a self-join on MeasuredParameter selecting on data values
                sql_pv = self.addParameterValuesSelfJoins(sql, self.kwargs['parametervalues'])
                logger.debug('\n\nsql_pv for parametervalue query = %s\n\n', sql_pv)
                qs_mp = MeasuredParameter.objects.raw(sql_pv)

        if qs_mp:
            logger.debug('type(qs_mp) = %s', type(qs_mp))
            logger.debug(pprint.pformat(str(qs_mp.query)))
        else:
            logger.debug("No queryset returned for qparams = %s", pprint.pformat(qparams))
        return qs_mp

    def getMPCount(self):
        '''
        Get the actual count of measured parameters giving the exising query.  If private _count
        member variable exist return that, otherwise expand the query set as necessary to get and
        return the count.
        '''
        if not self._count:
            logger.debug('Counting MPs from qs_mp = %s', str(self.qs_mp))
            if type(self.qs_mp) == RawQuerySet:
                # Most likely a RawQuerySet from a ParameterValues selection
                self._count = sum(1 for mp in self.qs_mp)
            else:
                self._count = self.qs_mp.count()

        logger.debug('self._count = %d', self._count)
        return int(self._count)

    def getLocalizedMPCount(self):
        '''
        Apply commas to the count number and return as a string
        '''
        locale.setlocale(locale.LC_ALL, 'en_US')
        return locale.format("%d", self.getMPCount(), grouping=True)

    def getMeasuredParametersPostgreSQL(self):
        '''
        Return SQL string that can be executed against the postgres database
        '''
        sql = 'Check "Get actual count" checkbox to see the SQL for your data selection'
        if self._count:
            qs_mp = self.qs_mp

            if type(qs_mp) == RawQuerySet:
                sql = postgresifySQL(qs_mp.raw_query) + ';'
                sql = self.addParameterValuesSelfJoins(sql, self.kwargs['parametervalues'], select_items=self.rest_select_items)
                sql = '\c %s\n' % settings.DATABASES[self.request.META['dbAlias']]['NAME'] + sql
            else:
                qs_mp = qs_mp.values(   'measurement__instantpoint__activity__platform__name', 'measurement__instantpoint__timevalue', 
                                        'measurement__geom', 'parameter__name', 'datavalue')
                if qs_mp:
                    sql = '\c %s\n' % settings.DATABASES[self.request.META['dbAlias']]['NAME']
                    sql +=  postgresifySQL(str(qs_mp.query)) + ';'

        return sqlparse.format(sql, reindent=True, keyword_case='upper')

    def addParameterValuesSelfJoins(self, query, pvDict, select_items= '''stoqs_instantpoint.timevalue as instantpoint__timevalue, 
                                                                          stoqs_measurement.depth as measurement__depth,
                                                                          stoqs_measuredparameter.datavalue as datavalue'''):
        '''
        Given a Postgresified MeasuredParameter query string @query' modify it to add the MP self joins needed 
        to restrict the data selection to the ParameterValues specified in @pvDict.  Add to the required
        measuredparameter.id the select items in the comma separeated value string @select_items.
        Return a Postgresified query string that can be used by Django's Manage.raw().
        select_items can be altered as needed, examples:
            For Flot contour plot we need just depth and time.
            For KML output we need in addition: latitude, longitude, parameter name, and platform name
            For REST we need about everything
        '''
        # Example original Postgresified SQL
        #SELECT
        #    stoqs_measuredparameter.id,
        #    stoqs_measuredparameter.measurement_id,
        #    stoqs_measuredparameter.parameter_id,
        #    stoqs_measuredparameter.datavalue 
        #FROM
        #    stoqs_measuredparameter 
        #        INNER JOIN stoqs_measurement 
        #        ON (stoqs_measuredparameter.measurement_id = stoqs_measurement.id) 
        #            INNER JOIN stoqs_instantpoint 
        #            ON (stoqs_measurement.instantpoint_id = stoqs_instantpoint.id) 
        #                INNER JOIN stoqs_parameter 
        #                ON (stoqs_measuredparameter.parameter_id = stoqs_parameter.id) 
        #                    INNER JOIN stoqs_activity 
        #                    ON (stoqs_instantpoint.activity_id = stoqs_activity.id) 
        #                        INNER JOIN stoqs_platform 
        #                        ON (stoqs_activity.platform_id = stoqs_platform.id) 
        #WHERE
        #    (stoqs_instantpoint.timevalue <= '2012-09-13 18:19:04' AND
        #    stoqs_instantpoint.timevalue >= '2012-09-13 05:16:48' AND
        #    stoqs_parameter.name IN ('temperature') AND
        #    stoqs_measurement.depth >= -5.66 AND
        #    stoqs_platform.name IN ('dorado') AND
        #    stoqs_measurement.depth <= 153.85 )

        # Example Self-join SQL to insert into the string
        #select
        #    stoqs_measuredparameter.datavalue,
        #    stoqs_parameter_1.name              as name_1,
        #    stoqs_measuredparameter_1.datavalue as datavalue_1,
        #    stoqs_measuredparameter_1.datavalue as datavalue_1b,
        #    stoqs_parameter.name 
        #from
        #    stoqs_measuredparameter stoqs_measuredparameter_1 
        #        inner join stoqs_parameter stoqs_parameter_1 
        #        on stoqs_measuredparameter_1.parameter_id = stoqs_parameter_1.id 
        #            inner join stoqs_measuredparameter 
        #            stoqs_measuredparameter 
        #            on stoqs_measuredparameter_1.measurement_id = 
        #            stoqs_measuredparameter.measurement_id 
        #                inner join stoqs_parameter stoqs_parameter 
        #                on stoqs_parameter.id = stoqs_measuredparameter.
        #                parameter_id 
        #where
        #    (stoqs_parameter_1.name ='sea_water_sigma_t') and
        #    (stoqs_measuredparameter_1.datavalue >24.5) and
        #    (stoqs_measuredparameter_1.datavalue <25.0) and
        #    (stoqs_parameter.name ='temperature')

        # Used by getParameterPlatformDatavaluePNG(): 'measurement__instantpoint__timevalue', 'measurement__depth', 'datavalue
        # Used by REST requests in stoqs/views/__init__(): stoqs_parameter.name, stoqs_parameter.standard_name, stoqs_measurement.depth, stoqs_measurement.geom, stoqs_instantpoint.timevalue, stoqs_platform.name, stoqs_measuredparameter.datavalue, stoqs_parameter.units
        select_items = 'stoqs_measuredparameter.id, ' + select_items
        add_to_from = ''
        from_sql = '' 
        where_sql = '' 
        i = 0
        for pminmax in pvDict:
            i = i + 1
            add_to_from = add_to_from + 'stoqs_parameter p' + str(i) + ', '
            from_sql = from_sql + 'INNER JOIN stoqs_measuredparameter mp' + str(i) + ' '
            from_sql = from_sql + 'on mp' + str(i) + '.measurement_id = stoqs_measuredparameter.measurement_id '
            for k,v in pminmax.iteritems():
                # Prevent SQL injection attacks
                p = re.compile("[';]")
                if p.search(k) or p.search(v[0]) or p.search(v[1]):
                    raise Exception('Invalid ParameterValue constraint expression: %s, %s' % (k, v))
                where_sql = where_sql + "(p" + str(i) + ".name = '" + k + "') AND "
                where_sql = where_sql + "(mp" + str(i) + ".datavalue > " + str(v[0]) + ") AND "
                where_sql = where_sql + "(mp" + str(i) + ".datavalue < " + str(v[1]) + ") AND "
                where_sql = where_sql + "(mp" + str(i) + ".parameter_id = p" + str(i) + ".id) AND "

        q = query
        p = re.compile('SELECT .+ FROM')
        q = p.sub('SELECT ' + select_items + ' FROM', q)
        q = q.replace('SELECT FROM stoqs_measuredparameter', 'FROM ' + add_to_from + 'stoqs_measuredparameter')
        q = q.replace('FROM stoqs_measuredparameter', 'FROM ' + add_to_from + 'stoqs_measuredparameter')
        q = q.replace('WHERE', from_sql + ' WHERE' + where_sql)

        return q

