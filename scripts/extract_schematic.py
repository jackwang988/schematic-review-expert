# -*- coding: utf-8 -*-
"""
extract_schematic.py
原理图 PDF 预处理：判定矢量/光栅，提取文本、元件位号、页码，光栅页渲染为图片供多模态识别。

用法：
  python extract_schematic.py "<schematic.pdf>" [skill_root]

输出（写入 output/_extract/）：
  meta.json         页数、每页矢量/光栅判定、文本量、推测元件位号
  page_XX.txt       矢量页文本（若有）
  page_XX.png       光栅页/需视觉识别页的渲染图（供 analyze_image）
并在 stdout 打印结构化摘要，供 AI 决定后续流程。
"""
import sys, os, json, re

REF_DES = re.compile(r'\b([RCLUQDJPYXFKTZ]{1,3}\d{1,4}[A-Z]?)\b')  # 常见位号
NET_HINT = re.compile(r'\b(VCC|VDD|VBAT|GND|AGND|DGND|3V3|1V8|5V0?|VIN|VOUT|VSYS|VDDIO|AVDD|DVDD)\b', re.I)

def analyze(pdf_path, out_dir):
    import fitz
    doc = fitz.open(pdf_path)
    os.makedirs(out_dir, exist_ok=True)
    pages = []
    all_refs = set()
    all_nets = set()
    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text()
        text_len = len(text.strip())
        # 判定矢量/光栅：矢量图文本量大且含绘图指令；光栅图基本无文本，页面被大图占满
        images = page.get_images(full=True)
        drawings = page.get_drawings()
        is_raster = (text_len < 20 and len(images) >= 1)
        kind = "raster" if is_raster else "vector"
        refs = sorted(set(REF_DES.findall(text)))
        nets = sorted(set(m.group(0).upper() for m in NET_HINT.finditer(text)))
        all_refs.update(refs); all_nets.update(nets)
        # 保存文本
        if text_len > 0:
            with open(os.path.join(out_dir, f"page_{i+1:02d}.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        # 光栅页 or 文本极少的页 -> 渲染成图片供多模态识别
        if is_raster or text_len < 20:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 提升清晰度
            pix.save(os.path.join(out_dir, f"page_{i+1:02d}.png"))
        pages.append({
            "page": i + 1,
            "kind": kind,
            "text_len": text_len,
            "n_images": len(images),
            "n_drawings": len(drawings),
            "ref_designators": refs,
            "power_nets": nets,
            "rendered_png": (is_raster or text_len < 20),
        })
    doc.close()
    n_raster = sum(1 for p in pages if p["kind"] == "raster")
    overall = "光栅PDF" if n_raster > len(pages) / 2 else ("矢量PDF" if n_raster == 0 else "混合PDF")
    meta = {
        "file": os.path.basename(pdf_path),
        "page_count": len(pages),
        "overall_type": overall,
        "raster_pages": n_raster,
        "unique_ref_designators": sorted(all_refs),
        "unique_power_nets": sorted(all_nets),
        "pages": pages,
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta

def main():
    args = sys.argv[1:]
    if not args:
        print("ERROR: 用法 python extract_schematic.py <schematic.pdf> [skill_root]"); sys.exit(1)
    pdf = args[0]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = args[1] if len(args) >= 2 else os.path.dirname(script_dir)
    if not os.path.exists(pdf):
        print(f"ERROR: 文件不存在 {pdf}"); sys.exit(1)
    try:
        import fitz  # noqa
    except ImportError:
        print("ERROR: 需要 PyMuPDF，请先安装：pip install pymupdf"); sys.exit(2)
    out_dir = os.path.join(skill_root, "output", "_extract")
    meta = analyze(pdf, out_dir)
    print(f"OK 解析完成：{meta['file']}")
    print(f"  类型：{meta['overall_type']}  | 页数：{meta['page_count']}  | 光栅页：{meta['raster_pages']}")
    print(f"  识别位号数：{len(meta['unique_ref_designators'])}")
    print(f"  电源网络提示：{', '.join(meta['unique_power_nets']) or '（无，可能需视觉识别）'}")
    print(f"  中间产物目录：{out_dir}")
    raster_pngs = [f"page_{p['page']:02d}.png" for p in meta['pages'] if p['rendered_png']]
    if raster_pngs:
        print(f"  需多模态视觉识别的页面图片：{', '.join(raster_pngs)}")

if __name__ == "__main__":
    main()
