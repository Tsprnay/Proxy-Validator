import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor

import requests
import socks

URL = "http://httpbin.org/ip"
TIMEOUT = (15, 27)

def download_proxy_list(url):
    try:
        current_proxy = socks.get_default_proxy()
        socks.set_default_proxy()
        session = requests.Session()
        response = session.get(url)
        response.raise_for_status()
        socks.set_default_proxy(*current_proxy)
        return response.text.strip().split('\n')
    except (requests.exceptions.RequestException, socket.timeout) as e:
        print("Error while downloading list:", e)
        socks.set_default_proxy(*current_proxy)
        return []

def is_valid_proxy_format(proxy):
    return re.match(r'^\d{1,3}(\.\d{1,3}){3}:\d+$', proxy) is not None

def set_socks_proxy(proxy, proxy_type):
    ip, port = proxy.split(':')
    port = int(port)
    socks.set_default_proxy(proxy_type, ip, port)
    socket.socket = socks.socksocket

def check_proxy(proxy_data):
    proxy, proxy_type = proxy_data
    if not is_valid_proxy_format(proxy):
        return proxy, False

    try:
        session = requests.Session()
        session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
        if proxy_type in [socks.SOCKS4, socks.SOCKS5]:
            set_socks_proxy(proxy, proxy_type)
        else:
            session.proxies = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}
        response = session.get(URL, timeout=TIMEOUT)
        real_ip = response.json()["origin"]
        proxy_ip = proxy.split(':')[0]
        if real_ip == proxy_ip:
            print(f"Valid proxy: {proxy}")
            return proxy, True
        return proxy, False
    except (requests.exceptions.RequestException, socket.timeout):
        return proxy, False

proxy_urls = {
    "http": "https://github.com/Tsprnay/Proxy-lists/raw/master/proxies/http.txt",
    "https": "https://github.com/Tsprnay/Proxy-lists/raw/master/proxies/https.txt",
    "socks4": "https://github.com/Tsprnay/Proxy-lists/raw/master/proxies/socks4.txt",
    "socks5": "https://github.com/Tsprnay/Proxy-lists/raw/master/proxies/socks5.txt"
}

proxy_types = {
    "http": None,
    "https": None,
    "socks4": socks.SOCKS4,
    "socks5": socks.SOCKS5
}

proxies_folder = 'proxies'
if not os.path.exists(proxies_folder):
    os.makedirs(proxies_folder)

for proxy_type, url in proxy_urls.items():
    proxies = download_proxy_list(url)
    with ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(check_proxy, [(proxy, proxy_types[proxy_type]) for proxy in proxies])
        valid_proxies = [proxy for proxy, valid in results if valid]
        with open(f"{proxies_folder}/valid_{proxy_type}_proxies.txt", "w") as file:
            for proxy in valid_proxies:
                file.write(proxy + "\n")
