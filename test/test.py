#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import parsenselect as pns
import pprint

pp = pprint.PrettyPrinter(indent=4)

p = pns.Parser(open('168.html', 'r').read()).fetch()
s = pns.Selector(p)

pp.pprint(s.find('.meta-achievements .linked'))

pp.pprint(s.walk(0))