# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static

# The database alias (the key of the DATABASES dictionary) will prefix all of our requests
pre = r'^(?P<dbAlias>[^/]+)/'  

# format is one of: 'html', 'csv', 'kml', 'json'
formatPat = r'(?P<format>[^/]{0,5})'

urlpatterns = patterns('',
            
    # New Map interfaces with inheritence of bootstrap template
    url(pre + r'activityWMS$', 'stoqs.views.wms.showActivityWMS', {}, name='show-activity-wms'),

    # Map interfaces
    url(pre + r'activitiesWMS$', 'stoqs.views.wms.showActivitiesWMS', {}, name='show-activities-wms'),
    url(pre + r'parametersWMS$', 'stoqs.views.wms.showParametersWMS', {}, name='show-parameters-wms'),
    url(pre + r'platformsWMS$', 'stoqs.views.wms.showPlatformsWMS', {}, name='show-platforms-wms'),

    # All STOQS objects - full object queries with .json, .xml, .html, and .csv responses
    url(pre + r'platformtype.?'      + formatPat, 'stoqs.views.showPlatformType',      {}, name='show-platformtype'),
    url(pre + r'platform.?'          + formatPat, 'stoqs.views.showPlatform',          {}, name='show-platform'),
    url(pre + r'parametergroupparameter.?'    + formatPat, 'stoqs.views.showParameterGroupParameter',    {}, name='show-parametergroupparameter'),
    url(pre + r'parametergroup.?'    + formatPat, 'stoqs.views.showParameterGroup',    {}, name='show-parametergroup'),
    url(pre + r'parameterresource.?' + formatPat, 'stoqs.views.showParameterResource', {}, name='show-parameterresource'),
    url(pre + r'platformresource.?'  + formatPat, 'stoqs.views.showPlatformResource',  {}, name='show-platformresource'),
    url(pre + r'measuredparameterresource.?'  + formatPat, 'stoqs.views.showMeasuredParameterResource',  {}, name='show-measuredparameterresource'),
    url(pre + r'resourceresource.?'  + formatPat, 'stoqs.views.showResourceResource',  {}, name='show-resourceresource'),
    url(pre + r'parameter.?'         + formatPat, 'stoqs.views.showParameter',         {}, name='show-parameter'),
    url(pre + r'activitytype.?'      + formatPat, 'stoqs.views.showActivityType',      {}, name='show-activitytype'),
    url(pre + r'activity.?'          + formatPat, 'stoqs.views.showActivity',          {}, name='show-activity'),
    url(pre + r'campaign.?'          + formatPat, 'stoqs.views.showCampaign',          {}, name='show-campaign'),
    url(pre + r'resourcetype.?'      + formatPat, 'stoqs.views.showResourceType',      {}, name='show-resourcetype'),
    url(pre + r'resource.?'          + formatPat, 'stoqs.views.showResource',          {}, name='show-resource'),
    url(pre + r'activityresource.?'  + formatPat, 'stoqs.views.showActivityResource',  {}, name='show-activityresource'),
    url(pre + r'activityparameter.?' + formatPat, 'stoqs.views.showActivityParameter', {}, name='show-activityparameter'),
    url(pre + r'simpledepthtime.?'   + formatPat, 'stoqs.views.showSimpleDepthTime',   {}, name='show-simpledepthtime'),
    url(pre + r'sampletype.?'        + formatPat, 'stoqs.views.showSampleType',        {}, name='show-sampletype'),
    url(pre + r'samplepurpose.?'     + formatPat, 'stoqs.views.showSamplePurpose',     {}, name='show-samplepuspose'),
    url(pre + r'sample.?'            + formatPat, 'stoqs.views.showSample',            {}, name='show-sample'),
    url(pre + r'analysismethod.?'    + formatPat, 'stoqs.views.showAnalysisMethod',    {}, name='show-analysismethod'),
    url(pre + r'instantpoint.?'      + formatPat, 'stoqs.views.showInstantPoint',      {}, name='show-instantpoint'),
    url(pre + r'measurement.?'       + formatPat, 'stoqs.views.showMeasurement',       {}, name='show-measurement'),

    # Requests that override BaseOutputer
    url(pre + r'sampledatatable.?'   + formatPat, 'stoqs.views.app.showSampleDT',      {}, name='show-sample-datatable'),
    url(pre + r'measuredparameter.?' + formatPat, 'stoqs.views.app.showMeasuredParameter',  {}, name='show-measuredparmeter'),
    url(pre + r'sampledparameter.?' + formatPat, 'stoqs.views.app.showSampledParameter',  {}, name='show-sampledparmeter'),
    url(pre + r'activityparameterhistogram.?'      
                                     + formatPat, 'stoqs.views.app.showActivityParameterHistogram',  {}, name='show-aph'),
    url(pre + r'resourceactivity.?' + formatPat, 'stoqs.views.app.showResourceActivity',  {}, name='show-resourceactivity'),
    url(pre + r'quicklookplots', 'stoqs.views.app.showQuickLookPlots',  {}, name='show-quicklookplots'),

    # URL For Chander's STOQQManager related views
    url(pre + r'query/summary/$', 'stoqs.views.query.queryData', {}, name='stoqs-query-summary'),
    url(pre + r'query/map/$', 'stoqs.views.query.queryMap', {}, name='stoqs-query-map'),
    url(pre + r'query/(?P<format>[^/]+)/?$', 'stoqs.views.query.queryData', {}, name='stoqs-query-results'),
    url(pre + r'query/', 'stoqs.views.query.queryUI', {}, name='stoqs-query-ui'),

    # Management, base of campaign, etc.
    url(r'campaigns.(?P<format>[^/]{3,5})$', 'stoqs.views.management.showCampaigns', {}, name='show-campaigns'),
    url(pre + r'mgmt$', 'stoqs.views.management.showDatabase', {}, name='show-database'),
    url(pre + r'deleteActivity/(?P<activityId>[0-9]+)$', 'stoqs.views.management.deleteActivity', {}, name='delete-activity'),
    url(pre + r'activitiesMBARICustom$', 'stoqs.views.management.showActivitiesMBARICustom', {}, name='show-activities'),

    # WFS - Tesing for exposing Sample data to the OpenLayers map
    # Prerequisites:
    #   su -y 'yum install libxml2-devel libxml2 libxslt-devel libxslt'
    #   pip install lxml
    #   pip install -e git+https://github.com/JeffHeard/ga_ows.git#egg=ga_ows
    #   export LD_LIBRARY_PATH='/usr/local/lib:$LD_LIBRARY_PATH' && python manage.py runserver 0.0.0.0:8000
    ##url(pre + r'wfs/?', WFS.as_view(
    ##    models=[m.Sample],          # everything but this is optional.
    ##    title='STOQS Sample WFS',
    ##    provider_name='MBARI',
    ##)),

    # Animation  
    url(pre + r'activitiesWMSAnimate$', 'stoqs.views.wms.showActivitiesWMSAnimate', {}, name='show-activities-wms-animate'),
        
    # format is either 'url' or 'image' 
    # url will return a persistant url for the created animation;  image will return the animaged GIF
    url(r'animatepoint/between/(?P<startDate>\w+)/(?P<endDate>\w+)/deltaminutes/(?P<deltaMinutes>\d+)/format/(?P<format>\w{3,5})/$', 
            'stoqs.views.animation.createAnimation',  {'rangeFlag': True}, name='create-animation-point'),  
    url(r'animatemap/between/(?P<startDate>\w+)/(?P<endDate>\w+)/deltaminutes/(?P<deltaMinutes>\d+)/format/(?P<format>\w{3,5})/$', 
            'stoqs.views.animation.createAnimation',  {'rangeFlag': False}, name='create-animation-map'),  

    # For testing only 
    url(r'testAnimateCoastwatch$', 'stoqs.views.wms.showActivitiesWMSAnimateCoastwatch', {} , name='test-animate-wms-coastwatch'),

    # If nothing above matches show the quey interface is a dbalias is specified, otherwise show the campaigns
    url(pre + '$', 'stoqs.views.query.queryUI', {}, name='base-campaign'),
    
    # Views related to generating permalinks for later use.
    url(pre + 'generate_permalink/', 'stoqs.views.permalinks.generate_permalink', {}, name='generate_permalink'),
    url(pre + 'permalink/(?P<id>[^/]*)/', 'stoqs.views.permalinks.load_permalink', {}, name='load_permalink'),

    url('^$', 'stoqs.views.management.showCampaigns', {}, name='show-default'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
