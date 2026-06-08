# Hello - Lean 4 入门示例项目

## 📖 项目简介

这是一个 **Hello World** 级别的 Lean 4 项目，用于演示 Lean 4 项目的基本结构和语法。

**Lean 4** 是一个现代的函数式编程语言和交互式定理证明器，由微软研究院开发。

## 🚀 快速开始

### 1. 构建项目

```bash
cd ~/LEAN4
lake build
```

这会编译项目，生成可执行文件 `build/bin/hello`。

### 2. 运行程序

```bash
# 方式一：使用 lake 运行
lake exe hello

# 方式二：直接运行编译后的二进制文件
./build/bin/hello
```

**预期输出：**
```
Hello, world!
```

### 3. 解释执行（不生成二进制）

```bash
lake env lean --run Main.lean
```

## 📁 项目结构

```
LEAN4/
├── .git/                   # Git 仓库
├── .github/
│   └── workflows/
│       └── lean-action.yml # GitHub Actions CI 配置
├── Hello/                  # 库模块目录
│   └── Basic.lean          # 基础定义模块
├── Hello.lean              # 库入口文件
├── Main.lean               # 主程序入口
├── lakefile.toml           # Lake 构建配置
├── lean-toolchain          # Lean 版本配置
├── .gitignore              # Git 忽略规则
└── README.md               # 本文件
```

## 📝 文件说明

| 文件 | 说明 |
|------|------|
| `Main.lean` | 程序入口，包含 `main` 函数 |
| `Hello.lean` | 库入口，组织库模块 |
| `Hello/Basic.lean` | 基础定义，包含 `hello` 常量 |
| `lakefile.toml` | 构建配置，定义项目元信息和目标 |
| `lean-toolchain` | 指定 Lean 工具链版本 |

## 🎓 代码详解

### Main.lean（主程序）

```lean
import Hello

def main : IO Unit :=
  IO.println s!"Hello, {hello}!"
```

- `import Hello` : 导入 Hello 库
- `def main` : 定义主函数
- `IO Unit` : 返回类型，表示执行 IO 操作
- `IO.println` : 打印输出函数
- `s!"..."` : 字符串插值语法

### Hello/Basic.lean（库定义）

```lean
def hello : String := "world"
```

- 定义了一个字符串常量 `hello`
- 值为 `"world"`
- 类型 `String` 会被自动推断

## 🔧 常用命令

```bash
# 构建项目
lake build

# 清理构建产物
lake clean

# 运行程序
lake exe hello

# 更新依赖（如果有）
lake update

# 查看帮助
lake --help
```

## 📚 扩展练习

试着修改项目，练习 Lean 4 语法：

### 练习 1：修改输出

编辑 `Hello/Basic.lean`：
```lean
def hello : String := "Lean 4"
```

重新构建运行，观察输出变化。

### 练习 2：添加新定义

在 `Hello/Basic.lean` 中添加：
```lean
def myNumber : Nat := 42
def isAwesome : Bool := true
```

### 练习 3：使用新定义

在 `Main.lean` 中使用新定义：
```lean
def main : IO Unit := do
  IO.println s!"Hello, {hello}!"
  IO.println s!"My number: {myNumber}"
  IO.println s!"Is awesome? {isAwesome}"
```

注意：多行 IO 操作需要使用 `do` 语法块。

## 🌐 相关链接

- [Lean 4 官方网站](https://lean-lang.org/)
- [Lean 4 文档](https://lean-lang.org/lean4/doc/)
- [Lean 4 教程](https://lean-lang.org/lean4/doc/learning.html)
- [Mathlib4](https://github.com/leanprover-community/mathlib4) - 数学库
- [Lean 4 中文社区](https://leanprover.cn/)

## 💡 学习建议

1. **从 Lean 4 官方教程开始**：https://lean-lang.org/lean4/doc/learning.html
2. **安装 VSCode Lean 扩展**：提供实时类型信息和错误提示
3. **边写边看类型**：Lean 的类型系统是最大的特色
4. **尝试证明简单定理**：体验交互式证明的魅力

---

**Happy Lean ing! 🎉**
