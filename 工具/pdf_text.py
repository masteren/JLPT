#!/usr/bin/env python3
"""把文字版 PDF 抽成纯文本（按页分段），只用标准库，无需 poppler。

用法:  python3 工具/pdf_text.py <file.pdf> > out.txt

扫描件（图片 PDF）抽不出东西 —— 那种用 工具/render_pdf.js 渲染成 PNG 再看。
"""
import re,zlib,sys

path=sys.argv[1]
data=open(path,'rb').read()

# --- parse indirect objects ---
objs={}
for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj\b',data):
    num=int(m.group(1))
    start=m.end()
    end=data.find(b'endobj',start)
    objs[num]=data[start:end if end>0 else start+100000]

def getstream(body):
    m=re.search(rb'stream\r?\n',body)
    if not m: return None
    s=m.end(); e=body.find(b'endstream',s)
    raw=body[s:e]
    if b'FlateDecode' in body[:m.start()]:
        try: return zlib.decompress(raw)
        except Exception:
            try: return zlib.decompressobj().decompress(raw)
            except Exception: return None
    return raw

# expand object streams (ObjStm)
for num,body in list(objs.items()):
    if b'/ObjStm' in body[:400]:
        d=getstream(body)
        if not d: continue
        n=int(re.search(rb'/N\s+(\d+)',body).group(1))
        first=int(re.search(rb'/First\s+(\d+)',body).group(1))
        hdr=d[:first].split()
        for i in range(n):
            onum=int(hdr[2*i]); off=int(hdr[2*i+1])
            nxt=int(hdr[2*i+3])+first if i+1<n else len(d)
            objs.setdefault(onum,d[first+off:nxt])

# --- ToUnicode cmaps per font object ---
def parse_cmap(d):
    mp={}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar',d,re.S):
        for a,b in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',blk):
            src=int(a,16)
            tgt=bytes.fromhex(b.decode()).decode('utf-16-be','replace')
            mp[src]=tgt
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange',d,re.S):
        for a,b,c in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',blk):
            lo,hi,st=int(a,16),int(b,16),int(c,16)
            for i in range(hi-lo+1):
                mp[lo+i]=chr(st+i)
    return mp

fontmaps={}   # font obj num -> cmap
for num,body in objs.items():
    m=re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R',body)
    if m and (b'/Font' in body or b'/BaseFont' in body):
        tu=int(m.group(1))
        d=getstream(objs.get(tu,b''))
        if d: fontmaps[num]=parse_cmap(d)


# --- pages ---
pages=[]
for num,body in objs.items():
    if re.search(rb'/Type\s*/Page(?![s])',body):
        pages.append((num,body))

def resolve_fonts(body):
    """map /Fx name -> cmap"""
    res={}
    m=re.search(rb'/Resources\s+(\d+)\s+\d+\s+R',body)
    if m:
        rbody=objs.get(int(m.group(1)),b'')
    else:
        m=re.search(rb'/Resources\s*<<',body)
        rbody=body[m.start():] if m else b''
    fm=re.search(rb'/Font\s+(\d+)\s+\d+\s+R',rbody)
    if fm:
        fbody=objs.get(int(fm.group(1)),b'')
    else:
        fm=re.search(rb'/Font\s*<<(.*?)>>',rbody,re.S)
        fbody=fm.group(1) if fm else b''
    for name,onum in re.findall(rb'/(\w+)\s+(\d+)\s+\d+\s+R',fbody):
        o=int(onum)
        if o in fontmaps: res[name.decode()]=fontmaps[o]
    return res

def unescape(s):
    out=bytearray(); i=0
    while i<len(s):
        c=s[i]
        if c==0x5c and i+1<len(s):
            nx=s[i+1]
            mapping={ord('n'):10,ord('r'):13,ord('t'):9,ord('b'):8,ord('f'):12,ord('('):40,ord(')'):41,ord('\\'):92}
            if nx in mapping: out.append(mapping[nx]); i+=2; continue
            if 0x30<=nx<=0x37:
                oct_=s[i+1:i+4]
                k=0
                while k<3 and i+1+k<len(s) and 0x30<=s[i+1+k]<=0x37: k+=1
                out.append(int(s[i+1:i+1+k],8)&0xff); i+=1+k; continue
            i+=2; continue
        out.append(c); i+=1
    return bytes(out)

def decode(raw, cmap, hexstr):
    if hexstr:
        h=re.sub(rb'[^0-9A-Fa-f]',b'',raw)
        if len(h)%2: h+=b'0'
        b=bytes.fromhex(h.decode())
    else:
        b=unescape(raw)
    if cmap is None:
        return b.decode('latin-1')
    out=[]
    for i in range(0,len(b)-1,2):
        code=(b[i]<<8)|b[i+1]
        out.append(cmap.get(code,''))
    return ''.join(out)

tok=re.compile(rb'/(\w+)\s+[\d.]+\s+Tf|\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|(TD|Td|T\*|ET|Tj|TJ)',re.S)

for pnum,(onum,body) in enumerate(pages,1):
    fonts=resolve_fonts(body)
    cm=re.search(rb'/Contents\s+(\d+)\s+\d+\s+R',body)
    content=b''
    if cm:
        content=getstream(objs.get(int(cm.group(1)),b'')) or b''
    else:
        am=re.search(rb'/Contents\s*\[(.*?)\]',body,re.S)
        if am:
            for o in re.findall(rb'(\d+)\s+\d+\s+R',am.group(1)):
                content+=(getstream(objs.get(int(o),b'')) or b'')
    cur=None
    buf=[]
    for m in tok.finditer(content):
        t=m.group(0)
        if m.group(1):
            cur=fonts.get(m.group(1).decode()); continue
        if m.group(2):
            if t in (b'TD',b'Td',b'T*',b'ET'): buf.append('\n')
            continue
        buf.append(decode(t[1:-1],cur,t[0:1]==b'<'))
    txt=re.sub(r'\n{2,}','\n',''.join(buf))
    print('\n########## PAGE %d ##########' % pnum)
    print(txt)
