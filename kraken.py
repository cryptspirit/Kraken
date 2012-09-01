#!/usr/bin/python2
# -*- coding: utf-8 -*-


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
import httplib
import urllib
import logging
import errno
import copy
import time

import thread

class Settings():
    '''
    класс настроек бота
    '''
    def __init__(self, proxy=None):
        
        self.use_cookie = False
        self.use_headers = False
        self.use_random_useragent = False
        self.useragent_data = []
        self.__current_useragent__ = 0
        self.proxy = None
        self.logger = None
        
        if isinstance(proxy, ProxyPool) or not proxy:
            self.proxy = proxy
        else:
            raise TypeError('proxy is not of type %s' %ProxyPool)
    
    def get_useragent(self):
        '''
        Возвращает строку User-Agent для заголовка запроса
        '''
        if self.useragent_data:
            r = self.useragent_data[self.__current_useragent__]
            if self.__current_useragent__ + 1 > len(self.useragent_data) - 1:
                self.__current_useragent__ = 0
            else:
                self.__current_useragent__ += 1
            return r
        else:
            return ''
    
    def set_logger(self, logfile, logger_name='Kraken'):
        '''
        Установка логера
        '''
        self.logger = logging.getLogger(logger_name)
        fh = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(levelname)s %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.setLevel(logging.DEBUG)
    
    def log_info(self, messeges):
        '''
        Запись в лог сообщение
        '''
        if self.logger: self.logger.info(messeges)
    
    def log_error(self, messeges):
        '''
        Запись в лог ошибки
        '''
        if self.logger: self.logger.error(messeges)
    
    def log_warn(self, messeges):
        '''
        Запись в лог предупреждения
        '''
        if self.logger: self.logger.warn(messeges)
    
class Bot():
    '''
    Класс настройки бота. Настройка браузера
    '''
    busy = False
    def __init__(self, setting):
        
        self.headers = {'Referer': ''}
        self.logger = None
        self.kraken_response = None
        self.cookies = {}
        if isinstance(setting, Settings):
            self.setting = setting
        else:
            raise TypeError('setting is not of type %s' % Settings)
    
    def __convert_raw_cookie__(self, raw_cookie):
        '''
        Преобразование сырой строки cookie в словарь
        '''
        #print raw_cookie
        index = raw_cookie.find(';') + 1
        cookie_data = raw_cookie[:index]
        cookie_path = raw_cookie[index:]
        index = cookie_data.rfind('=')
        cookie_name = cookie_data[:index]
        cookie_data = cookie_data[index + 1: -1]
        index = cookie_path.rfind('=') + 1
        cookie_path = cookie_path[index:]
        return cookie_name, cookie_data, cookie_path
        
    def set_referer(self, referer):
        '''
        Установка реферала
        '''
        self.headers['Referer'] = referer
        
    def __request__(self, url, post=False):
        '''
        Основная функция запроса
        '''
        if post:
            method = 'POST'
        else:
            method = 'GET'
        
        urlsplit = httplib.urlsplit(url)
        if not urlsplit.netloc and not urlsplit.scheme:
            url = 'http://%s' % url
            urlsplit = httplib.urlsplit(url)
        
        params = urlsplit.query
        headers = self.get_headers(url)
        if self.setting.proxy:
            server_address = self.setting.proxy.get_proxy()
        else:
            server_address = urlsplit.netloc
            
        connect = httplib.HTTPConnection(server_address)
        time_begin_request = time.time()
        try:
            connect.request(method, url, params, headers)
        except:
            self.setting.log_error('%s %s' % (url, 'connection error'))
            status = 404
            data = None
            time_request = time.time() - time_begin_request
        else:
            response = connect.getresponse()
            time_request = time.time() - time_begin_request
            status = response.status
            self.setting.log_info('%s %s' % (url, response.status))
            if response.status == 302:
                self.setting.log_warn('%s %s %s' % (url, response.status, response.getheader('location')))
                data = self.get_method(location, None)
            else:
                data = response.read()
                cookie = response.getheader('Set-Cookie')
        
                if self.setting.use_cookie:
                    if cookie:
                        cookie_name, cookie_data, cookie_path = self.__convert_raw_cookie__(cookie)
                        self.add_cookie(cookie_name, cookie_data, cookie_path)
        
        resolve_answer = (status, url, time_request, data)
        if self.kraken_response: self.kraken_response(resolve_answer)
        self.busy = False
        return resolve_answer
    
    def __call__(self, url):
        '''
        Запуск бота
        '''
        self.busy = True
        thread.start_new_thread(self.__request__, (url, ) )

    def get_cookie_string(self):
        '''
        Создание поля cookie для заголовка
        '''
        cookie_string = ''
        for i in self.cookies.keys():
            cookie_string += '%s=%s; ' % (i, self.cookies[i]['Data'])
        return cookie_string

    def add_cookie(self, cookie_name, cookie_data, cookie_path):
        '''
        Добавление cookie
        '''
        self.cookies[cookie_name] = {'Data' : cookie_data, 'Path' : cookie_path}

    def get_headers(self, url):
        '''
        Получение заголовка запроса
        '''
        self.headers['User-Agent'] = self.setting.get_useragent()
        if self.setting.use_cookie:
            self.headers['Cookie'] = self.get_cookie_string()
        else:
            self.headers['Cookie'] = ''
        return self.headers


