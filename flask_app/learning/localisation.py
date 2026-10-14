"""Language URL routing shared by legacy snapshots and Flask views."""
import re
from html import escape, unescape
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from .catalog import LANGUAGES

HOSTS = {'englishasaforeignlanguage.com', 'www.englishasaforeignlanguage.com',
         'englishasasecondlanguage.com', 'www.englishasasecondlanguage.com'}
EXCLUDED = ('/assets/', '/api/', '/health', '/private_products/', '/storage/', '/learning/')

def unprefix(path):
    parts = path.split('/', 2)
    if len(parts) > 1 and parts[1] in LANGUAGES:
        return '/' + (parts[2] if len(parts) > 2 else '')
    return path

def local_url(value, language):
    parsed = urlsplit(unescape(value))
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return value
    if parsed.netloc and parsed.netloc not in HOSTS:
        return value
    if not parsed.path.startswith('/') or parsed.path.startswith('//'):
        return value
    prefix = parsed.path.split('/', 2)[1]
    if prefix in LANGUAGES:
        language = prefix
    path = unprefix(parsed.path)
    if path.startswith(EXCLUDED) or path.startswith('/language/'):
        return value
    query = parse_qsl(parsed.query, keep_blank_values=True)
    chosen = dict(query).get('lang')
    if chosen in LANGUAGES:
        language = chosen
    query = [(key, val) for key, val in query if key != 'lang']
    return urlunsplit((parsed.scheme, parsed.netloc, '/' + language + path,
                       urlencode(query), parsed.fragment))

def local_links(html, language):
    return re.sub(r'\b(href|action)="([^"]*)"',
                  lambda m: m[1] + '="' + escape(local_url(m[2], language), quote=True) + '"', html)

class LanguagePaths:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        parts = path.split('/', 2)
        if len(parts) > 1 and parts[1] in LANGUAGES:
            environ['efl.url_language'] = parts[1]
            environ['SCRIPT_NAME'] = environ.get('SCRIPT_NAME', '') + '/' + parts[1]
            environ['PATH_INFO'] = unprefix(path)
        return self.app(environ, start_response)
