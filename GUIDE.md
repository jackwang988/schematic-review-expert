# 使用指导

安装、触发和首次运行命令见 README.md。完整流程见 references/review-workflow.md。公开版所有知识库初始为空，完整评审须有可读取文件与图像、执行脚本的 AI 助手参与。

## 器件资料入库

用 `python scripts/ingest_datasheet.py "uploads/chip.pdf" "YOUR-CHIP"` 归档用户有权处理的手册并建立规则卡骨架。随后逐项核实封装、型号、版本、工作范围与引脚定义。自动提取不等于验证。原厂 PDF 和本地规则卡默认不提交公共仓库。

## 原理图预处理

用 `python scripts/extract_schematic.py "uploads/demo.pdf"` 解析。output/_extract/meta.json 提供页数、位号与电源网络提示；文本页可能生成 txt，扫描或少文字页生成 png。预处理不生成电气网表，不直接完成设计正确性判断。

## Excel 导入表结构

build_company_rules.py 支持特定格式，非任意 Excel 通用解析器。主工作表名称须含“总体原则”，从第 4 行开始：B 序号、C SCH/PCB、D 检查项目、E 检查内容、F 严重度（高/中/低）。摄像头或 SE 工作表从第 5 行合并非空列；名称含“案例”的表导入经验库。导入后核对 index.json，空结果不能当作规范检查通过。

## 检索

`kb_search.py --list-chips` 列本地已入库型号；初始应提示为空。`--chip YOUR-CHIP` 查询型号。`--keyword` 仅检索公司规则索引，不是跨库全文搜索。`--list-modules` 列实际模块。

## 边界

手册不足则列待确认；公司规范缺失则标注未覆盖。只有图纸连接事实和可靠规则相互支持时才判错。原理图检查不替代网表、PCB 评审、仿真和硬件实测。
