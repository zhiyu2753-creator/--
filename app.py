"""
学生成绩统计工具 — 原生 GUI 桌面应用
=====================================
基于 customtkinter，带启动动画、自适应布局、双击 exe 直接运行（无 CMD 窗口）。

用法：
    python app.py       # 开发运行
    build_exe.bat        # 打包成单文件 exe（--noconsole）
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Optional

# customtkinter 在 PyInstaller 打包后可能需要特殊处理
try:
    import customtkinter as ctk
except ImportError:
    import tkinter.ttk as ttk
    # 如果 customtkinter 未安装，回退到 tkinter
    print("⚠️ customtkinter 未安装，使用 tkinter 回退方案")
    ctk = None

# 复用核心模块
from grade_stats import (
    DEMO_STUDENTS,
    Student,
    StatsResult,
    analyze,
    get_max_score,
    get_min_score,
    get_average_score,
    read_csv,
    read_json,
)

# ── 常量 ──────────────────────────────────────────────────
APP_TITLE = "📊 学生成绩统计工具"
APP_GEOMETRY = "1200x750"
APP_MINSIZE = (860, 560)
FONT_FAMILY = ("Microsoft YaHei", "PingFang SC", "Segoe UI", "sans-serif")

# 暖色调主题色
COLORS = {
    "amber": "#D4743A",
    "amber_light": "#F0A065",
    "amber_pale": "#FDF0E5",
    "coral": "#C94F3A",
    "gold": "#B8860B",
    "gold_light": "#F4D35E",
    "cream": "#FEFAF4",
    "card": "#FFFFFF",
    "text": "#3D2C20",
    "text_soft": "#7A6858",
    "border": "#E8DDD2",
    "green": "#3D8B40",
    "green_bg": "#EDF7EE",
    "red": "#C62828",
    "red_bg": "#FDEDEC",
    "bg": "#F5F0EB",
}


# ═══════════════════════════════════════════════════════════
#  启动动画（Splash Screen）
# ═══════════════════════════════════════════════════════════

class SplashScreen:
    """应用启动时的动画加载窗口。"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)       # 无边框
        self.root.attributes("-topmost", True)  # 置顶

        # 窗口居中
        w, h = 420, 280
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # 圆角背景（通过 Canvas 模拟）
        self.canvas = tk.Canvas(
            self.root, width=w, height=h,
            bg=COLORS["cream"], highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 绘制圆角矩形背景
        self._draw_rounded_rect(w, h, 20)

        # 标题
        self.title_id = self.canvas.create_text(
            w // 2, 70,
            text="学生成绩统计工具",
            font=(FONT_FAMILY[0], 22, "bold"),
            fill=COLORS["text"],
            anchor="center",
        )

        # 图标
        self.icon_id = self.canvas.create_text(
            w // 2, 130,
            text="📊",
            font=("Segoe UI Emoji", 40),
            anchor="center",
        )

        # 加载条背景
        bar_x1, bar_y1 = 60, 180
        bar_x2, bar_y2 = w - 60, 196
        self.canvas.create_rectangle(
            bar_x1, bar_y1, bar_x2, bar_y2,
            fill=COLORS["border"],
            outline="",
            tags="bar_bg",
        )

        # 加载条前景（动画）
        self.bar_fg = self.canvas.create_rectangle(
            bar_x1, bar_y1, bar_x1 + 6, bar_y2,
            fill=COLORS["amber"],
            outline="",
            tags="bar_fg",
        )
        self.bar_x1 = bar_x1
        self.bar_x2 = bar_x2
        self.bar_y1 = bar_y1
        self.bar_y2 = bar_y2

        # 进度文字
        self.pct_id = self.canvas.create_text(
            w // 2, 220,
            text="加载中...",
            font=(FONT_FAMILY[0], 11),
            fill=COLORS["text_soft"],
            anchor="center",
        )

        # 加载提示
        self.tip_id = self.canvas.create_text(
            w // 2, 250,
            text="",
            font=(FONT_FAMILY[0], 9),
            fill=COLORS["text_soft"],
            anchor="center",
        )

        self.progress = 0
        self._animate()

    def _draw_rounded_rect(self, w, h, r):
        """绘制圆角矩形背景。"""
        self.canvas.create_rectangle(r, 0, w - r, h, fill=COLORS["cream"], outline="")
        self.canvas.create_rectangle(0, r, w, h - r, fill=COLORS["cream"], outline="")
        self.canvas.create_oval(0, 0, r * 2, r * 2, fill=COLORS["cream"], outline="")
        self.canvas.create_oval(w - r * 2, 0, w, r * 2, fill=COLORS["cream"], outline="")
        self.canvas.create_oval(0, h - r * 2, r * 2, h, fill=COLORS["cream"], outline="")
        self.canvas.create_oval(w - r * 2, h - r * 2, w, h, fill=COLORS["cream"], outline="")

    def _animate(self):
        """逐帧动画：进度条前进 + 提示文字轮换。"""
        tips = ["加载界面组件...", "初始化数据模型...", "准备统计引擎...", "启动完成 ✓"]
        self.progress += 1.8

        if self.progress < 99:
            width = self.bar_x1 + (self.bar_x2 - self.bar_x1) * (self.progress / 100)
            self.canvas.coords(
                self.bar_fg,
                self.bar_x1, self.bar_y1, width, self.bar_y2
            )
            self.canvas.itemconfig(
                self.pct_id,
                text=f"{int(self.progress)}%",
            )
            tip_idx = min(int(self.progress / 25), len(tips) - 1)
            self.canvas.itemconfig(self.tip_id, text=tips[tip_idx])
            self.root.after(30, self._animate)
        else:
            # 动画完成，关闭 splash
            self.canvas.coords(
                self.bar_fg,
                self.bar_x1, self.bar_y1, self.bar_x2, self.bar_y2
            )
            self.canvas.itemconfig(self.pct_id, text="100%")
            self.root.after(200, self._finish)

    def _finish(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
#  主应用窗口
# ═══════════════════════════════════════════════════════════

class GradeStatsApp:
    """学生成绩统计主窗口 —— 原生 GUI 桌面应用。"""

    def __init__(self):
        # ── 根窗口配置 ──
        if ctk is not None:
            ctk.set_appearance_mode("Light")
            ctk.set_default_color_theme("green")
            self.root = ctk.CTk()
            # 自定义暖色调主题
            self._apply_warm_theme()
        else:
            self.root = tk.Tk()
            self.root.tk.call("tk", "scaling", 1.3)  # 高 DPI

        self.root.title(APP_TITLE)
        self.root.minsize(*APP_MINSIZE)
        self._center_window()

        # 绑定窗口大小变化 → 自适应字体和布局
        self.root.bind("<Configure>", self._on_resize)

        # ── 状态变量 ──
        self.students: List[Student] = []
        self.pass_line = 60.0
        self._resize_job: Optional[str] = None  # 防抖 ID

        # ── 构建 UI ──
        self._build_header()
        self._build_main_area()
        self._build_statusbar()

        # 初始状态：空数据
        self._refresh_all()

    # ── 主题配置 ───────────────────────────────────────

    def _apply_warm_theme(self):
        """覆盖 customtkinter 默认主题色为暖色调。"""
        # 注意：customtkinter 5.x 不支持直接的 theme JSON，用控件级别的 color 参数替代
        pass

    # ── 窗口居中 ───────────────────────────────────────

    def _center_window(self):
        """窗口居中显示。"""
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        # 使用默认大小
        w = max(w, 1200)
        h = max(h, 750)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── 响应式布局 ─────────────────────────────────────

    def _on_resize(self, event):
        """窗口大小变化时自适应调整（防抖）。"""
        if event.widget != self.root:
            return
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(150, self._apply_responsive)

    def _apply_responsive(self):
        """根据当前窗口尺寸调整字体大小和元素。"""
        width = self.root.winfo_width()
        # 动态调整全局字体
        base_size = 13 if width > 1100 else (12 if width > 900 else 11)
        # 更新统计卡片的字号
        if hasattr(self, "stat_font_size"):
            self.stat_font_size = base_size
        self._resize_job = None

    # ═══════════════════════════════════════════════════════
    #  顶部标题栏
    # ═══════════════════════════════════════════════════════

    def _build_header(self):
        """构建顶部标题和操作栏。"""
        header = self._frame(self.root, fg_color=COLORS["card"], height=56)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # 标题
        self._label(
            header, text=APP_TITLE,
            font=(FONT_FAMILY[0], 16, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=20, pady=12)

        # 右侧按钮
        btn_frame = self._frame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=12, pady=10)

        self._btn(btn_frame, text="📥 导入文件", command=self._import_file,
                  fg_color=COLORS["amber_pale"], text_color=COLORS["amber"],
                  hover_color=COLORS["border"]).pack(side="left", padx=4)

        self._btn(btn_frame, text="🎬 演示数据", command=self._load_demo,
                  fg_color=COLORS["amber"], text_color="white",
                  hover_color=COLORS["coral"]).pack(side="left", padx=4)

        # 分隔线
        sep = self._frame(self.root, fg_color=COLORS["border"], height=1)
        sep.pack(fill="x")

    # ═══════════════════════════════════════════════════════
    #  主内容区（左右双栏）
    # ═══════════════════════════════════════════════════════

    def _build_main_area(self):
        """构建主内容区：左侧录入 + 右侧统计，使用 PanedWindow 可拖拽分界。"""
        self.main_pane = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL,
            bg=COLORS["bg"], bd=0, sashwidth=4, sashrelief="flat",
        )
        self.main_pane.pack(fill="both", expand=True, padx=0, pady=0)

        # ── 左侧面板 ──
        self.left_frame = self._frame(self.main_pane, fg_color=COLORS["bg"])
        self._build_input_panel(self.left_frame)

        # ── 右侧面板 ──
        self.right_frame = self._frame(self.main_pane, fg_color=COLORS["bg"])
        self._build_stats_panel(self.right_frame)

        self.main_pane.add(self.left_frame, minsize=340, width=400)
        self.main_pane.add(self.right_frame, minsize=460, width=700)

    # ── 左侧：录入面板 ──────────────────────────────────

    def _build_input_panel(self, parent):
        """构建左侧录入区域。"""
        container = self._frame(parent, fg_color=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=14, pady=10)

        # 录入卡片
        card = self._card(container)
        card.pack(fill="both", expand=True)

        self._label(card, text="📝 录入成绩", font=(FONT_FAMILY[0], 14, "bold"),
                    text_color=COLORS["text"]).pack(anchor="w", padx=16, pady=(14, 10))

        # 输入框行
        input_row = self._frame(card, fg_color="transparent")
        input_row.pack(fill="x", padx=16)

        self.name_entry = self._entry(input_row, placeholder_text="输入姓名",
                                      width=140)
        self.name_entry.pack(side="left", padx=(0, 8))
        self.name_entry.bind("<Return>", lambda e: self.score_entry.focus_set())

        self.score_entry = self._entry(input_row, placeholder_text="成绩",
                                       width=80)
        self.score_entry.pack(side="left", padx=(0, 8))
        self.score_entry.bind("<Return>", lambda e: self._add_student())

        self._btn(input_row, text="➕ 添加", command=self._add_student,
                  fg_color=COLORS["amber"], text_color="white",
                  hover_color=COLORS["coral"], height=34).pack(side="left")

        # 及格线滑块
        slider_row = self._frame(card, fg_color="transparent")
        slider_row.pack(fill="x", padx=16, pady=(10, 6))

        self._label(slider_row, text="及格线：",
                    font=(FONT_FAMILY[0], 11),
                    text_color=COLORS["text_soft"]).pack(side="left")

        self.pass_var = tk.IntVar(value=60)
        self.pass_slider = self._slider(
            slider_row, from_=0, to=100, variable=self.pass_var,
            command=self._on_pass_change, width=120,
        )
        self.pass_slider.pack(side="left", padx=6)

        self.pass_label = self._label(
            slider_row, text="60 分",
            font=(FONT_FAMILY[0], 12, "bold"),
            text_color=COLORS["amber"],
        )
        self.pass_label.pack(side="left")

        # 学生列表标题
        list_header = self._frame(card, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(10, 4))
        self._label(list_header, text="👥 学生列表",
                    font=(FONT_FAMILY[0], 12, "bold"),
                    text_color=COLORS["text"]).pack(side="left")
        self.count_label = self._label(list_header, text="0 人",
                                       font=(FONT_FAMILY[0], 11),
                                       text_color=COLORS["text_soft"])
        self.count_label.pack(side="right")

        # 学生列表（可滚动的 Treeview 或 Listbox）
        list_frame = self._frame(card, fg_color=COLORS["cream"],
                                 corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # 使用 tkinter Treeview 做表格（customtkinter 没有 Treeview）
        columns = ("#", "name", "score", "action")
        self.tree = tk.ttk.Treeview(
            list_frame, columns=columns, show="headings",
            height=12,
        )
        self.tree.heading("#", text="#")
        self.tree.heading("name", text="姓名")
        self.tree.heading("score", text="成绩")
        self.tree.heading("action", text="")

        self.tree.column("#", width=36, anchor="center", stretch=False)
        self.tree.column("name", width=100, anchor="w")
        self.tree.column("score", width=60, anchor="center", stretch=False)
        self.tree.column("action", width=40, anchor="center", stretch=False)

        # 样式
        style = tk.ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=COLORS["cream"],
            fieldbackground=COLORS["cream"],
            foreground=COLORS["text"],
            rowheight=30,
            font=(FONT_FAMILY[0], 11),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["amber_pale"],
            foreground=COLORS["amber"],
            font=(FONT_FAMILY[0], 10, "bold"),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", COLORS["amber_pale"])],
                  foreground=[("selected", COLORS["text"])])

        # 滚动条
        scrollbar = tk.ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)

        # 双击编辑
        self.tree.bind("<Double-1>", self._edit_student)

        # 底部操作按钮
        btn_row = self._frame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 14))

        self._btn(btn_row, text="🗑 清空", command=self._clear_all,
                  fg_color="transparent", text_color=COLORS["text_soft"],
                  border_color=COLORS["border"], border_width=1.5,
                  hover_color=COLORS["red_bg"]).pack(side="left", padx=(0, 6))

        self._btn(btn_row, text="💾 导出 CSV", command=self._export_csv,
                  fg_color="transparent", text_color=COLORS["text_soft"],
                  border_color=COLORS["border"], border_width=1.5,
                  hover_color=COLORS["amber_pale"]).pack(side="left")

        self._btn(btn_row, text="✕ 删除选中", command=self._delete_selected,
                  fg_color="transparent", text_color=COLORS["red"],
                  border_color=COLORS["red_bg"], border_width=1.5,
                  hover_color=COLORS["red_bg"]).pack(side="right")

    # ── 右侧：统计面板 ──────────────────────────────────

    def _build_stats_panel(self, parent):
        """构建右侧统计展示区域。"""
        container = self._frame(parent, fg_color=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=14, pady=10)

        # ── 统计卡片网格 ──
        grid_frame = self._frame(container, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat_col")

        self.stat_cards = {}
        stat_specs = [
            ("stat_max", "🥇 最高分", COLORS["amber_pale"], COLORS["amber"]),
            ("stat_min", "🥈 最低分", COLORS["red_bg"], COLORS["red"]),
            ("stat_avg", "📊 平均分", COLORS["cream"], COLORS["text"]),
            ("stat_med", "📐 中位数", COLORS["cream"], COLORS["text"]),
            ("stat_std", "📏 标准差", COLORS["cream"], COLORS["text"]),
            ("stat_pass", "✅ 及格率", COLORS["green_bg"], COLORS["green"]),
        ]

        for i, (key, label, bg, fg) in enumerate(stat_specs):
            row, col = i // 3, i % 3
            card = self._stat_card(grid_frame, label, "", "", bg, fg)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.stat_cards[key] = card

        # ── 分布 + 排名（可滚动） ──
        bottom = self._frame(container, fg_color="transparent")
        bottom.pack(fill="both", expand=True, pady=(8, 0))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)

        # 分数段分布
        dist_card = self._card(bottom)
        dist_card.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        self._label(dist_card, text="📈 分数段分布",
                    font=(FONT_FAMILY[0], 13, "bold"),
                    text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(12, 8))

        self.dist_bars = {}
        segs = [
            ("90-100", COLORS["gold_light"]),
            ("80-89", COLORS["amber_light"]),
            ("70-79", "#D4946A"),
            ("60-69", "#B8846A"),
            ("<60", "#D49494"),
        ]
        for label, color in segs:
            bar_frame = self._frame(dist_card, fg_color="transparent")
            bar_frame.pack(fill="x", padx=14, pady=3)

            self._label(bar_frame, text=label,
                        font=(FONT_FAMILY[0], 10),
                        text_color=COLORS["text_soft"],
                        width=5).pack(side="left")

            bar_bg = tk.Frame(bar_frame, bg=COLORS["cream"], height=18)
            bar_bg.pack(side="left", fill="x", expand=True, padx=6)
            bar_bg.pack_propagate(False)

            bar_fg = tk.Frame(bar_bg, bg=color, height=18)
            bar_fg.place(x=0, y=0, relheight=1.0, width=0)

            cnt_lbl = self._label(bar_frame, text="0",
                                  font=(FONT_FAMILY[0], 10, "bold"),
                                  text_color=COLORS["text"],
                                  width=3)
            cnt_lbl.pack(side="left")

            self.dist_bars[label] = (bar_fg, cnt_lbl)

        # 成绩排名
        rank_card = self._card(bottom)
        rank_card.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        self._label(rank_card, text="🏆 成绩排名",
                    font=(FONT_FAMILY[0], 13, "bold"),
                    text_color=COLORS["text"]).pack(anchor="w", padx=14, pady=(12, 8))

        # 可滚动排名
        rank_list_frame = self._frame(rank_card, fg_color=COLORS["cream"],
                                      corner_radius=8)
        rank_list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.rank_canvas = tk.Canvas(
            rank_list_frame, bg=COLORS["cream"],
            highlightthickness=0, bd=0,
        )
        rank_scroll = tk.ttk.Scrollbar(rank_list_frame, orient="vertical",
                                       command=self.rank_canvas.yview)
        self.rank_inner = self._frame(self.rank_canvas, fg_color="transparent")

        self.rank_inner.bind("<Configure>",
                             lambda e: self.rank_canvas.configure(
                                 scrollregion=self.rank_canvas.bbox("all")))

        self.rank_canvas.create_window((0, 0), window=self.rank_inner, anchor="nw",
                                       tags="rank_window")
        self.rank_canvas.configure(yscrollcommand=rank_scroll.set)

        self.rank_canvas.pack(side="left", fill="both", expand=True)
        rank_scroll.pack(side="right", fill="y")

        # Canvas 宽度自适应
        self.rank_canvas.bind("<Configure>", lambda e: self.rank_canvas.itemconfig(
            "rank_window", width=e.width))

    def _stat_card(self, parent, label, value, sub, bg_color, value_color):
        """创建一个统计指标卡片。"""
        card = self._frame(parent, fg_color=bg_color, corner_radius=10)
        inner = self._frame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        lbl = self._label(inner, text=label,
                          font=(FONT_FAMILY[0], 10),
                          text_color=COLORS["text_soft"])
        lbl.pack()

        val = self._label(inner, text="—",
                          font=(FONT_FAMILY[0], 22, "bold"),
                          text_color=value_color)
        val.pack()

        sub_lbl = self._label(inner, text="",
                              font=(FONT_FAMILY[0], 9),
                              text_color=COLORS["text_soft"])
        sub_lbl.pack()

        # 存引用以便更新
        card._val_label = val
        card._sub_label = sub_lbl
        return card

    # ═══════════════════════════════════════════════════════
    #  底部状态栏
    # ═══════════════════════════════════════════════════════

    def _build_statusbar(self):
        """构建底部状态栏。"""
        bar = self._frame(self.root, fg_color=COLORS["card"], height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_label = self._label(
            bar, text="✅ 就绪",
            font=(FONT_FAMILY[0], 10),
            text_color=COLORS["text_soft"],
        )
        self.status_label.pack(side="left", padx=16)

        self.total_label = self._label(
            bar, text="学生总数：0 人",
            font=(FONT_FAMILY[0], 10),
            text_color=COLORS["text_soft"],
        )
        self.total_label.pack(side="right", padx=16)

    # ═══════════════════════════════════════════════════════
    #  业务逻辑
    # ═══════════════════════════════════════════════════════

    def _add_student(self):
        """添加一名学生。"""
        name = self.name_entry.get().strip()
        score_str = self.score_entry.get().strip()

        if not name:
            messagebox.showwarning("提示", "请输入学生姓名")
            self.name_entry.focus_set()
            return
        if not score_str:
            messagebox.showwarning("提示", "请输入成绩")
            self.score_entry.focus_set()
            return

        try:
            score = float(score_str)
        except ValueError:
            messagebox.showwarning("提示", "成绩必须是数字")
            self.score_entry.focus_set()
            return

        if score < 0 or score > 100:
            messagebox.showwarning("提示", "成绩应在 0~100 之间")
            self.score_entry.focus_set()
            return

        self.students.append(Student(name=name, score=score))
        self.name_entry.delete(0, "end")
        self.score_entry.delete(0, "end")
        self.name_entry.focus_set()
        self._refresh_all()
        self._set_status(f"✅ 已添加：{name}（{score} 分）")

    def _delete_selected(self):
        """删除选中的学生。"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在左侧列表中点击选中要删除的学生")
            return
        # 获取选中行的索引
        item = self.tree.item(sel[0])
        idx = int(item["values"][0]) - 1
        if 0 <= idx < len(self.students):
            name = self.students[idx].name
            del self.students[idx]
            self._refresh_all()
            self._set_status(f"🗑 已删除：{name}")

    def _edit_student(self, event):
        """双击编辑学生。"""
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        idx = int(item["values"][0]) - 1
        if 0 <= idx < len(self.students):
            s = self.students[idx]

            # 弹出简单编辑对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("编辑学生")
            dialog.geometry("280x160")
            dialog.transient(self.root)
            dialog.grab_set()
            # 居中
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - 280) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - 160) // 2
            dialog.geometry(f"+{x}+{y}")

            tk.Label(dialog, text="姓名：", font=(FONT_FAMILY[0], 11)).pack(pady=(14, 2))
            name_entry = tk.Entry(dialog, font=(FONT_FAMILY[0], 11), width=24)
            name_entry.insert(0, s.name)
            name_entry.pack()

            tk.Label(dialog, text="成绩：", font=(FONT_FAMILY[0], 11)).pack(pady=(6, 2))
            score_entry = tk.Entry(dialog, font=(FONT_FAMILY[0], 11), width=24)
            score_entry.insert(0, str(s.score))
            score_entry.pack()

            def save():
                new_name = name_entry.get().strip()
                new_score_str = score_entry.get().strip()
                if not new_name:
                    messagebox.showwarning("提示", "姓名不能为空", parent=dialog)
                    return
                try:
                    new_score = float(new_score_str)
                except ValueError:
                    messagebox.showwarning("提示", "成绩必须是数字", parent=dialog)
                    return
                if new_score < 0 or new_score > 100:
                    messagebox.showwarning("提示", "成绩应在 0~100 之间", parent=dialog)
                    return
                self.students[idx] = Student(name=new_name, score=new_score)
                dialog.destroy()
                self._refresh_all()
                self._set_status(f"✏️ 已修改：{new_name}（{new_score} 分）")

            tk.Button(dialog, text="💾 保存", command=save,
                      bg=COLORS["amber"], fg="white", font=(FONT_FAMILY[0], 11),
                      borderwidth=0, padx=20, pady=4, cursor="hand2").pack(pady=12)

            score_entry.bind("<Return>", lambda e: save())
            score_entry.focus_set()
            score_entry.selection_range(0, "end")

    def _clear_all(self):
        """清空所有学生数据。"""
        if not self.students:
            return
        if messagebox.askyesno("确认", f"确定要清空全部 {len(self.students)} 名学生吗？"):
            self.students.clear()
            self._refresh_all()
            self._set_status("🗑 已清空全部数据")

    def _load_demo(self):
        """加载演示数据。"""
        self.students = list(DEMO_STUDENTS)
        self.pass_var.set(60)
        self._refresh_all()
        self._set_status("🎬 已加载 8 条演示数据")

    def _import_file(self):
        """导入 CSV / JSON 文件。"""
        path = filedialog.askopenfilename(
            title="选择学生数据文件",
            filetypes=[
                ("CSV / JSON 文件", "*.csv;*.json"),
                ("CSV 文件", "*.csv"),
                ("JSON 文件", "*.json"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return

        try:
            ext = Path(path).suffix.lower()
            if ext == ".csv":
                imported = read_csv(path)
            elif ext == ".json":
                imported = read_json(path)
            else:
                messagebox.showerror("错误", f"不支持的文件格式「{ext}」")
                return

            self.students = imported
            self._refresh_all()
            self._set_status(f"📥 已导入 {len(imported)} 名学生（来源：{Path(path).name}）")

        except (ValueError, FileNotFoundError) as e:
            messagebox.showerror("导入失败", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"文件解析失败：{e}")

    def _export_csv(self):
        """导出为 CSV 文件。"""
        if not self.students:
            messagebox.showinfo("提示", "暂无数据可导出")
            return

        path = filedialog.asksaveasfilename(
            title="导出 CSV",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile="学生成绩.csv",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["姓名", "成绩"])
                for s in self.students:
                    writer.writerow([s.name, s.score])
            self._set_status(f"💾 已导出 {len(self.students)} 条记录 → {Path(path).name}")
            messagebox.showinfo("导出成功", f"已导出 {len(self.students)} 名学生到：\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _on_pass_change(self, val):
        """及格线滑块变化时刷新。"""
        self.pass_line = float(val)
        self.pass_label.configure(text=f"{int(self.pass_line)} 分")
        self._refresh_all()

    # ═══════════════════════════════════════════════════════
    #  刷新 UI
    # ═══════════════════════════════════════════════════════

    def _refresh_all(self):
        """完全刷新所有 UI：学生列表 + 统计面板。"""
        self._refresh_student_list()
        self._refresh_stats()

    def _refresh_student_list(self):
        """刷新左侧学生列表表格。"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.count_label.configure(text=f"{len(self.students)} 人")

        for i, s in enumerate(self.students):
            status = "✅" if s.score >= self.pass_line else "⚠️"
            self.tree.insert("", "end", values=(i + 1, f"  {s.name}", f"{s.score} {status}", "✕"))

    def _refresh_stats(self):
        """刷新右侧统计面板。"""
        if not self.students:
            self._show_empty_stats()
            self.total_label.configure(text="学生总数：0 人")
            return

        try:
            result = analyze(self.students, pass_line=self.pass_line)
        except ValueError:
            self._show_empty_stats()
            return

        # 统计卡片
        self._update_stat_card("stat_max",
                               str(result.max_student.score),
                               result.ties_max[0].name if len(result.ties_max) == 1
                               else f"{len(result.ties_max)}人并列")

        self._update_stat_card("stat_min",
                               str(result.min_student.score),
                               result.ties_min[0].name if len(result.ties_min) == 1
                               else f"{len(result.ties_min)}人并列")

        self._update_stat_card("stat_avg", f"{result.average:.2f}")
        self._update_stat_card("stat_med", f"{result.median:.2f}")
        self._update_stat_card("stat_std", f"{result.std_dev:.2f}")
        self._update_stat_card("stat_pass",
                               f"{result.pass_rate:.1%}",
                               f"{int(result.pass_rate * result.count)}/{result.count}")

        # 分布柱状图
        max_cnt = max(result.distribution.values()) if result.distribution else 1
        for label, (bar, cnt_lbl) in self.dist_bars.items():
            key = "60以下" if label == "<60" else label
            cnt = result.distribution.get(key, 0)
            cnt_lbl.configure(text=f"{cnt}")
            pct = cnt / max_cnt if max_cnt > 0 else 0
            bar.place_configure(width=int(pct * 140))  # 动态宽度

        # 排名列表
        for widget in self.rank_inner.winfo_children():
            widget.destroy()

        for i, s in enumerate(result.sorted_students):
            row = self._frame(self.rank_inner, fg_color="transparent")
            row.pack(fill="x", padx=0, pady=2)

            # 排名序号
            rank_color = COLORS["gold_light"] if i < 3 else COLORS["amber_pale"]
            rank_frame = tk.Frame(row, bg=rank_color, width=28, height=28)
            rank_frame.pack(side="left", padx=(8, 8))
            rank_frame.pack_propagate(False)
            tk.Label(rank_frame, text=str(i + 1),
                     bg=rank_color, fg=COLORS["text"],
                     font=(FONT_FAMILY[0], 10, "bold")).pack(expand=True)

            # 姓名
            tk.Label(row, text=s.name,
                     bg=COLORS["cream"], fg=COLORS["text"],
                     font=(FONT_FAMILY[0], 11), anchor="w").pack(
                side="left", fill="x", expand=True)

            # 成绩
            tk.Label(row, text=str(s.score),
                     bg=COLORS["cream"], fg=COLORS["amber"],
                     font=(FONT_FAMILY[0], 11, "bold"), width=6, anchor="e").pack(
                side="right", padx=(0, 8))

        self.total_label.configure(text=f"学生总数：{result.count} 人")

    def _update_stat_card(self, key, value, sub=""):
        """更新单个统计卡片的值。"""
        card = self.stat_cards.get(key)
        if card:
            card._val_label.configure(text=value)
            card._sub_label.configure(text=sub)

    def _show_empty_stats(self):
        """重置统计面板为空状态。"""
        for key in self.stat_cards:
            self._update_stat_card(key, "—")
        for label, (bar, cnt_lbl) in self.dist_bars.items():
            cnt_lbl.configure(text="0")
            bar.place_configure(width=0)
        for widget in self.rank_inner.winfo_children():
            widget.destroy()
        tk.Label(self.rank_inner, text="添加学生后\n显示排名",
                 bg=COLORS["cream"], fg=COLORS["text_soft"],
                 font=(FONT_FAMILY[0], 11)).pack(expand=True)
        self.total_label.configure(text="学生总数：0 人")

    def _set_status(self, text):
        """更新底部状态文字。"""
        self.status_label.configure(text=text)

    # ═══════════════════════════════════════════════════════
    #  Widget 工厂方法（统一创建路径）
    # ═══════════════════════════════════════════════════════

    def _frame(self, parent, **kw):
        if ctk is not None:
            return ctk.CTkFrame(parent, **kw)
        return tk.Frame(parent, **{k: v for k, v in kw.items()
                                   if k in ("bg", "height", "width")})

    def _label(self, parent, text="", font=None, text_color=None, width=None, **kw):
        if ctk is not None:
            font_kw = {}
            if font:
                font_kw = {"font": (font[0], font[1]),
                            "text_color": text_color or COLORS["text"]}
            return ctk.CTkLabel(parent, text=text, width=width or 0, **font_kw, **kw)
        fg = text_color or COLORS["text"]
        bg = parent.cget("bg") if hasattr(parent, "cget") else COLORS["cream"]
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg,
                        width=width or 0, **kw)

    def _btn(self, parent, text="", command=None, fg_color=None,
             text_color=None, hover_color=None, border_color=None,
             border_width=0, height=32, **kw):
        if ctk is not None:
            # customtkinter 不允许 "transparent" 作为按钮颜色，需转换为实际颜色
            btn_fg = fg_color if fg_color and fg_color != "transparent" else COLORS["card"]
            btn_hover = hover_color if hover_color else COLORS["coral"]
            btn_border = border_color if border_color and border_color != "transparent" else btn_fg
            return ctk.CTkButton(
                parent, text=text, command=command,
                fg_color=btn_fg,
                text_color=text_color or "white" if btn_fg == COLORS["amber"] else text_color or COLORS["text_soft"],
                hover_color=btn_hover,
                border_color=btn_border,
                border_width=border_width,
                height=height,
                font=(FONT_FAMILY[0], 11),
                corner_radius=8,
                **kw,
            )
        btn = tk.Button(parent, text=text, command=command,
                        bg=fg_color or COLORS["amber"],
                        fg=text_color or "white",
                        font=(FONT_FAMILY[0], 11),
                        borderwidth=border_width, padx=12, pady=4,
                        cursor="hand2", **kw)
        if hover_color:
            btn.bind("<Enter>", lambda e: btn.configure(bg=hover_color))
            if fg_color:
                btn.bind("<Leave>", lambda e: btn.configure(bg=fg_color))
        return btn

    def _entry(self, parent, placeholder_text="", width=140, **kw):
        if ctk is not None:
            return ctk.CTkEntry(
                parent, placeholder_text=placeholder_text, width=width,
                font=(FONT_FAMILY[0], 12),
                fg_color=COLORS["cream"],
                text_color=COLORS["text"],
                border_color=COLORS["border"],
                corner_radius=8,
                height=34,
                **kw,
            )
        entry = tk.Entry(parent, font=(FONT_FAMILY[0], 12), width=width // 8,
                         bg=COLORS["cream"], fg=COLORS["text"], bd=1,
                         relief="solid", **kw)
        if placeholder_text:
            entry.insert(0, placeholder_text)
            entry.bind("<FocusIn>", lambda e: entry.delete(0, "end")
                       if entry.get() == placeholder_text else None)
            entry.bind("<FocusOut>", lambda e: entry.insert(0, placeholder_text)
                       if not entry.get() else None)
        return entry

    def _slider(self, parent, from_=0, to=100, variable=None, command=None,
                width=120, **kw):
        if ctk is not None:
            return ctk.CTkSlider(
                parent, from_=from_, to=to, variable=variable,
                command=command, width=width,
                progress_color=COLORS["amber"],
                button_color=COLORS["amber"],
                button_hover_color=COLORS["coral"],
                **kw,
            )
        return tk.Scale(parent, from_=from_, to=to, variable=variable,
                        command=command, orient="horizontal", length=width,
                        bg=COLORS["cream"], fg=COLORS["text"],
                        troughcolor=COLORS["border"],
                        highlightthickness=0, **kw)

    def _card(self, parent, **kw):
        """创建带圆角和阴影效果的卡片。"""
        defaults = {"fg_color": COLORS["card"], "corner_radius": 12}
        defaults.update(kw)
        return self._frame(parent, **defaults)

    # ═══════════════════════════════════════════════════════
    #  启动
    # ═══════════════════════════════════════════════════════

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════

def main():
    """启动应用：先显示启动动画，再打开主窗口。"""
    # 阶段 1：Splash 动画
    splash = SplashScreen()
    splash.run()  # 阻塞直到动画完成

    # 阶段 2：主窗口
    app = GradeStatsApp()
    app.root.lift()
    app.root.focus_force()
    app.run()


if __name__ == "__main__":
    # Windows 无控制台时 stdout/stderr 可能不可用
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    main()
