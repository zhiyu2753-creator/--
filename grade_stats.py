"""
学生成绩统计小工具
===================
面向非技术用户（如老师）的命令行工具，支持交互式输入、CSV/JSON 文件导入、
Python API 调用三种方式，输出最高分、最低分、平均分、中位数、标准差、及格率、
分数段分布、排序列表等全面统计。

用法：
    python grade_stats.py                 # 交互式输入
    python grade_stats.py --demo          # 演示模式
    python grade_stats.py --file data.csv # 从 CSV 导入
    python grade_stats.py --file data.json# 从 JSON 导入
    python grade_stats.py --help          # 帮助信息

作为库使用：
    from grade_stats import Student, analyze

    students = [Student("张三", 85), Student("李四", 92)]
    result = analyze(students)
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# ── 1. 数据模型 ────────────────────────────────────────────


@dataclass
class Student:
    """学生数据，包含姓名和成绩。"""
    name: str
    score: float


@dataclass
class StatsResult:
    """统计结果容器，便于格式化输出和程序化调用。"""
    count: int
    max_student: Student
    min_student: Student
    ties_max: List[Student]       # 并列最高分的学生
    ties_min: List[Student]       # 并列最低分的学生
    average: float
    median: float
    std_dev: float
    pass_rate: float              # 0.0 ~ 1.0
    pass_line: float              # 及格线
    distribution: Dict[str, int]  # 分数段 → 人数
    sorted_students: List[Student]  # 按成绩降序


# ── 2. 统计引擎 ────────────────────────────────────────────

def analyze(students: List[Student], pass_line: float = 60.0) -> StatsResult:
    """
    对一批学生成绩进行全方位统计分析。

    Args:
        students: 学生列表
        pass_line: 及格分数线，默认 60 分

    Returns:
        StatsResult: 包含全部统计指标的结果对象

    Raises:
        ValueError: 学生列表为空时抛出
    """
    if not students:
        raise ValueError("学生列表不能为空，请至少提供一位学生的成绩。")

    scores = [s.score for s in students]

    # ── 最高分（含并列检测） ──
    max_score = max(scores)
    max_student = max(students, key=lambda s: s.score)
    ties_max = [s for s in students if s.score == max_score]

    # ── 最低分（含并列检测） ──
    min_score = min(scores)
    min_student = min(students, key=lambda s: s.score)
    ties_min = [s for s in students if s.score == min_score]

    # ── 平均分、中位数、标准差 ──
    avg = statistics.mean(scores)
    med = statistics.median(scores)
    std = statistics.pstdev(scores)  # 总体标准差

    # ── 及格率 ──
    passed = sum(1 for s in scores if s >= pass_line)
    pass_rate = passed / len(students)

    # ── 分数段分布 ──
    distrib = {
        "90-100": 0,
        "80-89": 0,
        "70-79": 0,
        "60-69": 0,
        "60以下": 0,
    }
    for s in scores:
        if s >= 90:
            distrib["90-100"] += 1
        elif s >= 80:
            distrib["80-89"] += 1
        elif s >= 70:
            distrib["70-79"] += 1
        elif s >= 60:
            distrib["60-69"] += 1
        else:
            distrib["60以下"] += 1

    # ── 按成绩降序排列 ──
    sorted_students = sorted(students, key=lambda s: s.score, reverse=True)

    return StatsResult(
        count=len(students),
        max_student=max_student,
        min_student=min_student,
        ties_max=ties_max,
        ties_min=ties_min,
        average=avg,
        median=med,
        std_dev=std,
        pass_rate=pass_rate,
        pass_line=pass_line,
        distribution=distrib,
        sorted_students=sorted_students,
    )


# ── 2b. 单指标便捷函数（兼容旧版 API） ──────────────────────


def get_max_score(students: List[Student]) -> Student:
    """返回最高分的学生（便捷函数）。"""
    if not students:
        raise ValueError("学生列表不能为空")
    return max(students, key=lambda s: s.score)


def get_min_score(students: List[Student]) -> Student:
    """返回最低分的学生（便捷函数）。"""
    if not students:
        raise ValueError("学生列表不能为空")
    return min(students, key=lambda s: s.score)


def get_average_score(students: List[Student]) -> float:
    """返回平均分（便捷函数）。"""
    if not students:
        raise ValueError("学生列表不能为空")
    return sum(s.score for s in students) / len(students)


# ── 3. 格式化输出 ──────────────────────────────────────────

def print_report(result: StatsResult) -> None:
    """以用户友好的中文格式打印统计报告。"""
    print("\n" + "=" * 44)
    print("  📊  学生成绩统计报告")
    print("=" * 44)

    # 基本信息
    print(f"  学生总数：{result.count} 人")
    print(f"  及格线　：{result.pass_line:.0f} 分")
    print("-" * 44)

    # 最高分
    if len(result.ties_max) == 1:
        print(f"  🥇 最高分：{result.max_student.name} — {result.max_student.score}")
    else:
        names = "、".join(s.name for s in result.ties_max)
        score = result.max_student.score
        print(f"  🥇 最高分：{names} — {score}（{len(result.ties_max)} 人并列）")

    # 最低分
    if len(result.ties_min) == 1:
        print(f"  🥈 最低分：{result.min_student.name} — {result.min_student.score}")
    else:
        names = "、".join(s.name for s in result.ties_min)
        score = result.min_student.score
        print(f"  🥈 最低分：{names} — {score}（{len(result.ties_min)} 人并列）")

    # 统计量
    print(f"  平均分　：{result.average:.2f}")
    print(f"  中位数　：{result.median:.2f}")
    print(f"  标准差　：{result.std_dev:.2f}")
    print(f"  及格率　：{result.pass_rate:.1%}（{int(result.pass_rate * result.count)}/{result.count}）")

    # 分数段分布
    print("-" * 44)
    print("  📈 分数段分布")
    bar_max = 20  # 柱状图最大宽度
    max_count = max(result.distribution.values()) if result.count > 0 else 1
    for segment, count in result.distribution.items():
        bar_len = int(count / max_count * bar_max) if max_count > 0 else 0
        bar = "█" * bar_len
        print(f"  {segment:>6}：{count:>3} 人 {bar}")

    # 全部排名
    print("-" * 44)
    print("  📋 成绩排名（降序）")
    for i, s in enumerate(result.sorted_students, 1):
        print(f"  {i:>3}. {s.name:<8} {s.score}")

    print("=" * 44 + "\n")


# ── 4. 数据输入 ────────────────────────────────────────────

def collect_interactive() -> List[Student]:
    """交互式收集学生数据，支持确认/修改/删除。"""
    students: List[Student] = []

    print("\n📝 交互式成绩录入")
    print("   请输入「姓名 成绩」，一行一个，输入空行结束。")
    print("   示例：张三 85")

    # 阶段一：逐行录入
    while True:
        entry = input(f"   [{len(students) + 1}] ").strip()
        if not entry:
            if not students:
                print("   ⚠️ 尚未录入任何学生，请至少输入一条数据。")
                continue
            break

        # 支持逗号或空格分隔
        parts = entry.replace(",", " ").replace("，", " ").split()
        if len(parts) < 2:
            print("   ⚠️ 格式错误，请用「姓名 成绩」格式，如「张三 85」")
            continue

        name = parts[0]
        try:
            score = float(parts[1])
        except ValueError:
            print(f"   ⚠️「{parts[1]}」不是有效数字，请重新输入")
            continue

        if score < 0 or score > 100:
            print(f"   ⚠️ 成绩应在 0~100 之间，你输入的是 {score}")
            continue

        students.append(Student(name=name, score=score))
        print(f"   ✅ 已录入：{name}（{score} 分）")

    # 阶段二：确认与编辑
    while True:
        print(f"\n   已录入 {len(students)} 名学生：")
        for i, s in enumerate(students, 1):
            print(f"   {i}. {s.name} — {s.score}")

        print("\n   输入序号删除，输入「姓名 新成绩」修改，回车确认：")
        action = input("   > ").strip()

        if not action:
            break  # 确认完成

        # 尝试按序号删除
        if action.isdigit():
            idx = int(action) - 1
            if 0 <= idx < len(students):
                removed = students.pop(idx)
                print(f"   🗑 已删除：{removed.name}")
            else:
                print(f"   ⚠️ 序号超出范围（1~{len(students)}）")
            continue

        # 尝试修改成绩
        parts = action.replace(",", " ").replace("，", " ").split()
        if len(parts) >= 2:
            name = parts[0]
            try:
                new_score = float(parts[1])
            except ValueError:
                print(f"   ⚠️「{parts[1]}」不是有效数字")
                continue

            if new_score < 0 or new_score > 100:
                print(f"   ⚠️ 成绩应在 0~100 之间")
                continue

            # 按姓名查找并修改
            found = False
            for s in students:
                if s.name == name:
                    s.score = new_score
                    print(f"   ✏️ 已修改：{name} → {new_score}")
                    found = True
                    break
            if not found:
                students.append(Student(name=name, score=new_score))
                print(f"   ✅ 已新增：{name}（{new_score} 分）")
        else:
            print("   ⚠️ 输入无效，请重试")

    return students


def read_csv(filepath: str) -> List[Student]:
    """
    从 CSV 文件读取学生数据。
    支持两种格式：
      - 含表头：name,score
      - 无表头：直接两列
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{filepath}")

    students: List[Student] = []
    with open(path, "r", encoding="utf-8-sig") as f:  # utf-8-sig 处理 BOM
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            # 跳过空行
            if not row or all(c.strip() == "" for c in row):
                continue
            # 尝试跳过表头行
            if row_num == 1 and row[0].strip().lower() in ("name", "姓名", "名字"):
                continue
            if len(row) < 2:
                print(f"   ⚠️ 第 {row_num} 行数据不完整，已跳过")
                continue
            name = row[0].strip()
            try:
                score = float(row[1].strip())
            except ValueError:
                print(f"   ⚠️ 第 {row_num} 行成绩「{row[1].strip()}」不是有效数字，已跳过")
                continue
            if score < 0 or score > 100:
                print(f"   ⚠️ 第 {row_num} 行成绩 {score} 超出 0~100 范围，已跳过")
                continue
            students.append(Student(name=name, score=score))

    if not students:
        raise ValueError(f"未能从文件中读取到任何有效学生数据：{filepath}")
    return students


