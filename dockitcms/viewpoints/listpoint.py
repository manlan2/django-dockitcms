from dockitcms.utils import ConfigurableTemplateResponseMixin, generate_object_detail_scaffold, generate_object_list_scaffold

from common import BaseCollectionViewPoint

import dockit
from dockit.views import ListView, DetailView

from django.conf.urls.defaults import patterns, url
from django import forms
from django.template import Template, TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _


TEMPLATE_SOURCE_CHOICES = [
    ('name', _('By Template Name')),
    ('html', _('By Template HTML')),
]

class PointListView(ConfigurableTemplateResponseMixin, ListView):
    pass

class PointDetailView(ConfigurableTemplateResponseMixin, DetailView):
    pass


class ListViewPoint(BaseCollectionViewPoint):
    list_template_source = dockit.CharField(choices=TEMPLATE_SOURCE_CHOICES, default='name')
    list_template_name = dockit.CharField(default='dockitcms/list.html', blank=True)
    list_template_html = dockit.TextField(blank=True)
    list_content = dockit.TextField(blank=True)
    detail_template_source = dockit.CharField(choices=TEMPLATE_SOURCE_CHOICES, default='name')
    detail_template_name = dockit.CharField(default='dockitcms/detail.html', blank=True)
    detail_template_html = dockit.TextField(blank=True)
    detail_content = dockit.TextField(blank=True)
    paginate_by = dockit.IntegerField(blank=True, null=True)
    
    list_view_class = PointListView
    detail_view_class = PointDetailView
    
    
    def get_document(self):
        doc_cls = self.collection.get_document()
        view_point = self
        class WrappedDoc(doc_cls):
            def get_absolute_url(self):
                return view_point.reverse('detail', self.pk)
            
            class Meta:
                proxy = True
        
        return WrappedDoc
    
    def _configuration_from_prefix(self, params, prefix):
        config = dict()
        for key in ('template_source', 'template_name', 'template_html', 'content'):
            config[key] = params.get('%s_%s' % (prefix, key), None)
        return config
    
    def get_urls(self):
        document = self.get_document()
        params = self.to_primitive(self)
        return patterns('',
            url(r'^$', 
                self.list_view_class.as_view(document=document,
                                      configuration=self._configuration_from_prefix(params, 'list'),
                                      paginate_by=params.get('paginate_by', None)),
                name='index',
            ),
            url(r'^(?P<pk>.+)/$', 
                self.detail_view_class.as_view(document=document,
                                        configuration=self._configuration_from_prefix(params, 'detail'),),
                name='detail',
            ),
        )
    
    
    
    def _clean_template_html(self, content):
        if not content:
            return content
        try:
            Template(content)
        except TemplateSyntaxError, e:
            raise forms.ValidationError(unicode(e))
        return content
    
    #TODO add model level validation
    def clean_list_template_html(self):
        return self._clean_template_html(self.cleaned_data.get('list_template_html'))
    
    def clean_detail_template_html(self):
        return self._clean_template_html(self.cleaned_data.get('detail_template_html'))
    
    def clean_list_content(self):
        return self._clean_template_html(self.cleaned_data.get('list_content'))
    
    def clean_detail_content(self):
        return self._clean_template_html(self.cleaned_data.get('detail_content'))
    
    def clean(self):
        #TODO pump the error to their perspective field
        if self.cleaned_data.get('list_template_source') == 'name':
            if not self.cleaned_data.get('list_template_name'):
                raise forms.ValidationError(_('Please specify a list template name'))
        if self.cleaned_data.get('list_template_source') == 'html':
            if not self.cleaned_data.get('list_template_html'):
                raise forms.ValidationError(_('Please specify the list template html'))
        
        if self.cleaned_data.get('detail_template_source') == 'name':
            if not self.cleaned_data.get('detail_template_name'):
                raise forms.ValidationError(_('Please specify a detail template name'))
        if self.cleaned_data.get('detail_template_source') == 'html':
            if not self.cleaned_data.get('detail_template_html'):
                raise forms.ValidationError(_('Please specify the detail template html'))
        return self.cleaned_data
    
    class Meta:
        typed_key = 'listview'

