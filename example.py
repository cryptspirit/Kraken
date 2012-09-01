#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  example.py
#  
#  Copyright 2012  <mort@Sanctum>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
import kraken

def example1():
    '''
    Самый простой пример
    '''
    bots = kraken.BotPool()
    settings = kraken.Settings()
    bots.append(kraken.Bot(settings))
    re = bots('http://test.com')
    return re

def example2():
    '''
    Обработка нескольких ссылок. Ипользование cookis и логирования
    '''
    urls = ['http://test.com', 'http://test.org', 'http://test.ru']
    bots = kraken.BotPool()
    settings = kraken.Settings()
    settings.set_logger('kraken.log')
    settings.use_cookie = True
    bots.append(kraken.Bot(settings))
    re = bots(urls)
    return re

def example3():
    '''
    Использование нескольких ботов с разными настройками
    '''
    bots = kraken.BotPool()
    for i in xrange(10):
        settings = kraken.Settings()
        settings.useragent_data.append('kraken %s' % i)
        bots.append(kraken.Bot(settings))
    re = bots('http://test.com')
    return re

def main():
    print example3()
    return 0

if __name__ == '__main__':
    main()

