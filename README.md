# 📊 学生成绩统计工具

适合老师、教务人员使用的学生成绩统计桌面软件。输入姓名和成绩，一键获得最高分、最低分、平均分、中位数、标准差、及格率、分数段分布、排名等全面统计。

## ✨ 功能特性

- 📝 **三种输入方式** — 手动录入、CSV 导入、JSON 导入
- 📊 **八项统计指标** — 最高分（含并列）、最低分（含并列）、平均分、中位数、标准差、及格率、分数段分布、排名
- 🖥 **原生桌面应用** — 基于 customtkinter 的现代化 GUI，无需浏览器
- 📱 **自适应布局** — 窗口自由缩放，左右分栏可拖拽调整
- 🎬 **启动动画** — 精美的加载画面
- 💾 **导出 CSV** — 方便在 Excel 中进一步处理
- 🎚 **可调及格线** — 滑块实时调整，统计即时刷新
- 📦 **单文件 EXE** — 双击即用，无需安装 Python

## 📥 安装与运行

### 方式一：下载 EXE（推荐，无需安装任何环境）

从 [Releases](../../releases) 页面下载最新版 `成绩统计工具.exe`，双击运行即可。

### 方式二：Python 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/zhiyu2753-creator/--.git
cd --

# 2. 安装依赖（仅 GUI 模式需要）
pip install customtkinter

# 3. 启动 GUI
python app.py

# 或使用命令行版（无需额外依赖）
python grade_stats.py --demo
```

## 📖 使用指南

### GUI 桌面版

| 操作 | 方法 |
|------|------|
| 添加学生 | 左侧输入姓名 + 成绩 → 点击「添加」或按 Enter |
| 删除学生 | 列表选中 → 点击「删除选中」 |
| 修改学生 | 双击列表中的学生 → 弹出编辑窗口 |
| 导入文件 | 点击「📥 导入文件」→ 选择 CSV 或 JSON |
| 演示数据 | 点击「🎬 演示数据」加载 8 条示例 |
| 调整及格线 | 拖动底部滑块（0-100） |
| 导出数据 | 点击「💾 导出 CSV」保存当前列表 |
| 调整布局 | 拖拽中间分隔条改变左右面板比例 |

### 命令行版

```bash
python grade_stats.py                  # 交互式逐个录入
python grade_stats.py --demo           # 使用内置演示数据
python grade_stats.py --file data.csv  # 从 CSV 文件导入
python grade_stats.py --file data.json # 从 JSON 文件导入
python grade_stats.py --pass-line 70   # 自定义及格线
```

### 作为 Python 库使用

```python
from grade_stats import Student, analyze

students = [Student("张三", 85), Student("李四", 92), Student("王五", 78)]
result = analyze(students, pass_line=60)

print(result.average)     # 85.0
print(result.max_student) # Student(name='李四', score=92)
print(result.pass_rate)   # 1.0
print(result.distribution) # {'90-100': 1, '80-89': 1, '70-79': 1, ...}
```

## 📋 文件格式

### CSV 格式

```csv
姓名,成绩
张三,85
李四,92
王五,78
```

支持带或不带表头，编码自动识别（含 UTF-8 BOM）。

### JSON 格式

```json
[
  { "name": "张三", "score": 85 },
  { "name": "李四", "score": 92 }
]
```

或键值对格式：

```json
{
  "张三": 85,
  "李四": 92
}
```

## 🔧 开发与构建

```bash
# 运行测试
python -m pytest test_grade_stats.py -v

# 打包 EXE
build_exe.bat
# 或手动：
python -m PyInstaller --onefile --noconsole --name "成绩统计工具" \
  --hidden-import customtkinter --hidden-import darkdetect \
  --hidden-import grade_stats --clean app.py
```

## 🛠 技术栈

| 模块 | 技术 | 外部依赖 |
|------|------|----------|
| 核心引擎 | Python 标准库 (`statistics`, `csv`, `json`) | 无 |
| 桌面 GUI | customtkinter + tkinter | `customtkinter`, `darkdetect` |
| 打包 | PyInstaller | `pyinstaller` |

## 📁 项目结构

```
├── grade_stats.py       # 核心引擎 + CLI 入口
├── app.py               # 桌面 GUI 应用
├── test_grade_stats.py  # 单元测试（32 项）
├── build_exe.bat        # 一键打包脚本
├── SPEC.md              # 规格文档
└── README.md
```

## 📄 许可

MIT License
