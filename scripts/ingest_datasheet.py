# -*- coding: utf-8 -*-
"""
ingest_datasheet.py
用户上传器件手册(datasheet)后，将其归档并生成/更新「设计规则卡」入库。

行为：
  1. 归档原始 datasheet 到 knowledge_base/datasheets/<型号>/
  2. 提取 PDF 文本首若干页，辅助 AI 填写规则卡
  3. 生成规则卡骨架 knowledge_base/chip_rules/<型号>.md（若已存在则不覆盖，仅提示）
  4. 更新 chip_rules/index.json 索引

用法：
  python ingest_datasheet.py "<datasheet.pdf>" [型号] [skill_root]
  型号可省略，省略时取文件名（去扩展名）。
"""
import sys, os, json, re, shutil, datetime

def extract_text(pdf_path, max_pages=6, max_chars=8000):
    try:
        import fitz
    except ImportError:
        return "", "PyMuPDF 未安装，跳过文本预览"
    doc = fitz.open(pdf_path)
    parts = []
    for i in range(min(max_pages, doc.page_count)):
        parts.append(doc[i].get_text())
    doc.close()
    txt = "\n".join(parts)
    return txt[:max_chars], None

def main():
    args = sys.argv[1:]
    if not args:
        print("ERROR: 用法 python ingest_datasheet.py <datasheet.pdf> [型号] [skill_root]"); sys.exit(1)
    pdf = args[0]
    model = args[1] if len(args) >= 2 and args[1] else os.path.splitext(os.path.basename(pdf))[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = args[2] if len(args) >= 3 else os.path.dirname(script_dir)

    if not os.path.exists(pdf):
        print(f"ERROR: 文件不存在 {pdf}"); sys.exit(1)

    # 归一化型号（做文件名安全处理）
    model_safe = re.sub(r'[\\/:*?"<>|]', '_', model).strip()
    if model_safe in ("", ".", ".."):
        print("ERROR: 型号必须为非空文件夹名称，不能是 . 或 .."); sys.exit(1)
    ds_dir = os.path.join(skill_root, "knowledge_base", "datasheets", model_safe)
    chip_dir = os.path.join(skill_root, "knowledge_base", "chip_rules")
    os.makedirs(ds_dir, exist_ok=True)
    os.makedirs(chip_dir, exist_ok=True)

    # 1. 归档
    dst = os.path.join(ds_dir, os.path.basename(pdf))
    if os.path.abspath(pdf) != os.path.abspath(dst):
        shutil.copy2(pdf, dst)

    # 2. 提取文本
    preview, err = extract_text(dst)

    # 3. 生成规则卡骨架
    card_path = os.path.join(chip_dir, f"{model_safe}.md")
    card_exists = os.path.exists(card_path)
    if not card_exists:
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(f"""# 器件设计规则卡：{model}

- **型号**: {model}
- **封装**: <待填写>
- **datasheet版本**: <待填写>
- **归档路径**: knowledge_base/datasheets/{model_safe}/{os.path.basename(pdf)}
- **入库时间**: {datetime.date.today().isoformat()}
- **状态**: 骨架待AI补全

## 电源引脚要求
<型号/引脚名/电压范围/去耦电容要求>

## 关键引脚功能
<复位/启动配置/时钟/使能引脚 的连接方式与要求>

## 外围器件参数
<退耦电容、上下拉电阻、匹配电阻、晶振负载电容等推荐值>

## 典型应用电路
<datasheet 推荐电路要点>

## 设计禁忌
<明确禁止的接法>

## datasheet 文本预览（首页节选，供AI提取，可删除）
```
{preview[:3000] if preview else '（无文本，可能为光栅PDF，需多模态识别）'}
```
""")

    # 4. 更新索引
    idx_path = os.path.join(chip_dir, "index.json")
    if os.path.exists(idx_path):
        with open(idx_path, encoding="utf-8") as f:
            idx = json.load(f)
    else:
        idx = {"chips": []}
    # upsert
    entry = {
        "model": model,
        "model_safe": model_safe,
        "card": f"knowledge_base/chip_rules/{model_safe}.md",
        "datasheet": f"knowledge_base/datasheets/{model_safe}/{os.path.basename(pdf)}",
        "ingested_at": datetime.date.today().isoformat(),
    }
    idx["chips"] = [c for c in idx["chips"] if c.get("model_safe") != model_safe]
    idx["chips"].append(entry)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

    print(f"OK 已归档器件手册：{model}")
    print(f"  规则卡：{card_path} {'(已存在，未覆盖)' if card_exists else '(新建骨架)'}")
    print(f"  datasheet：{dst}")
    if err: print(f"  提示：{err}")
    print(f"  下一步：请AI阅读规则卡预览文本，补全『电源引脚/关键引脚/外围器件/禁忌』字段后保存。")

if __name__ == "__main__":
    main()
