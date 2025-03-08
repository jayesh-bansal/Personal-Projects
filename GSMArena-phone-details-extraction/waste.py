import requests
import time
import random
headers = {
     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
     'Accept-Language': 'en-US,en;q=0.9',
     'Accept-Encoding': 'gzip, deflate, br',
     'Connection': 'keep-alive'
}
f=open('part 2.txt','r')
j=0
url=[]
for i in f:
    while j!=len(i):
        if i[j:j+4]=='href':
            j+=6
            s=''
            while i[j]!='"':
                s+=i[j]
                j+=1
            url.append(s)
        j+=1
        
print(url)
for i in range(15,50):
    res = requests.get(url[i], headers=headers)
    f=res.text
    time.sleep(random.uniform(1,10))
    f=f.split('>')
    for i in range(len(f)):
        try:
            if 'modelname' in f[i]:
                print(f[i+1][:-4],end='@')
            if 'link-network-detail' in f[i]:
                print(f[i+1][:-3],end='@')
            if '"status"' in f[i]:
                print(f[i+1][:-4],end='@')
            if 'dimensions' in f[i]:
                print(f[i+1][:-4])
                break
        except:
            pass
