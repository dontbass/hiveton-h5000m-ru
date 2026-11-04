import json,re,sys,hashlib,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from netdata_runs import RUN,CJK
ND=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"translations","netdata")
W=sys.argv[1]; UP=sys.argv[2]; OUT=sys.argv[3]
os.makedirs(OUT,exist_ok=True)
md5=lambda b: hashlib.md5(b).hexdigest()
def ops_from(src, reps):
    reps=sorted(reps); ops=[]; out=[]; last=0; boff=0
    for s,e,n in reps:
        pre=src[last:s]; boff+=len(pre.encode()); old=src[s:e]
        ops.append([boff,len(old.encode()),n,old]); boff+=len(old.encode())
        out.append(pre); out.append(n); last=e
    out.append(src[last:]); return ops,''.join(out)
def keepws(orig,tr):
    lead=re.match(r'^\s*',orig).group(); trail=re.search(r'\s*$',orig).group()
    if not tr.startswith(lead): tr=lead+tr.lstrip()
    if trail and not tr.endswith(trail): tr=tr.rstrip()+trail
    return tr
def write(target_rel, src_text, new_text, ops, name):
    ob=src_text.encode(); nb=new_text.encode()
    json.dump({'target':'/usr/share/netdata/web/'+target_rel,'orig_md5':md5(ob),'orig_size':len(ob),'new_md5':md5(nb),'ops':ops},
              open(f'{OUT}/{name}.json','w'),ensure_ascii=False)
    open(f'/tmp/nd_out_{name}','wb').write(nb)
    print(name,'ops',len(ops))
# UI runs dict
runs=json.load(open(ND+'/ui_runs.json')); tr={}
for l in open(ND+'/ui_ru.txt',encoding='utf-8'):
    l=l.rstrip('\n')
    if not l: continue
    i,t=l.split('\t',1); tr[runs[int(i)]]=t
assert len(tr)==len(runs),(len(tr),len(runs))
D={k:keepws(k,v) for k,v in tr.items()}
PUNCT={'。':'. ','，':', ','：':': ','；':'; ','！':'! ','？':'? ','（':' (','）':') ','、':', '}
PUNCT_RE=re.compile('|'.join(map(re.escape,PUNCT)))
PER_FILE={'main.chunk.js':{'秒':'с'}}
# short option names: toggle buttons (data-on/data-off) and <b>…</b> references in the options dialog
SHORT={'选中':'Фокус','始终':'Всегда','非零':'Ненулевые','全部':'Все','销毁':'Удалять','隐藏':'Скрывать',
 '异步':'Асинхр.','同步':'Синхр.','并行':'Параллельно','顺序':'По очереди','重新同步':'Синхр.','尽力而为':'Как выйдет',
 '不同步':'Нет','右侧':'Справа','下方':'Снизу','深色':'Тёмная','浅色':'Светлая','需要帮助':'Да','不需要':'Нет',
 '填充':'Дополнять','不填充':'Нет','平滑':'Плавно','粗糙':'Ломаной','自动缩放':'Авто','固定单位':'Исходные',
 '摄氏度':'Цельсий','华氏度':'Фаренгейт','时间':'Время','秒':'Секунды'}
for f,name in [('index.html','index.html'),('static/js/main.7d1bdca1.chunk.js','main.chunk.js'),('static/js/2.92ca8446.chunk.js','2.chunk.js')]:
    s=open(f'{W}/{f}',encoding='utf-8',newline='').read(); reps=[]
    OV=PER_FILE.get(name,{})
    for m in RUN.finditer(s):
        t=m.group()
        if t.strip().startswith('//'): continue
        if not CJK.search(t):
            if PUNCT_RE.search(t): reps.append((m.start(),m.end(),PUNCT_RE.sub(lambda x: PUNCT[x.group()],t)))
            continue
        pre=s[max(0,m.start()-10):m.start()]
        is_opt = name=='index.html' and t in SHORT and (re.search(r'data-(on|off)="$',pre) or (pre.endswith('<b>') and s[m.end():m.end()+4]=='</b>'))
        if is_opt: v=SHORT[t]
        elif t in OV: v=OV[t]
        elif t in D: v=D[t]
        else: print('MISSING',f,repr(t)); continue
        if name=='index.html':
            # HTML text nodes: Chinese needs no spaces around inline tags, Russian does
            if m.start()>0 and s[m.start()-1]=='>' and v[:1].isalnum(): v=' '+v
            if m.end()<len(s) and s[m.end()]=='<' and v[-1:].isalnum():
                nx=re.match(r'(?:<[^>]*>\s*)+([^<]+)', s[m.end():m.end()+600])
                if nx:
                    nt=nx.group(1); r2=RUN.match(nt)
                    nt=D.get(r2.group(), nt) if r2 and r2.group() else nt
                    if nt.lstrip()[:1].isalnum(): v=v+' '
        reps.append((m.start(),m.end(),v))
    ops,new=ops_from(s,reps); write(f,s,new,ops,name)
