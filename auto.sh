#!/bin/bash

PIDS=$(ps -ef | grep python3.9 | grep -v grep | awk '{print $2}')

if [ "$PIDS" = "" ]; then
	/usr/bin/python3.9 /root/limitoo/news_py/bbc.py
	/usr/bin/python3.9 /root/limitoo/news_py/au_abc.py
	/usr/bin/python3.9 /root/limitoo/news_py/us_newsweek.py
	/usr/bin/python3.9 /root/limitoo/news_py/us_nytimes.py
	/usr/bin/python3.9 /root/limitoo/news_py/cbsnews.py
	/usr/bin/python3.9 /root/limitoo/news_py/rnz.py
	/usr/bin/python3.9 /root/limitoo/news_py/aljazeera.py
else
        echo "Spider Build is runing."
        echo $PIDS
fi


