#!/usr/local/bin/python
# -*- coding: UTF-8 -*-
import re, copy, HTMLParser as hp

class Selector:
    ''' ----- initialization ----- '''
    def __init__(self, parsed_html):
        self._root = None
        self._cursor = None
        self._init(parsed_html)
    
    ''' ----- static methods ----- '''
    @staticmethod
    def _selector_match(selector, tag):
        selector_divide = []
        match_attr = None
        
        attr_m = None
        if '[' in selector:  # attribute
            attr_pattern = re.compile(r'\w*\[([a-zA-Z0-9_\-]+)([=~\|\^\$\*]?)=?[\'"]?([^\]\'"]*)[\'"]?\]$')
            m = attr_pattern.search(selector)
            if m:
                attr_m = m.groups()
                selector = attr_pattern.sub('', selector)

        if '#' in selector:  # id
            selector_divide = selector.split('#')
            match_attr = 'id'
        elif '.' in selector:  # class
            selector_divide = selector.split('.')
            match_attr = 'class'
        else:  # tag
            selector_divide = [selector, '']

        if attr_m is not None:
            selector_divide.append(attr_m)

        for i in range(len(selector_divide)):
            e = selector_divide[i]

            if e == '':
                continue
            if i == 0:  # tag part
                if tag['name'] != e:
                    return False
            elif i == 1:  # decorator part
                if match_attr not in tag['attributes']:
                    return False
                if match_attr == 'id' and tag['attributes']['id'] != e:
                    return False
                if match_attr == 'class' and e not in tag['attributes']['class']:
                    return False
            elif i== 2:  # attributes part
                a_attr, a_operator, a_value = e
                if a_attr not in tag['attributes']:
                    return False
                    
                val = tag['attributes'][a_attr]
                
                if a_operator == '=' and val != a_value:
                    return False
                if a_operator == '~' and not(re.search(r'(^|\\s)'+a_value+'(\\s|$)',  val)):
                    return False
                if a_operator == '|' and not(re.search(r'^'+a_value+'-?', val)):
                    return False
                if a_operator == '^' and val.find(a_value) != 0:
                    return False
                if a_operator == '$' and val.rfind(a_value) != (len(val)-len(a_value)):
                    return False
                if a_operator == '*' and a_value not in val:
                    return False

        return True

    ''' ----- private method ----- '''
    def _init(self, parsed_html):
        self._root = parsed_html
        self._cursor = parsed_html
    
    def _find(self, selector, tag):
        tag_list = []

        if self._selector_match(selector, tag):
            tag_list.append(tag)

        for x in tag['children']:
            buf = self._find(selector, x)
            tag_list.extend(buf)

        return tag_list

    ''' ----- public method ----- '''
    def find(self, selector):
        parts = selector.split(' ')
        tag_list = []
        current_tag = self._cursor

        for part in parts:
            part = part.strip()
            if part == '':
                continue
            if type(current_tag) == type([]):
                current_tag_backup = reduce(lambda x, y: x+y['children'], current_tag, [])
                if type(current_tag_backup) is type({}):
                    current_tag_backup = current_tag_backup['children']
                current_tag = []
                for c in current_tag_backup:
                    current_tag.extend(self._find(part, c))
            else:
                current_tag = self._find(part, current_tag)

            if part in parts[-1]:
                tag_list.extend(current_tag)

        self._cursor = tag_list

        return tag_list

    def walk_to(self, *walk_route):
        for step in walk_route:
            step = int(step)
            if type(self._cursor) is type([]):
                self._cursor = self._cursor[step]
            elif type(self._cursor) is type({}):
                self._cursor = self._cursor['children'][step]
        return self
    
    def walk(self, *walk_route):
        start = copy.deepcopy(self._cursor)
        out = self.walk_to(*walk_route).get_cursor()
        self._cursor = start
        return out
        
    
    def reset(self):
        self._cursor = self._root
        return self

    def set_root(self, parsed_html):
        self._init(parsed_html)
        return self

    def get_root(self):
        return copy.deepcopy(self._root)

    def get_cursor(self):
        return copy.deepcopy(self._cursor)


class Parser(hp.HTMLParser):
    ''' ----- initialization ----- '''
    def __init__(self, html_data=None):
        hp.HTMLParser.__init__(self)
        self._root = self._create_tag('')
        self._cursor = None

        if html_data != None:
            self.parse( html_data )

    ''' ----- interfaces implementation ----- '''
    def handle_starttag(self, name, attr):
        if self._cursor is None:
            parent = self._root
        else:
            parent = self._cursor
            
        attr_hash = {}
        for a_key, a_value in attr:
            if a_key == 'class':
                attr_hash[a_key] = a_value.split(' ')
            else:
                attr_hash[a_key] = a_value

        tag = self._create_tag(name, attributes=attr_hash, parent=parent)
        parent['children'].append(tag)

        self._cursor = tag

    def handle_data(self, data):
        self._cursor['data'] += data
        self._cursor['dataSet'].append(data)

    def handle_endtag(self, tag):
        self._cursor = self._cursor['parent']
        for i in range(len(self._cursor['children'])):
            self._cursor['children'][i]['parent'] = None
            del self._cursor['children'][i]['parent']

    ''' ----- static method ----- '''
    @staticmethod
    def _create_tag(name, **kwargs):
        out = {
            'name': name,
            'data': '',
            'dataSet':  [],
            'attributes': {},
            'parent': None,
            'children': []
        }
        out.update(kwargs)
        return out

    ''' ----- public method ----- '''
    def fetch(self):
        return copy.deepcopy(self._root)

    def parse(self, html_data):
        if type(html_data) is type(''):
            html_data = html_data.decode('utf-8')
        hp.HTMLParser.feed(self, html_data.strip())
        return self