class ProxyPool(list):
    '''
    Список прокси серверов
    '''
    def __init__(self):
        self.__current_proxy = 0
        list.__init__(self)
        
    def __get_roundrobin_proxy__(self):
        '''
        Выбор прокси по принципу Round Robin
        '''
        if self:
            if self.__current_proxy + 1 > len(self) - 1:
                self.__current_proxy = 0
            else:
                self.__current_proxy += 1
            return self[self.__current_proxy]
        else:
            return None
    
    def get_proxy(self):
        '''
        Получение адреса прокси сервера
        '''
        return self.__get_roundrobin_proxy__()

class BotPool(list):
    '''
    Список ботов
    '''
    use_busy = True
    def __init__(self):
        list.__init__(self)
        
    def __setitem__(self, index, bot):
        '''
        Замена бота
        '''
        if not isinstance(bot, Bot):
            raise TypeError, 'bot is not of type %s' % Bot
        bot.kraken_response = self.response
        list.__setitem__(self, index, bot)

    def append(self, bot):
        '''
        Добавление бота
        '''
        if not isinstance(bot, Bot):
            raise TypeError, 'bot is not of type %s' % Bot
        bot.kraken_response = self.response
        list.append(self, bot)

    def add_list_bots(self, n, bot):
        '''
        Добавление нескольких ботов по образцу
        '''
        if n < 1:
            raise TypeError, 'The number can not be less than one'
        if isinstance(bot, Bot):
            for i in xrange(n): self.append(copy.copy(bot))
        else:
            raise TypeError, 'bot is not of type %s' % Bot
    
    def response(self, responses):
        '''
        Callback для ответа
        '''
        self.response_list.append(responses)
        
    def __call__(self, url, post=False):
        '''
        Запрос
        '''
        if not isinstance(url, str) and not isinstance(url, list):
            raise TypeError, 'url is not of type %s or type %s' % (str, list)
        self.response_list = []
        if type(url) == list:
            index_my_bot = 0
            index_url = 0
            while index_url < len(url):
                if not self[index_my_bot].busy and self.use_busy:
                    if index_url: self[index_my_bot].set_referer(url[index_url - 1])
                    a = self[index_my_bot](url[index_url])
                    index_url += 1
                if index_my_bot == (len(self) - 1):
                    index_my_bot = 0
                else:
                    index_my_bot += 1
            while len(self.response_list) < len(url):
                time.sleep(1)
        else:
            for i in self: i(url)
            while len(self.response_list) < len(self):
                time.sleep(1)
        return self.response_list

