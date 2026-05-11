"""
手写数字采样工具
---------------
用鼠标在画布上写数字，生成 28x28 灰度图片。
支持导出为 PNG 图片和文本格式（兼容 C 推理程序）。

使用方式:
    python sampling.py

操作:
    - 鼠标左键拖拽: 书写
    - 鼠标右键拖拽: 擦除
    - 滚轮: 调整笔刷大小
    - 按 'c': 清空画布
    - 按 's': 保存为 PNG (samples/drawn_000.png)
    - 按 't': 保存为文本 (samples/drawn_000.txt)
    - 按 'p': 用当前训练的 MLP 模型预测
    - 按 'q' 或关闭窗口: 退出
"""

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.backend_bases import MouseButton
import os
import glob

# ── CJK 字体配置（解决 matplotlib 中文显示问题）──
_cjk_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(_cjk_path):
    fm.fontManager.addfont(_cjk_path)
    _prop = fm.FontProperties(fname=_cjk_path)
    _font_name = _prop.get_name()
    plt.rcParams["font.family"] = _font_name
    plt.rcParams["axes.unicode_minus"] = False

# ── 画布参数 ──
CANVAS_SIZE = 280   # 画布像素 (280x280)，方便书写
OUTPUT_SIZE = 28    # 输出尺寸 (28x28)
BRUSH_SIZE = 16     # 默认笔刷半径


