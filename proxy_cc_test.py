import urllib2
import re
import threading
import random
import time
import requests
lock = threading.Lock()

headers = {"User-agent":"Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36"}
proxy_filter_queue = []
thread_test_list = []

def download_proxy():
    print "download proxy from http://www.xicidaili.com"
    for urls in ["http://www.xicidaili.com/nn/", "http://www.xicidaili.com/nt/"]:
        for page in range(1, 50):
            url = urls + str(page)
            print url
            user_agent = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
            request = urllib2.Request(url)
            request.add_header("User-Agent", user_agent)
            content = urllib2.urlopen(request)
            results = re.findall(r'[0-9]+(?:\.[0-9]+){0,3}</td>\s+<td>\d*</td>', content.read())
            for result in results:
                ip_info = re.findall(r'[0-9]+(?:\.[0-9]+){0,3}', result)
                port_info = re.findall(r'<td>\d+</td>', result)
                if not ip_info or not port_info:
                    continue
                ip = ip_info[0]
                port = port_info[0][4:-5]
                proxy_thread(target=filter_proxy_timeout, args=(ip, port))
    wait_all_proxy_thread()
    with open('proxy.txt', 'w') as f:
        for info in proxy_filter_queue:
            f.write('%s %s\n'%(info['ip'], info['port']))

def load_proxy_file():
    try:
        proxy_list = []
        with open('proxy.txt', 'r') as f:
            for line in f.readlines():
                content = line.split()
                ip, port= content[0], content[1]
                proxy_list.append([ip.strip(), port.strip()])
        return proxy_list
    except Exception as e:
        print "load_proxy_file error:", e

def filter_proxy_timeout(ip, port):
    try:
        r = requests.get('http://baidu.com', timeout=1, headers=headers, proxies={"http":"http://%s:%s"%(ip, port)})
        if len(r.text) > 10000:
            proxy_filter_queue.append({'ip':ip, 'port':port})
    except requests.exceptions.Timeout:
        pass
    except Exception:
        pass
    else:
        print "get"

def proxy_thread(target, args=None, kwargs=None):
    t = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread_test_list.append(t)
    t.start()

def wait_all_proxy_thread():
    for t in thread_test_list:
        t.join()
    else:
        print "all threads done"
    del thread_test_list[:]

def test_url_run(reset_file=False, thread_count=10, sleep_time=1, request_times=10):
    try:
        if reset_file:
            download_proxy()
        proxy_list = load_proxy_file()
        thread_list = []
        for i in range(thread_count):
            proxy = random.choice(proxy_list)
            proxy_thread(target=run, args=proxy, kwargs={"sleep_time":sleep_time, "request_times":request_times})
        wait_all_proxy_thread()
    except Exception as e:
        print "test_url error:", e

def run(ip=None, port=None, url='http://127.0.0.1', sleep_time=1, request_times=10):
    url = "http://www.baidu.com"
    #url = "http://192.168.0.1:3000"
    try:
        proxy = {"http": "http://%s:%s"%(ip, port)}
        n = 0
        while True:
            n += 1
            response = requests.get(url=url, headers=headers, proxies=proxy)
            if len(response.text) > 10000:
                lock.acquire()
                print ip, port, 1, 'get'#, response.text
                lock.release()
                time.sleep(sleep_time)
            if n > request_times:
                break
    except Exception as e:
        lock.acquire()
        print ip, port, "run error:", e
        lock.release()

def test_run(ip=None, port=None):
    url = "http://www.baidu.com"
    if not ip:
        ip, port =" 127.0.0.1", "8087"
    proxy = {"http":"http://%s:%s"%(ip, port)}
    print proxy
    proxy_support = urllib2.ProxyHandler(proxy)
    opener = urllib2.build_opener(proxy_support)
    urllib2.install_opener(opener)
    user_agent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36"
    headers={'User-agent' : 'Mozilla/5.0'}
    request = urllib2.Request(url, None, headers)
    try:
        n = 0
        while True:
            content = urllib2.urlopen(request)
            time.sleep(0.1)
            n += 1
            if content.read():
                lock.acquire()
                print content.read()
                print ip, port, 1
                lock.release()
            if n > 10:break
    except Exception as e:
        lock.acquire()
        print ip, port, e, '\n'
        lock.release()


if __name__ == '__main__':
    test_url_run(reset_file=False)
    # test_run("127.0.0.1", "8087")
