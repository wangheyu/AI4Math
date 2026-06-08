/-
  Main.lean - 程序主入口文件

  这是 Lean 4 可执行程序的入口点。
  当运行 `lake build` 或 `lake exe hello` 时，
  会编译并执行这里的 `main` 函数。
-/

-- 导入 Hello 库模块
-- 这会引入 Hello.lean 及其依赖的所有定义
import Hello

/-
  定义主函数

  `def main : IO Unit :=` 的含义：
  - `def main`      : 定义一个名为 main 的函数
  - `: IO Unit`     : 类型签名，表示这个函数会执行 IO 操作，返回 Unit（类似 void）
  - `:=`            : 定义符号，后面是函数体
  - `IO Unit`       : IO 表示这是一个可以进行输入输出的计算
  - `Unit`          : 类似其他语言的 void，表示不返回有意义的值

  Lean 4 使用 `:=` 而不是 `=` 来定义函数，
  这是因为 `=` 用于表示等式/命题，而 `:=` 用于定义。
-/
def main : IO Unit :=
  -- IO.println 是一个 IO 操作，用于向标准输出打印一行文本
  -- s!"..." 是 Lean 4 的字符串插值语法（类似 Python 的 f-string）
  -- {hello} 会替换为 hello 变量的值
  -- hello 来自 Hello/Basic.lean 中定义的值
  IO.println s!"Hello, {hello}!"

/-
  运行方式：

  1. 在项目根目录执行：
     lake build           -- 编译项目
     lake exe hello       -- 运行编译后的程序

  2. 或者直接运行（自动编译）：
     lake env lean --run Main.lean

  3. 也可以先构建再运行：
     lake build
     ./build/bin/hello    -- 直接执行二进制文件

  预期输出：
  Hello, world!
-/