class DigitSampler:
    def __init__(self):
        self.canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.float32)
        self.brush_size = BRUSH_SIZE
        self.drawing = False
        self.erasing = False
        self._save_counter = self._find_next_counter()

        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.fig.canvas.manager.set_window_title(
            "手写数字采样 — 左键书写/右键擦除/s保存/p预测/q退出"
        )
        self.img = self.ax.imshow(self.canvas, cmap="gray", vmin=0, vmax=1)
        self._update_title()
        self.ax.axis("off")

        # 绑定事件
        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.fig.canvas.mpl_connect("close_event", self.on_close)

    # ── 自动编号 ──

    def _find_next_counter(self) -> int:
        """扫描 samples/ 目录，找到下一个可用编号。"""
        os.makedirs("samples", exist_ok=True)
        existing = glob.glob("samples/drawn_[0-9][0-9][0-9].png")
        existing += glob.glob("samples/drawn_[0-9][0-9][0-9].txt")
        if not existing:
            return 0
        nums = []
        for path in existing:
            basename = os.path.basename(path)
            try:
                num = int(basename.split("_")[1].split(".")[0])
                nums.append(num)
            except (IndexError, ValueError):
                pass
        return max(nums) + 1 if nums else 0

    # ── 鼠标事件 ──

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == MouseButton.LEFT:
            self.drawing = True
            self._draw_point(event.xdata, event.ydata)
        elif event.button == MouseButton.RIGHT:
            self.erasing = True
            self._erase_point(event.xdata, event.ydata)

    def on_release(self, event):
        self.drawing = False
        self.erasing = False

    def on_motion(self, event):
        if not (self.drawing or self.erasing):
            return
        if event.inaxes != self.ax:
            return
        if self.drawing:
            self._draw_point(event.xdata, event.ydata)
        elif self.erasing:
            self._erase_point(event.xdata, event.ydata)

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == "up":
            self.brush_size = min(60, self.brush_size + 2)
        else:
            self.brush_size = max(4, self.brush_size - 2)
        self._update_title()

    def on_key(self, event):
        if event.key == "c":
            self.canvas.fill(0)
            self.img.set_data(self.canvas)
            self.fig.canvas.draw_idle()
            print("画布已清空")
        elif event.key == "s":
            self.save_png()
        elif event.key == "t":
            self.save_text()
        elif event.key == "p":
            self.predict()
        elif event.key == "q":
            plt.close(self.fig)

    def on_close(self, event):
        print("退出采样工具")

    # ── 绘制逻辑 ──

    def _draw_point(self, x, y):
        """在 (x,y) 位置画一个圆形笔触，高斯衰减让边缘柔和。"""
        yy, xx = np.ogrid[:CANVAS_SIZE, :CANVAS_SIZE]
        dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        mask = dist <= self.brush_size
        falloff = np.exp(-0.5 * (dist[mask] / (self.brush_size * 0.5)) ** 2)
        self.canvas[mask] = np.maximum(self.canvas[mask], falloff)
        self.img.set_data(self.canvas)
        self.fig.canvas.draw_idle()

    def _erase_point(self, x, y):
        """在 (x,y) 位置擦除。"""
        yy, xx = np.ogrid[:CANVAS_SIZE, :CANVAS_SIZE]
        dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        mask = dist <= self.brush_size
        self.canvas[mask] = 0
        self.img.set_data(self.canvas)
        self.fig.canvas.draw_idle()

    def _update_title(self):
        self.ax.set_title(
            f"在画布上写数字 | 笔刷大小: {self.brush_size}px | "
            f"下一个编号: {self._save_counter:03d} | "
            "s:保存 p:预测 c:清空",
            fontsize=9,
        )
        self.fig.canvas.draw_idle()

    # ── 图像处理 ──

    def get_28x28(self) -> np.ndarray:
        """将画布降采样为 28x28 灰度图（归一化到 [0,1]）。"""
        factor = CANVAS_SIZE // OUTPUT_SIZE  # 10
        small = np.zeros((OUTPUT_SIZE, OUTPUT_SIZE), dtype=np.float32)
        for i in range(OUTPUT_SIZE):
            for j in range(OUTPUT_SIZE):
                patch = self.canvas[
                    i * factor : (i + 1) * factor, j * factor : (j + 1) * factor
                ]
                small[i, j] = patch.mean()
        return small

    def save_png(self):
        """保存为 28x28 PNG，文件名自动编号。"""
        os.makedirs("samples", exist_ok=True)
        img_28 = self.get_28x28()
        filename = f"samples/drawn_{self._save_counter:03d}.png"

        fig, ax = plt.subplots(figsize=(2, 2))
        ax.imshow(img_28, cmap="gray", vmin=0, vmax=1)
        ax.axis("off")
        fig.savefig(filename, dpi=28, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        print(f"PNG 已保存到 {filename} (28x28)")
        self._save_counter += 1
        self._update_title()

    def save_text(self):
        """保存为文本格式（兼容 mnist_mlp_infer.c），文件名自动编号。"""
        os.makedirs("samples", exist_ok=True)
        img_28 = self.get_28x28()
        filename = f"samples/drawn_{self._save_counter:03d}.txt"

        with open(filename, "w") as f:
            f.write(f"# Hand-drawn digit sample\n")
            for i in range(OUTPUT_SIZE):
                row = " ".join(f"{img_28[i, j]:.4f}" for j in range(OUTPUT_SIZE))
                f.write(row + "\n")

        print(f"文本已保存到 {filename}")
        self._save_counter += 1
        self._update_title()

    def predict(self):
        """用训练好的 MLP 模型预测当前画布上的数字。"""
        try:
            import torch
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from models import MLPClassifier
        except ImportError as e:
            print(f"无法加载模型: {e}")
            return

        img_28 = self.get_28x28()
        x = torch.from_numpy(img_28).float().unsqueeze(0).unsqueeze(0)

        model = MLPClassifier()
        try:
            state = torch.load(
                "checkpoints/mnist_mlp.pt", map_location="cpu", weights_only=True
            )
            model.load_state_dict(state)
            model.eval()
            with torch.no_grad():
                logits = model(x).numpy().flatten()
                probs = np.exp(logits) / np.exp(logits).sum()
                pred = int(np.argmax(logits))
                confidence = float(probs[pred])
        except FileNotFoundError:
            print("未找到 checkpoints/mnist_mlp.pt，请先运行 mnist_mlp.py 训练模型")
            return

        print(f"\n{'='*40}")
        print(f"  MLP 预测结果: {pred}  (置信度: {confidence:.2%})")
        print(f"{'='*40}")
        print("  各类别概率:")
        for i in range(10):
            bar = "#" * int(probs[i] * 40)
            marker = " <--" if i == pred else ""
            print(f"    {i}: {bar} {probs[i]:.3f}{marker}")
        print(f"{'='*40}\n")

        self.ax.set_title(
            f"预测: {pred} (置信度 {confidence:.1%}) | "
            f"笔刷: {self.brush_size}px | s:保存 p:预测 c:清空",
            fontsize=9,
            color="red" if confidence < 0.5 else "black",
        )
        self.fig.canvas.draw_idle()


def main():
    print("手写数字采样工具")
    print("=" * 50)
    print("操作说明:")
    print("  左键拖拽: 书写")
    print("  右键拖拽: 擦除")
    print("  滚轮:     调整笔刷大小 (4-60px)")
    print("  c:        清空画布")
    print("  s:        保存为 PNG (自动编号)")
    print("  t:        保存为文本 (自动编号，兼容 C 推理)")
    print("  p:        用 MLP 模型预测")
    print("  q:        退出")
    print("=" * 50)
    print()

    sampler = DigitSampler()
    plt.show()


if __name__ == "__main__":
    main()
