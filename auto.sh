#!/bin/bash

PIDS=$(ps -ef | grep bbc.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/bbc.py
fi

PIDS=$(ps -ef | grep au_abc.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/au_abc.py
fi

PIDS=$(ps -ef | grep us_newsweek.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/us_newsweek.py
fi

PIDS=$(ps -ef | grep us_nytimes.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/us_nytimes.py
fi

PIDS=$(ps -ef | grep cbsnews.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/cbsnews.py
fi
PIDS=$(ps -ef | grep rnz.py | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/rnz.py
fi

PIDS=$(ps -ef | grep aljazeera.py  | grep -v grep | awk '{print $2}')
if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/aljazeera.py
fi