# dashboard-react.js map values by English key
mp=json.load(open(ND+'/map.json')); mru=[l.rstrip('\n') for l in open(ND+'/map_ru.txt',encoding='utf-8')]
K={}
for (en,zh),ru in zip(mp,mru): K[en]=ru
s=open(f'{W}/dashboard-react.js',encoding='utf-8',newline='').read(); reps=[]
for m in re.finditer(r"^(\s*'((?:[^'\\]|\\.)*)'\s*:\s*')((?:[^'\\]|\\.)*)'",s,re.M):
    en,zh=m.group(2),m.group(3)
    if CJK.search(zh) and en in K:
        ru=K[en].replace("\\","\\\\").replace("'","\\'")
        reps.append((m.start(3),m.end(3),ru))
ops,new=ops_from(s,reps); write('dashboard-react.js',s,new,ops,'dashboard-react.js')
# dashboard_info.js: upstream English + russian menu titles + extra submenu entries
up=open(f'{UP}/dashboard_info.js',encoding='utf-8',newline='').read()
menu=dict(l.rstrip('\n').split('\t') for l in open(ND+'/menu_ru.tsv',encoding='utf-8') if l.strip())
def tsub(m):
    t=m.group(2); return m.group(1)+menu.get(t,t).replace("'","\\'")+"'"
up2=re.sub(r"(title: *')([^']*)'",tsub,up)
extra=json.load(open(ND+'/extra_submenu.json')); sru=[l.rstrip('\n') for l in open(ND+'/submenu_ru.txt',encoding='utf-8')]
assert len(extra)==len(sru)
ins=''.join("\n    '%s': {\n        title: '%s'\n    },\n" % (k,r.replace("'","\\'")) for (k,_),r in zip(extra,sru))
anchor='netdataDashboard.submenu = {'
assert up2.count(anchor)==1
up2=up2.replace(anchor,anchor+ins,1)
sf=open(f'{W}/dashboard_info.js',encoding='utf-8',newline='').read()
open(f'{OUT}/dashboard_info.new.bin','wb').write(up2.encode()); open(f'{OUT}/dashboard_info.old.bin','wb').write(sf.encode())
json.dump({'target':'/usr/share/netdata/web/dashboard_info.js','orig_md5':md5(sf.encode()),'orig_size':len(sf.encode()),'new_md5':md5(up2.encode()),
  'ops':[[0,len(sf.encode()),{'file':'dashboard_info.new.bin'},{'file':'dashboard_info.old.bin'}]]},open(f'{OUT}/dashboard_info.js.json','w'))
open('/tmp/nd_out_dashboard_info.js','wb').write(up2.encode())
# dashboard.html: upstream English
uh=open(f'{UP}/dashboard/dashboard.html','rb').read(); sh=open(f'{W}/dashboard.html','rb').read()
open(f'{OUT}/dashboard.new.bin','wb').write(uh); open(f'{OUT}/dashboard.old.bin','wb').write(sh)
json.dump({'target':'/usr/share/netdata/web/dashboard.html','orig_md5':md5(sh),'orig_size':len(sh),'new_md5':md5(uh),
  'ops':[[0,len(sh),{'file':'dashboard.new.bin'},{'file':'dashboard.old.bin'}]]},open(f'{OUT}/dashboard.html.json','w'))
print('done')
