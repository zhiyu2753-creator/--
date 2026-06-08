# SPEC: 学生成绩统计小工具

---

## 1. Objective（目标）

**一句话：** 让非技术用户（如老师）能方便地输入学生成绩，一键获得最高分、最低分、平均分等全面统计数据。

**目标用户：** 非技术用户（老师、教务人员），通过命令行直接操作。

**成功标准：**
- 用户能在 30 秒内完成一批成绩的输入并看到统计结果
- 支持三种输入方式（交互式、文件导入、代码调用）
- 输出直观、中文界面、异常情况有友好提示

---

## 2. Commands / API（命令与接口）

### 2.1 CLI 命令

| 命令 | 说明 |
|------|------|
| `python grade_stats.py` | 交互式输入模式（默认） |
| `python grade_stats.py --demo` | 使用内置示例数据快速演示 |
| `python grade_stats.py --file scores.csv` | 从 CSV 文件读取 |
| `python grade_stats.py --file scores.json` | 从 JSON 文件读取 |
| `python grade_stats.py --help` | 显示帮助信息 |

**交互式输入流程：**
1. 提示用户逐行输入「姓名 成绩」
2. 输入空行结束
3. 回显已录入的学生列表，允许确认/修改/删除
4. 确认后输出完整统计

### 2.2 Python API（作为库调用）

```python
from grade_stats import analyze, Student

students = [Student("张三", 85), Student("李四", 92)]
result = analyze(students)
# result = {
#     "count": 2,
#     "max": Student("李四", 92),
#     "min": Student("张三", 85),
#     "average": 88.5,
#     "median": 88.5,
#     "std_dev": 4.95,
#     "pass_rate": 1.0,        # 默认 ≥60 为及格
#     "distribution": {...},   # 分数段分布
#     "sorted": [Student(...), ...],  # 按成绩降序
# }
```

### 2.3 支持的统计指标

| 指标 | 说明 |
|------|------|
| 最高分 | 含并列提示 |
| 最低分 | 含并列提示 |
| 平均分 | 算术平均 |
| 中位数 | 偶数个取中间两数的平均 |
| 标准差 | 总体标准差 |
| 及格率 | 默认及格线 60 分，可配置 |
| 分数段分布 | 90-100 / 80-89 / 70-79 / 60-69 / <60 |
| 排序列表 | 按成绩降序输出全部学生 |

---

## 3. Project Structure（项目结构）

```
笔试/
├── SPEC.md                 # 本文件
├── grade_stats.py          # 主程序（CLI + 核心逻辑）
└── test_grade_stats.py     # 单元测试
```

**决策理由：** 这是一个小型工具，单文件即可承载全部逻辑（约 300 行），无需拆分成多模块。若后续扩展再重构。

**模块内结构（class/function 分组）：**
```
# 1. 数据模型    — Student dataclass
# 2. 统计引擎    — analyze() 及各项统计函数
# 3. 格式化输出   — print_report()
# 4. 数据输入    — collect_interactive(), read_csv(), read_json()
# 5. CLI 入口    — main() / argparse
```

---

## 4. Code Style（代码规范）

| 维度 | 规范 |
|------|------|
| 类型注解 | 所有函数参数和返回值必须有类型注解 |
| 数据模型 | 使用 `@dataclass` 定义 Student |
| 注释语言 | 中文 docstring + 关键逻辑行内注释 |
| 命名规范 | 函数用 `snake_case`，类用 `PascalCase` |
| 行长 | ≤ 100 字符 |
| 错误处理 | 空列表、非数字成绩、文件不存在等均需友好提示，不裸抛 traceback |
| 依赖 | **零外部依赖**，仅用 Python 标准库 |

---

## 5. Testing Strategy（测试策略）

| 层级 | 内容 | 工具 |
|------|------|------|
| 单元测试 | 每个统计函数独立测试 | `unittest`（标准库） |
| 边界测试 | 空列表、单人、多人并列、全满分、全零分 | 同上 |
| 输入容错 | 非法成绩字符串、缺失列、文件编码问题 | 同上 |

**测试用例清单：**
- `test_average` — 正常、单人、空列表抛异常
- `test_max_min` — 唯一最值、多人并列
- `test_median` — 奇数个、偶数个
- `test_std_dev` — 值全部相同时为 0
- `test_pass_rate` — 全及格、全不及格、自定义及格线
- `test_distribution` — 各分段计数正确
- `test_analyze_empty` — 空列表抛异常
- `test_csv_parsing` — 正常 CSV、缺列 CSV、空文件
- `test_json_parsing` — 正常 JSON、格式错误 JSON

---

## 6. Boundaries（边界）

### Always Do（始终执行）
- ✅ 中文用户界面，面向非技术用户
- ✅ 所有统计计算使用标准库（`statistics` 模块）
- ✅ 输入有误时给出具体、友好的中文错误提示
- ✅ 函数带类型注解和中文 docstring
- ✅ 最高分/最低分自动检测并列情况

### Ask First（先确认）
- ⚠️ 是否新增外部依赖（当前原则：零依赖）
- ⚠️ 多文件拆分（当前原则：单文件）
- ⚠️ GUI / Web 界面（当前原则：仅 CLI）
- ⚠️ 数据持久化（保存历史记录到文件）

### Never Do（禁止）
- ❌ 使用 `pandas`、`numpy` 等重型第三方库
- ❌ 英文界面或英文错误提示
- ❌ 裸抛 Python traceback 给用户看到
- ❌ 静默忽略错误（如跳过非法行而不提示）

---

> **状态：** ⏳ 等待确认 → 确认后按此 SPEC 实现 `grade_stats.py` + `test_grade_stats.py`
