from logging import getLogger
from copy import deepcopy
from string import strip
from ZTUtils import make_hidden_input
from DateTime import DateTime
from DateTime.interfaces import TimeError

from zope.component import queryUtility
from plone.app.layout.viewlets.common import SearchBoxViewlet

from Products.Archetypes.interfaces import IVocabulary
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.solr.interfaces import ISolrConnectionConfig

log = getLogger(__name__)

DATE_LOWERBOUND = '1000-01-05T23:00:00Z'
DATE_UPPERBOUND = '2499-12-30T23:00:00Z'

def param(view, name):
    """ return a request parameter as a list """
    value = view.request.form.get(name, [])
    if isinstance(value, basestring):
        value = [value]
    return value


def facetParameters(context, request):
    """ determine facet fields to be queried for """
    marker = []
    fields = request.get('facet.field', request.get('facet_field', marker))
    ranges = request.get('facet.range', request.get('facet_range', marker))
    if isinstance(fields, basestring):
        fields = [fields]
    if fields is marker:
        fields = getattr(context, 'facet_fields', marker)
    if fields is marker:
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            fields = config.facets
    if isinstance(ranges, basestring):
        ranges = [ranges]
    if ranges is marker:
        ranges = getattr(context, 'facet_ranges', marker)
    if ranges is marker:
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            ranges = ['Date', 'expires', 'modified'] #config.facetranges
    types = dict()
    for f in fields:
        types.update({f:'standard'})
    for r in ranges:
        types.update({r:'range'})
    dependencies = {}
    for idx, field in enumerate(fields):
        if ':' in field:
            facet, dep = map(strip, field['name'].split(':', 1))
            dependencies[facet] = map(strip, dep.split(','))
    return dict(fields=tuple(fields) + tuple(ranges), 
                types=types, 
                dependencies=dependencies)


class FacetMixin:
    """ mixin with helpers common to the viewlet and view """

    hidden = ViewPageTemplateFile('templates/hiddenfields.pt')

    def hiddenfields(self):
        """ render hidden fields suitable for inclusion in search forms """
        facet_params = facetParameters(self.context, self.request)
        queries = param(self, 'fq')
        facets = filter(lambda f: facet_params['types'][f] == 'standard', facet_params['fields'])
        ranges = filter(lambda f: facet_params['types'][f] == 'range', facet_params['fields'])
        return self.hidden(facets=facets, ranges=ranges, queries=queries)


class SearchBox(SearchBoxViewlet, FacetMixin):
    index = ViewPageTemplateFile('templates/searchbox.pt')


