import re,sys,json
RUN=re.compile(r'[^"\'`<>\r\n\\]*[一-鿿　-〿＀-￯][^"\'`<>\r\n\\]*')
CJK=re.compile(r'[一-鿿]')
def runs(s): return [m for m in RUN.finditer(s) if CJK.search(m.group())]
if __name__=='__main__':
    W=sys.argv[1]; out={}
    for f in sys.argv[2:]:
        s=open(W+'/'+f,encoding='utf-8').read()
        for m in runs(s):
            t=m.group(); out.setdefault(t,[]).append(f)
    L=sorted(out, key=lambda k:(min(out[k]),k))
    json.dump(L,open('runs.json','w'),ensure_ascii=False,indent=0)
    for i,k in enumerate(L): print(i,'|',k.strip()[:110],'|',','.join(sorted(set(x.split('/')[-1][:8] for x in out[k]))))
