/-
  Hello/Basic.lean - 基础定义模块

  这个模块包含库的基础定义。
  在 Hello 级别的示例中，我们只定义了一个简单的字符串值。

  在更复杂的项目中，这里可以放置：
  - 基础数据类型定义
  - 工具函数
  - 公共常量
  - 基础定理和证明
-/

/-
  定义 hello 常量

  `def hello := "world"` 的含义：
  - `def`         : 定义关键字
  - `hello`       : 名称（小写开头是惯例）
  - `:=`          : 定义符号
  - `"world"`     : 字符串字面量

  Lean 的类型推断会自动推断出：
  hello : String := "world"

  我们也可以显式写出类型签名：
  def hello : String := "world"

  在 Lean 中，所有东西都有类型：
  - "world" 的类型是 String
  - 42 的类型是 Nat（自然数）
  - true 的类型是 Bool
-/
def hello : String := "world"

/-
  更多示例（可以取消注释尝试）：

  -- 定义一个数字
  def myNumber : Nat := 42

  -- 定义一个布尔值
  def isAwesome : Bool := true

  -- 定义一个函数
  def greet (name : String) : String :=
    s!"Hello, {name}!"

  -- 定义一个带证明的定理（Lean 的精髓！）
  theorem addition_commutative (a b : Nat) : a + b = b + a := by
    -- 这里需要给出证明
    omega  -- omega 策略可以自动证明线性算术

  试一试：在 Main.lean 中使用这些定义！
-/
