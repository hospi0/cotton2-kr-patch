import sys,glob,struct; sys.path.insert(0,'tools')
from mf import spt_items
import vsscan
sys.stdout.reconfigure(encoding='utf-8')
b=open(glob.glob('work/disc/**/CHR_VS1.MF',recursive=True)[0],'rb').read()
e,offs,ents=vsscan.sch_table(b)
d,sz=e['SPT']; s=b[d:d+sz]; items,_=spt_items(s)
pos2item={p:k for k,p,*_ in items}
G="ちぇっ!こい つがボウィロー を持てると思たのになあ…ま 、か。それより早く見け宿力使えはクッアプ リ何企んでみだわさょ待‼や道付あ出すゃは ?う丸ヨニしゔ食べ〜コトンも行"
G=G.replace(' ','')
lab={0:'<A>',1:'<CL>',2:'<C>',3:'<ED>',15:'<M>',16:'<N>',18:'<P>',19:'<○>',20:'<S>',32:'<W>',17:'<n>',26:'<s>',33:'<z>'}
for i in range(4,9): lab[i]='<d%d>'%(i-4)
for i,v in zip(range(9,15),'nAIUEO'): lab[i]=v.lower() if v!='n' else '_'
for i in range(21,26): lab[i]='<e%d>'%(i-21)
for i in range(27,32): lab[i]='<w%d>'%(i-27)
for k in range(34,34+len(G)): lab[k]=G[k-34]
out=[]
for i,en in enumerate(ents):
    if len(en)<4: break
    it=pos2item.get(struct.unpack_from('>I',en,0)[0],-1)
    extra=struct.unpack_from('>H',en,12)[0]
    t=lab.get(it,'[%d]'%it)
    if extra: t+='{%X}'%extra
    out.append(t)
print(''.join('\n%d:'%i+t if t=='<ED>' else t for i,t in enumerate(out)))
