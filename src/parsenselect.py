#!/usr/local/bin/python
# -*- coding: UTF-8 -*-
import re, HTMLParser as hp

class Selector:
    """ initialization """
    def __init__(self, parsed_html):
        self._root = parsed_html
        self._cursor = parsed_html

    """ static method """
    def _selectorMatch(selector, tag):
        selector_divide = []
        match_attr = None

        a_key, a_value = None, None
        if '[' in selector:  # attribute
            pattern = re.compile(r".*\[(.+)\]")
            m = pattern.match(selector)
            a_key, a_value = map(lambda x: x.strip('\'"'), m.group(1).split('='))
            selector = pattern.sub('', selector)

        if '#' in selector:  # id
            selector_divide = selector.split('#')
            match_attr = 'id'
        elif '.' in selector:  # class
            selector_divide = selector.split('.')
            match_attr = 'class'
        else:  # tag
            selector_divide = [selector, '']

        if a_key is not None:
            selector_divide.append((a_key, a_value))

        res = True
        for i in range(len(selector_divide)):
            e = selector_divide[i]

            if e == '':
                continue
            if i == 0:  # tag part
                res = res and (tag['name'] == e)
            elif i == 1:  # decorator part
                if match_attr == 'id':
                    res = res and ('id' in tag['attributes'].keys() and tag['attributes']['id'] == e)
                elif match_attr == 'class':
                    res = res and ('class' in tag['attributes'].keys() and e in tag['attributes']['class'])
            elif i== 2:  # attributes part
                res = res and (e[0] in tag['attributes'].keys() and tag['attributes'][e[0]] == e[1])

        return res
    _selectorMatch = staticmethod(_selectorMatch)

    """ private method """
    def _find(self, selector, tag):
        tag_list = []

        if self._selectorMatch(selector, tag):
            tag_list.append(tag)

        for x in tag['children']:
            buf = self._find(selector, x)
            tag_list.extend(buf)

        return tag_list

    """ public method """
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

    def reset(self):
        self._cursor = self._root
        return self

    def setRoot(self, parsed_html):
        self._root = parsed_html
        self._cursor = parsed_html
        return self

    def getRoot(self):
        return self._root

    def getCursor(self):
        return self._cursor


class Parser(hp.HTMLParser):
    """ initialization """
    def __init__(self, html_data=None):
        hp.HTMLParser.__init__(self)
        self._root = self._createTag('')
        self._cursor = None

        if html_data != None:
            self.parse( html_data )

    """ interfaces implementation """
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

        tag = self._createTag(name, attributes=attr_hash, parent=parent, children=[])
        parent['children'].append(tag)

        self._cursor = tag

    def handle_data(self, data):
        self._cursor['data'] = data

    def handle_endtag(self, tag):
        self._cursor = self._cursor['parent']
        for i in range(len(self._cursor['children'])):
            self._cursor['children'][i]['parent'] = None
            del self._cursor['children'][i]['parent']

    """ static method """
    def _createTag(name, data='', attributes={}, parent=None, children=[]):
        return {
                'name': name,
                'data': data,
                'attributes': attributes,
                'parent': parent,
                'children': children
            }
    _createTag = staticmethod(_createTag)

    """ public method """
    def read(self):
        return self._root

    def parse(self, html_data):
        if type(html_data) is type(''):
            html_data = html_data.decode('utf-8')
        hp.HTMLParser.feed(self, html_data.strip())
        return self
