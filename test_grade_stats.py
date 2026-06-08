"""
学生成绩统计小工具 — 单元测试
==============================
覆盖：正常场景、边界条件、输入容错、文件解析。
"""

import csv
import json
import math
import os
import tempfile
import unittest

from grade_stats import (
    Student,
    StatsResult,
    analyze,
    get_max_score,
    get_min_score,
    get_average_score,
    read_csv,
    read_json,
    print_report,
    collect_interactive,
)


class TestStatistics(unittest.TestCase):
    """核心统计函数测试。"""

    def setUp(self):
        """构造共享测试数据。"""
        self.single = [Student("小明", 85)]
        self.normal = [
            Student("A", 90),
            Student("B", 80),
            Student("C", 70),
            Student("D", 60),
            Student("E", 50),
        ]  # 分数梯次分布，覆盖全部分段
        self.tie = [
            Student("甲", 90),
            Student("乙", 85),
            Student("丙", 90),
            Student("丁", 50),
            Student("戊", 50),
        ]  # 最高、最低均有并列

    # ── 1. 平均分 ────────────────────────────────────

    def test_average_normal(self):
        """正常情况：多人多分数。"""
        result = analyze(self.normal)
        self.assertAlmostEqual(result.average, 70.0)

    def test_average_single(self):
        """单人列表。"""
        result = analyze(self.single)
        self.assertEqual(result.average, 85.0)

    def test_average_all_same(self):
        """所有成绩相同时平均值等于该值。"""
        students = [Student("X", 100), Student("Y", 100), Student("Z", 100)]
        result = analyze(students)
        self.assertEqual(result.average, 100.0)

    # ── 2. 最高分 / 最低分 ───────────────────────────

    def test_max_min_unique(self):
        """唯一最高/最低。"""
        result = analyze(self.normal)
        self.assertEqual(result.max_student.score, 90)
        self.assertEqual(result.max_student.name, "A")
        self.assertEqual(result.min_student.score, 50)
        self.assertEqual(result.min_student.name, "E")
        self.assertEqual(len(result.ties_max), 1)
        self.assertEqual(len(result.ties_min), 1)

    def test_max_min_tie(self):
        """并列最高/最低。"""
        result = analyze(self.tie)
        self.assertEqual(result.max_student.score, 90)
        self.assertEqual(result.min_student.score, 50)
        self.assertEqual(len(result.ties_max), 2)
        self.assertEqual(len(result.ties_min), 2)
        tied_names = {s.name for s in result.ties_max}
        self.assertEqual(tied_names, {"甲", "丙"})

    # ── 3. 中位数 ────────────────────────────────────

    def test_median_odd(self):
        """奇数个学生。"""
        result = analyze(self.normal)  # 5 人：50,60,70,80,90 → 中位数 70
        self.assertEqual(result.median, 70.0)

    def test_median_even(self):
        """偶数个学生。"""
        students = [Student("A", 10), Student("B", 20), Student("C", 30), Student("D", 40)]
        result = analyze(students)  # 中位数 = (20+30)/2 = 25
        self.assertEqual(result.median, 25.0)

    # ── 4. 标准差 ────────────────────────────────────

    def test_std_dev_zero(self):
        """所有值相同时标准差为 0。"""
        students = [Student("X", 80), Student("Y", 80)]
        result = analyze(students)
        self.assertEqual(result.std_dev, 0.0)

    def test_std_dev_nonzero(self):
        """正常计算。"""
        result = analyze([Student("A", 0), Student("B", 100)])
        self.assertAlmostEqual(result.std_dev, 50.0)

    # ── 5. 及格率 ────────────────────────────────────

    def test_pass_rate_all_pass(self):
        """全部及格。"""
        result = analyze([Student("A", 60), Student("B", 80)], pass_line=60)
        self.assertEqual(result.pass_rate, 1.0)

    def test_pass_rate_all_fail(self):
        """全部不及格。"""
        result = analyze([Student("A", 59), Student("B", 30)], pass_line=60)
        self.assertEqual(result.pass_rate, 0.0)

    def test_pass_rate_custom_line(self):
        """自定义及格线。"""
        result = analyze([Student("A", 70), Student("B", 80)], pass_line=75)
        self.assertEqual(result.pass_rate, 0.5)

    # ── 6. 分数段分布 ───────────────────────────────

    def test_distribution(self):
        """各分段计数正确。"""
        result = analyze(self.normal)  # 90,80,70,60,50 — 每段各 1 人
        self.assertEqual(result.distribution["90-100"], 1)
        self.assertEqual(result.distribution["80-89"], 1)
        self.assertEqual(result.distribution["70-79"], 1)
        self.assertEqual(result.distribution["60-69"], 1)
        self.assertEqual(result.distribution["60以下"], 1)

    def test_distribution_all_top(self):
        """全部在最高分段。"""
        students = [Student("X", 95), Student("Y", 100)]
        result = analyze(students)
        self.assertEqual(result.distribution["90-100"], 2)
        self.assertEqual(sum(result.distribution.values()), 2)

    # ── 7. 空列表异常 ────────────────────────────────

    def test_analyze_empty(self):
        """空列表应抛出 ValueError。"""
        with self.assertRaises(ValueError):
            analyze([])

    # ── 8. 排序输出 ──────────────────────────────────

    def test_sorted_descending(self):
        """按成绩降序排列。"""
        result = analyze(self.normal)
        scores = [s.score for s in result.sorted_students]
        self.assertEqual(scores, [90, 80, 70, 60, 50])