def read_json(filepath: str) -> List[Student]:
    """
    从 JSON 文件读取学生数据。
    支持两种格式：
      - 对象数组：[{"name": "张三", "score": 85}, ...]
      - 对象映射：{"张三": 85, "李四": 92}
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{filepath}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    students: List[Student] = []

    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                name = item.get("name") or item.get("姓名")
                score = item.get("score") or item.get("成绩")
                if name is None or score is None:
                    print(f"   ⚠️ 第 {i} 条数据缺少 name/score 字段，已跳过")
                    continue
            else:
                print(f"   ⚠️ 第 {i} 条数据格式不正确，已跳过")
                continue
            try:
                score = float(score)
            except (ValueError, TypeError):
                print(f"   ⚠️ 第 {i} 条数据成绩「{score}」不是有效数字，已跳过")
                continue
            if score < 0 or score > 100:
                print(f"   ⚠️ 第 {i} 条数据成绩 {score} 超出 0~100 范围，已跳过")
                continue
            students.append(Student(name=str(name), score=score))

    elif isinstance(data, dict):
        for name, score in data.items():
            try:
                score = float(score)
            except (ValueError, TypeError):
                print(f"   ⚠️ {name} 的成绩「{score}」不是有效数字，已跳过")
                continue
            if score < 0 or score > 100:
                print(f"   ⚠️ {name} 的成绩 {score} 超出 0~100 范围，已跳过")
                continue
            students.append(Student(name=name, score=score))

    else:
        raise ValueError(f"JSON 文件格式不支持，请使用数组或对象：{filepath}")

    if not students:
        raise ValueError(f"未能从文件中读取到任何有效学生数据：{filepath}")
    return students


# ── 5. CLI 入口 ────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="grade_stats",
        description="学生成绩统计小工具 — 输入姓名和成绩，输出全面统计数据。",
        epilog="示例：python grade_stats.py --demo",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="使用内置示例数据快速演示",
    )
    parser.add_argument(
        "--file", type=str, default=None, metavar="PATH",
        help="从 CSV 或 JSON 文件导入数据",
    )
    parser.add_argument(
        "--pass-line", type=float, default=60.0, metavar="N",
        help="设置及格分数线（默认 60）",
    )
    return parser


# 内置演示数据
DEMO_STUDENTS = [
    Student("张三", 85),
    Student("李四", 92),
    Student("王五", 78),
    Student("赵六", 88),
    Student("钱七", 92),
    Student("孙八", 55),
    Student("周九", 73),
    Student("吴十", 60),
]


def main(argv: List[str] | None = None) -> None:
    """主入口，解析参数并调度对应的输入模式。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.demo:
            students = DEMO_STUDENTS
            print("🎬 演示模式 — 使用内置示例数据")

        elif args.file:
            filepath = args.file
            ext = Path(filepath).suffix.lower()
            if ext == ".csv":
                students = read_csv(filepath)
                print(f"📂 已从 CSV 文件读取：{filepath}")
            elif ext == ".json":
                students = read_json(filepath)
                print(f"📂 已从 JSON 文件读取：{filepath}")
            else:
                print(f"❌ 不支持的文件格式「{ext}」，请使用 .csv 或 .json 文件")
                sys.exit(1)

        else:
            students = collect_interactive()

        # 统计并输出
        result = analyze(students, pass_line=args.pass_line)
        print_report(result)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except (csv.Error, json.JSONDecodeError) as e:
        print(f"❌ 文件解析失败：{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        sys.exit(0)


if __name__ == "__main__":
    # Windows GBK 环境下强制 UTF-8 输出，避免 emoji 编码错误
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
