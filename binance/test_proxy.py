import requests
import time

proxy_user = "larqmyeoovdkuqy187592-zone-lightning-region-in"
proxy_pass = "ainovlwbom"
proxy_host = "res-as.lightningproxies.net"
proxy_port = "9999"

proxies = {
    "http": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}",
    "https": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}",
}

for i in range(5):
    try:
        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=20)
        print(f"Attempt {i+1}: {r.json()}")
    except Exception as e:
        print(f"Attempt {i+1} failed: {e}")
    time.sleep(2)