class TestFileInput(unittest.TestCase):
    """文件读取（CSV / JSON）测试。"""

    def setUp(self):
        """创建临时目录用于测试文件。"""
        self.tmpdir = tempfile.mkdtemp()

    def _write(self, filename: str, content: str):
        """写入临时文件并返回路径。"""
        path = os.path.join(self.tmpdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    # ── CSV 测试 ─────────────────────────────────────

    def test_csv_normal(self):
        """正常 CSV 文件。"""
        path = self._write("scores.csv",
                           "name,score\n张三,85\n李四,92\n王五,78\n")
        students = read_csv(path)
        self.assertEqual(len(students), 3)
        self.assertEqual(students[0].name, "张三")
        self.assertEqual(students[0].score, 85.0)
        self.assertEqual(students[1].score, 92.0)

    def test_csv_no_header(self):
        """无表头 CSV。"""
        path = self._write("scores.csv", "张三,85\n李四,92\n")
        students = read_csv(path)
        self.assertEqual(len(students), 2)

    def test_csv_skip_invalid_rows(self):
        """跳过成绩无效的行。"""
        path = self._write("scores.csv",
                           "name,score\n张三,abc\n李四,92\n王五,\n")
        students = read_csv(path)
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "李四")

    def test_csv_score_out_of_range(self):
        """成绩超出 0~100 范围的行应跳过。"""
        path = self._write("scores.csv",
                           "张三,85\n李四,150\n王五,-10\n赵六,70\n")
        students = read_csv(path)
        self.assertEqual(len(students), 2)

    def test_csv_empty(self):
        """空文件抛出异常。"""
        path = self._write("scores.csv", "")
        with self.assertRaises(ValueError):
            read_csv(path)

    def test_csv_utf8_bom(self):
        """UTF-8 BOM 编码的 CSV。"""
        path = os.path.join(self.tmpdir, "scores.csv")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("name,score\n张三,85\n")
        students = read_csv(path)
        self.assertEqual(len(students), 1)

    # ── JSON 测试 ────────────────────────────────────

    def test_json_array(self):
        """JSON 对象数组格式。"""
        path = self._write("scores.json",
                           '[{"name":"张三","score":85},{"name":"李四","score":92}]')
        students = read_json(path)
        self.assertEqual(len(students), 2)
        self.assertEqual(students[0].name, "张三")

    def test_json_dict(self):
        """JSON 对象映射格式。"""
        path = self._write("scores.json", '{"张三":85,"李四":92}')
        students = read_json(path)
        self.assertEqual(len(students), 2)
        self.assertEqual(students[1].score, 92.0)

    def test_json_skip_invalid(self):
        """跳过无效条目。"""
        path = self._write("scores.json",
                           '[{"name":"张三","score":85},{"name":"李四"}]')
        students = read_json(path)
        self.assertEqual(len(students), 1)

    def test_json_malformed(self):
        """格式错误的 JSON。"""
        path = self._write("scores.json", "this is not json")
        with self.assertRaises(json.JSONDecodeError):
            read_json(path)

    def test_json_empty(self):
        """空 JSON 数组抛出异常。"""
        path = self._write("scores.json", "[]")
        with self.assertRaises(ValueError):
            read_json(path)

    def test_file_not_found(self):
        """文件不存在抛出异常。"""
        with self.assertRaises(FileNotFoundError):
            read_csv("/nonexistent/file.csv")


class TestLegacyAPI(unittest.TestCase):
    """旧版 API 兼容性测试（get_max_score 等独立函数）。"""

    def setUp(self):
        self.students = [Student("A", 90), Student("B", 80), Student("C", 70)]

    def test_get_max_score(self):
        self.assertEqual(get_max_score(self.students).name, "A")

    def test_get_min_score(self):
        self.assertEqual(get_min_score(self.students).name, "C")

    def test_get_average_score(self):
        self.assertAlmostEqual(get_average_score(self.students), 80.0)

    def test_legacy_empty(self):
        """旧 API 空列表也应抛异常。"""
        with self.assertRaises(ValueError):
            get_max_score([])


if __name__ == "__main__":
    unittest.main(verbosity=2)
