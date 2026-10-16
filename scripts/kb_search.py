# -*- coding: utf-8 -*-
"""
kb_search.py
知识库检索工具：在公司规范库 / 器件规则库 / 经验库中按关键词/模块检索规则条目。
低 Token 设计：只返回命中的结构化条目，不返回全文。

用法：
  python kb_search.py --module 电源设计            # 按模块加载全部条目
  python kb_search.py --keyword 复位 晶振 去耦      # 按关键词检索公司规范
  python kb_search.py --chip CH9329                # 检索器件规则卡是否已入库
  python kb_search.py --list-modules               # 列出所有可用模块
  python kb_search.py --list-chips                 # 列出已入库器件
可加 [--root <skill_root>]，默认自动推断。
"""
import sys, os, json, argparse

def load_index(skill_root):
    p = os.path.join(skill_root, "knowledge_base", "company_rules", "index.json")
    if not os.path.exists(p): return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def load_chip_index(skill_root):
    p = os.path.join(skill_root, "knowledge_base", "chip_rules", "index.json")
    if not os.path.exists(p): return {"chips": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--module", default=None)
    ap.add_argument("--keyword", nargs="*", default=None)
    ap.add_argument("--chip", default=None)
    ap.add_argument("--list-modules", action="store_true")
    ap.add_argument("--list-chips", action="store_true")
    a = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = a.root or os.path.dirname(script_dir)
    idx = load_index(root)
    if idx is None:
        idx = {"modules": [], "rules": []}

    if a.list_modules:
        for m in idx["modules"]:
            cnt = sum(1 for r in idx["rules"] if r["module"] == m)
            print(f"{m}\t{cnt}条")
        return

    if a.list_chips:
        ci = load_chip_index(root)
        if not ci["chips"]:
            print("（器件规则库为空，用户可上传 datasheet 入库）")
        for c in ci["chips"]:
            print(f"{c['model']}\t{c['card']}")
        return

    if a.chip:
        ci = load_chip_index(root)
        hit = [c for c in ci["chips"] if a.chip.lower() in c["model"].lower()]
        if hit:
            for c in hit:
                print(f"命中：{c['model']} -> {c['card']}  datasheet: {c.get('datasheet', '未归档')}（请检查本地是否存在）")
        else:
            print(f"未命中器件：{a.chip}（需外网检索 datasheet 或提示用户上传）")
        return

    results = []
    if a.module:
        results = [r for r in idx["rules"] if a.module in r["module"]]
    elif a.keyword:
        kws = [k.lower() for k in a.keyword]
        for r in idx["rules"]:
            hay = (r["content"] + r["category"] + r["module"]).lower()
            if any(k in hay for k in kws):
                results.append(r)
    else:
        print("请指定 --module / --keyword / --chip"); return

    print(f"# 命中 {len(results)} 条规则\n")
    for r in results:
        print(f"[{r['no']}|{r['domain']}|{r['module']}|默认{r['severity']}] {r['content']}")

if __name__ == "__main__":
    main()
