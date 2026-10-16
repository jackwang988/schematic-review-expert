#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rf_dense_pairing.py —— 密集标签区"位号↔数值"稳健配对工具
解决问题: 当多个 R/L/C 器件靠得很近、数值标签夹在中间时,
          纯"最近距离"配对会张冠李戴(甚至两个位号抢同一个值)。
方法    : ①符号类型门控(单位必须匹配符号: pF/nF/uF->C, nH/uH->L, R/k/Ω->R)
          ②通过门控后做"一对一贪心配对（非全局最优）"(贪心去重, 撞车按总距离最小裁决)
          ③输出置信度: 唯一候选=高; 多候选被裁决=中(需高清复核)
用法    : python rf_dense_pairing.py <pdf> <page_index> [x0 y0 x1 y1]
"""
import sys, re, fitz

# 单位 -> 器件类型
UNIT2TYPE = [
    (re.compile(r'(?i)\d\s*(pF|nF|uF|µF)$'), 'C'),
    (re.compile(r'(?i)\d\s*(nH|uH|µH|mH|pH)$'), 'L'),
    (re.compile(r'(?i)\d\s*(R|k|K|Ω|Ohm|R-1%)$|^\dR$|^0R$'), 'R'),
]
REF2TYPE = {'C':'C','L':'L','R':'R'}  # 位号首字母 -> 类型

def val_type(tok):
    for rx,ty in UNIT2TYPE:
        if rx.search(tok): return ty
    return None

def ref_type(ref):
    m=re.match(r'^([A-Za-z]+)\d', ref)
    if not m: return None
    p=m.group(1).upper()
    if p in ('C','CC','CP'): return 'C'
    if p in ('L','LP','LX','FB'): return 'L'
    if p in ('R','RP'): return 'R'
    return None

def pair(pdf, pidx, clip=None):
    doc=fitz.open(pdf); page=doc[pidx]; wrds=page.get_text("words")
    def center(w): return ((w[0]+w[2])/2,(w[1]+w[3])/2)
    def inclip(cx,cy):
        return clip is None or (clip[0]<=cx<=clip[2] and clip[1]<=cy<=clip[3])
    refs=[]; vals=[]
    for w in wrds:
        t=w[4].strip(); cx,cy=center(w)
        if not inclip(cx,cy): continue
        rt=ref_type(t)
        if rt and re.match(r'^[A-Za-z]+\d+$', t):
            refs.append({'ref':t,'type':rt,'x':cx,'y':cy})
        vt=val_type(t)
        if vt:
            vals.append({'val':t,'type':vt,'x':cx,'y':cy})
    # 候选边: 仅"类型匹配"的 ref-val 对
    edges=[]
    for r in refs:
        for vi, v in enumerate(vals):
            if r['type']==v['type']:
                d=((r['x']-v['x'])**2+(r['y']-v['y'])**2)**0.5
                edges.append((d,r['ref'],vi))
    edges.sort()
    # 一对一贪心分配(全局最小距离优先, 去重)
    used_r=set(); used_v=set(); assign={}
    for d,rf,vi in edges:
        if rf in used_r or vi in used_v: continue
        assign[rf]=(vals[vi]['val'],round(d,1)); used_r.add(rf); used_v.add(vi)
    # 置信度: 该 ref 在同类型候选里若只有1个值->高, 否则中
    conf={}
    for r in refs:
        cands=[v for v in vals if v['type']==r['type']]
        conf[r['ref']]='高' if len(cands)==1 else '中(需高清复核)'
    return refs, vals, assign, conf

if __name__=='__main__':
    pdf=sys.argv[1]; pidx=int(sys.argv[2])
    clip=tuple(map(float,sys.argv[3:7])) if len(sys.argv)>=7 else None
    refs,vals,assign,conf=pair(pdf,pidx,clip)
    print("位号:",[r['ref'] for r in refs])
    print("数值:",[v['val'] for v in vals])
    print("\n配对结果(符号类型门控 + 一对一贪心配对（非全局最优）):")
    for r in refs:
        a=assign.get(r['ref'])
        print(f"  {r['ref']:5s}[{r['type']}] -> {a[0] if a else '(无同类型值)':8s}  d={a[1] if a else '-'}  置信:{conf[r['ref']]}")
    # 未分配的值
    from collections import Counter
    remaining = Counter(v["val"] for v in vals)
    remaining.subtract(a[0] for a in assign.values())
    left = list(remaining.elements())
    if left: print("  未分配数值:",left)
