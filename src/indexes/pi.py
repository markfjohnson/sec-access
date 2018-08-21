import urllib3
http = urllib3.PoolManager()
resp = http.request("GET", "http://www.yahoo.com")
print(resp)