/-
  Hello.lean - Hello 库的根模块

  这个文件是 `Hello` 库的入口点。
  它定义了哪些模块属于这个库。

  在 Lean 4 项目中：
  - 大写字母开头的 .lean 文件（如 Hello.lean）通常作为库的入口
  - 它通过 import 语句组织库的模块结构
  - 其他文件要使用这个库，只需 `import Hello` 即可
-/

-- 导入 Hello 子目录下的 Basic 模块
-- 这会将 Hello/Basic.lean 中的定义纳入 Hello 库
import Hello.Basic

/-
  模块组织说明：

  目录结构：
    Hello.lean          ← 你在这里（库入口）
    Hello/
      Basic.lean        ← 基础定义模块

  当你写 `import Hello.Basic` 时：
  - Lean 会在当前目录查找 Hello/Basic.lean
  - 也会查找 Hello.lean 中的 `import Hello.Basic`

  如果需要添加更多模块，只需：
  1. 在 Hello/ 目录下创建新的 .lean 文件
  2. 在这里添加对应的 import 语句
  3. 新模块中的定义就会自动成为 Hello 库的一部分

  示例：
    import Hello.Basic      -- 已有
    import Hello.Utils      -- 新增工具模块
    import Hello.Data       -- 新增数据模块
-/
