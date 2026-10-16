# 原理图辅助评审 Skill · schematic-review-expert

作者：[Jack](https://github.com/jackwang988) · 公开版 `2.2.1-public` · [MIT](LICENSE)

把原理图 PDF 交给支持 Skills 的 AI 助手，按六阶段工作流检查器件外围、电源与复位、接口等，并整理带页码、坐标、证据和待确认项的报告。Python 脚本负责 PDF 预处理、规则检索与手册入库，完整评审需要 AI 助手参与，并非独立运行的 EDA/ERC 引擎。

## 包含什么

- 原理图评审工作流与 5 个辅助脚本。
- 芯片规则库初始为空，由使用者提供原厂手册后在本地建库。公开版不分发历史项目规则卡。
- 公司设计规范、原厂 datasheet PDF 和项目评审案例初始为空。未导入公司规范时报告应标注该维度未覆盖。
- 不承诺检出率；无法确认的连线、参数与引脚进入待确认项，真实设计须由工程师复核。

## 安装到 Codex

需要 Git、Python 3.10+ 和支持本地 Skills、文件读取与脚本执行的 Codex。克隆到用户技能目录下；如目录已存在，请先备份，不要覆盖用户知识库。

macOS / Linux：
```bash
mkdir -p ~/.agents/skills
git clone https://github.com/jackwang988/schematic-review-expert.git ~/.agents/skills/schematic-review-expert
cd ~/.agents/skills/schematic-review-expert
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/kb_search.py --list-chips
```

Windows PowerShell：
```powershell
New-Item -ItemType Directory -Force "$HOME/.agents/skills" | Out-Null
git clone https://github.com/jackwang988/schematic-review-expert.git "$HOME/.agents/skills/schematic-review-expert"
Set-Location "$HOME/.agents/skills/schematic-review-expert"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/kb_search.py --list-chips
```

重新开启 Codex 会话，并在提示词中告知虚拟环境 Python 的路径。安装目录依据 [官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)；其他宿主请按其本地 Skill 目录安装，并完整保留目录结构。本仓库公开不等于自动安装到 ChatGPT Work。

## 第一次使用

将可处理的原理图放在 `uploads/`，输入：

> 用 $schematic-review-expert 评审 uploads/demo.pdf，重点检查电源、复位和 USB 接口。先确认手册与规范是否齐全；逐引脚核对，输出证据、未覆盖范围和待确认项。

脚本单独运行示例（用已安装依赖的 Python）：
```bash
python scripts/extract_schematic.py "uploads/demo.pdf"
python scripts/kb_search.py --chip CP2102N
python scripts/ingest_datasheet.py "uploads/chip.pdf" "YOUR-CHIP"
python scripts/build_company_rules.py "uploads/checklist.xlsx"
python -m unittest discover -s tests -v
```

报告与中间文件在 `output/`。`--keyword` 仅查公司规则；未附带的手册需自行从原厂取得。详细操作及 Excel 表结构见 [GUIDE.md](GUIDE.md)。

## 数据与贡献

[.gitignore](.gitignore) 默认忽略上传、报告、手册与用户公司规范；已跟踪的文件仍需自行审查。公开提交前检查暂存区，不要上传真实公司或客户资料。

见 [贡献指南](CONTRIBUTING.md)、[数据与安全说明](SECURITY.md)、[第三方说明](THIRD_PARTY_NOTICES.md)。AI 识别及通用规则不取代原厂手册、网表校验和硬件实测。
