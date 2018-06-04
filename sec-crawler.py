import requests
cik="0000320193"
priorto="20010101"
count=10
base_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+str(cik)+"&type=10-K&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)

r = requests.get(base_url)
data = r.text
print(data)