class SearchFacetsView(BrowserView, FacetMixin):
    """ view for displaying facetting info as provided by solr searches """

    def __init__(self, context, request):
        pdict = facetParameters(context, request)
        self.facet_fields = pdict['fields']
        self.facet_types = pdict['types']

        standard = filter(lambda f: self.facet_types[f] == 'standard', self.facet_fields)
        ranges = filter(lambda f: self.facet_types[f] == 'range', self.facet_fields)
        self.default_query = {'facet': 'true',
                              'facet.field': standard,
                              'facet.range': ranges, 
                              'facet.range.start': 'NOW/DAY-6MONTHS',
                              'facet.range.end': 'NOW/DAY', 
                              'facet.range.gap': '+7DAYS',
                              'facet.range.other': 'all',
                             }

        self.submenus = [dict(title=field, id=field) for field in self.facet_fields]
        self.queryparam = 'fq'
        BrowserView.__init__(self, context, request)


    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        self.form = deepcopy(self.default_query)
        self.form.update(deepcopy(self.request.form))

        if not 'results' in self.kw or \
                    not hasattr(self.kw['results'], 'facet_counts'):

            query = deepcopy(self.form)
            catalog = getToolByName(self.context, 'portal_catalog')
            self.results = catalog(query)
            if not 'results' in self.kw:
                self.kw['results'] = self.results

        if not getattr(self, 'results', None):
            self.results = self.kw['results']

        facet_counts = getattr(self.results, 'facet_counts', {})
        voctool = getToolByName(self.context, 'portal_vocabularies', None)
        self.vocDict = dict()

        for field in self.facet_fields:
            voc = voctool.getVocabularyByName(field)
            if IVocabulary.providedBy(voc):
                self.vocDict[field] = ( voc.Title(), 
                                        voc.getVocabularyDict(self.context))
            elif facet_counts: 
                # we don't have a matching vocabulary, so we fake one
                before = after = -1
                if field in facet_counts['facet_fields']:
                    field_values = facet_counts['facet_fields'][field].keys()

                elif field in facet_counts['facet_ranges']:
                    field_values= facet_counts['facet_ranges'][field]['counts'].keys()
                    before = facet_counts['facet_ranges'][field].get('before', -1)
                    after = facet_counts['facet_ranges'][field].get('after', -1)
                else:
                    continue

                content = dict()
                if before >= 0:
                    content[DATE_LOWERBOUND] = ('Before', None)
                for value in field_values:
                    content[value] = (self.getDisplayValue(value), None)
                if after >= 0:
                    content[DATE_UPPERBOUND] = ('After', None)
                self.vocDict[field] = (self.getDisplayValue(field), content)
        return super(SearchFacetsView, self).__call__(*args, **kw)

    def getDisplayValue(self, value):
        try:
            datetime = DateTime(value)
            return datetime.strftime('%d.%m.%Y')
        except DateTime.SyntaxError:
            # so it's not a date, let's return it as-is for now
            return value
        except TimeError:
            return value

    def getResults(self):
        return self.results or self.kw['results']

    def getCounts(self):
        res = self.getResults()
        if not hasattr(res, 'facet_counts'):
            return {}
        counts = res.facet_counts['facet_fields']
        for rng in res.facet_counts['facet_ranges']:
            counts[rng] = res.facet_counts['facet_ranges'][rng]['counts']
        return counts

    def sort(self, submenu):
        return sorted(submenu, key=lambda x:x['count'], reverse=True)

    def sortrange(self, submenu):
        return sorted(submenu, key=lambda x:x['id'], reverse=False)

    def getMenu(self, 
                id='ROOT', 
                title=None, 
                vocab={}, 
                counts=None, 
                parent=None, 
                facettype=None):
        menu = []
        #lower_bound = dict(id='1000-01-05T23:00:00Z', 
        #                   title='Earlier', 
        #                   isrange=True, 
        #                   isstandard=False, 
        #                   selected=False, 
        #                   selected_from=False, 
        #                   selected_to=False, 
        #                   count=0, 
        #                   content=[])
        #upper_bound = dict(id='2499-12-30T23:00:00Z', 
        #                   title='Later', 
        #                   isrange=True, 
        #                   isstandard=False, 
        #                   selected=False, 
        #                   selected_from=False, 
        #                   selected_to=False, 
        #                   count=0, 
        #                   content=[])

        if not vocab and id == 'ROOT':
            vocab = self.vocDict
        if not counts and id == 'ROOT':
            counts = self.getCounts()

        count = 0
        if isinstance(counts, int):
            count = int(counts)

        if not facettype or id in self.facet_fields:
            facettype = self.facet_types.get(id, 'standard')
        isrange = facettype == 'range'
        isstandard = facettype == 'standard'

        if vocab:
            for term in vocab:
                submenu = []
                counts_sub = None
                if isinstance(counts, dict):
                    counts_sub = counts.get(term, None)
                title_sub = ''
                vocab_sub = vocab.get(term, {})
                if vocab_sub:
                    title_sub = vocab_sub[0]
                    vocab_sub = vocab_sub[1]
                submenu = self.getMenu(
                                    id=term, 
                                    title=title_sub, 
                                    vocab=vocab_sub, 
                                    counts=counts_sub, 
                                    parent=id, 
                                    facettype=facettype)
                menu.append(submenu)
            if isrange:
                menu = self.sortrange(menu)
            #    menu = [lower_bound] + menu + [upper_bound]
            else:
                menu = self.sort(menu)

            if isrange and not filter(lambda item: item['selected'], menu):
                menu[0]['selected_from'] = True
                menu[-1]['selected_to'] = True

        selected = False
        selected_from = False
        selected_to = False
        if parent not in [None, 'ROOT']:
            facet_counts = getattr(self.results, 'facet_counts')
            if isrange:
                date = self.request.get(parent, {}).get('query', [])
                # XXX: When is query not a DateTime object?
                if isinstance(date, DateTime):
                    date = date.HTML4()
                    range = self.request.get(parent, {}).get('range')
                    if range == 'min':
                        selected = id > date
                        selected_from = date == id
                    elif range == 'max':
                        selected = id < date
                        selected_to = date == id
                else:
                    selected = id in date 
                    selected_from = date and date[0] == id
                    selected_to = date and date[1] == id
            else:
                count = facet_counts['facet_fields'][parent][id]
                selected = False
                if count:
                    queried = self.request.get(parent)
                    if queried == id:
                        selected = True
                    elif isinstance(queried, (list, tuple)) and id in queried:
                        selected  = True

        return dict(id=id, 
                    title=title, 
                    isrange=isrange, 
                    isstandard=isstandard, 
                    selected=selected, 
                    selected_from=selected_from, 
                    selected_to=selected_to, 
                    count=count, 
                    content=menu)

    def showSubmenu(self, submenu):
        """Returns True if submenu has an entry with query or clearquery set,
            i.e. should be displayed
        """
        return not filter(lambda x: x.get('selected', False) \
                          or x['count']>0, submenu) == []

    def expandSubmenu(self, submenu):
        """Returns True if submenu has an entry with clearquery set, i.e.
           should be displayed expanded
        """
        return not filter(lambda x: x.has_key('clearquery'), submenu) == []

    def getHiddenFields(self):
        return make_hidden_input([x for x in self.form.items() if x[0] not in self.facet_fields])

