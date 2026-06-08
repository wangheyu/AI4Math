/-
  Tutorial.lean - Lean 4 数学推理入门

  这个文件是一个交互式的 Lean 4 教程，介绍基本的数学推理和定理证明。
  建议配合 VSCode 的 Lean 扩展使用，可以实时查看类型信息和证明状态。

  使用方法：
  1. 在 VSCode 中打开此文件
  2. 将光标放在 `by` 后面的证明块中，Lean 会显示当前的证明目标
  3. 逐行输入证明策略，观察证明状态的变化
  4. 完成证明后，Lean 会显示 "goals accomplished"
-/

-- ============================================================================
-- 第一部分：命题和定理
-- ============================================================================

/-
在 Lean 中，我们用 `theorem` 或 `example` 来陈述一个数学命题。

格式：
  theorem 定理名称 (参数) : 命题 := by
    证明策略

例如：
-/

-- 简单的逻辑命题
theorem true_is_true : True := by
  -- `True` 是逻辑真，用 `trivial` 策略可以直接证明
  trivial

-- 命题可以是关于具体数字的
example : 2 + 2 = 4 := by
  -- `rfl` (reflexivity) 证明两边计算后相等
  rfl

example : 3 * 5 = 15 := by
  rfl

-- ============================================================================
-- 第二部分：使用假设
-- ============================================================================

/-
在证明中，我们经常需要使用已有的假设。

`intro` 策略引入假设
`exact` 策略使用假设
-/

example (x : Nat) : x = x := by
  -- 这是自反性
  rfl

example (a b : Nat) (h : a = b) : b = a := by
  -- `symm` 翻转等式方向
  symm
  -- 现在目标是 a = b，正好是假设 h
  exact h

-- 更复杂的例子
example (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by
  -- `rw` (rewrite) 用等式重写目标
  rw [h1]
  -- 现在目标变成 b = c
  exact h2

-- ============================================================================
-- 第三部分：基本策略
-- ============================================================================

/-
Lean 提供了许多内置的证明策略：

- `rfl` : 自反性，证明 x = x
- `trivial` : 证明显然的命题
- `simp` : 使用简化规则
- `omega` : 自动证明线性算术
- `ring` : 证明代数等式（环论）
- `rw` : 重写（替换）
- `intro` : 引入假设或变量
- `exact` : 精确匹配目标
-/

-- 算术证明
example (a b : Nat) : a + b = b + a := by
  -- `omega` 可以自动证明关于自然数的线性算术
  omega

example (a b c : Nat) : (a + b) + c = a + (b + c) := by
  -- 这也是线性算术
  omega

-- 代数等式
-- 注意：`ring` 策略要求类型满足 CommRing（交换环），Nat 只是半环，所以这里用 Int
example (x y : Int) : x + y = y + x := by
  -- `ring` 策略可以处理交换环中的等式
  ring

example (x y : Int) : (x + y) ^ 2 = x ^ 2 + 2 * x * y + y ^ 2 := by
  -- `ring` 也能处理更复杂的代数恒等式
  ring

-- ============================================================================
-- 第四部分：蕴含和函数
-- ============================================================================

/-
在 Lean 中，"如果 P 则 Q" 写成 `P → Q`，这是一个函数类型。

证明 `P → Q` 就是给出一个函数：输入 P 的证明，输出 Q 的证明。
-/

-- 简单的蕴含
theorem modus_ponens (P Q : Prop) (h1 : P → Q) (h2 : P) : Q := by
  -- `apply` 将目标从 Q 变成 P（因为 h1 : P → Q）
  apply h1
  -- 现在目标是 P，正好是 h2
  exact h2

-- 另一个例子
example (P Q R : Prop) (h1 : P → Q) (h2 : Q → R) : P → R := by
  -- 引入假设 P
  intro hP
  -- 使用 h1 得到 Q
  have hQ : Q := h1 hP
  -- 使用 h2 得到 R
  have hR : R := h2 hQ
  -- 目标就是 R
  exact hR

-- ============================================================================
-- 第五部分：合取和析取
-- ============================================================================

/-
合取（AND）：`P ∧ Q`，表示 P 和 Q 都成立
析取（OR）：`P ∨ Q`，表示 P 或 Q 至少一个成立
-/

-- 合取
example (P Q : Prop) (hP : P) (hQ : Q) : P ∧ Q := by
  -- `constructor` 将目标 P ∧ Q 分成两个子目标：P 和 Q
  constructor
  -- 第一个子目标是 P
  exact hP
  -- 第二个子目标是 Q
  exact hQ

example (P Q : Prop) (h : P ∧ Q) : P := by
  -- `cases` 分解合取
  cases h with
  | intro hP hQ =>
    -- 现在有了 hP : P 和 hQ : Q
    exact hP

-- 析取
example (P Q : Prop) (hP : P) : P ∨ Q := by
  -- `left` 选择证明左边的析取支
  left
  exact hP

example (P Q : Prop) (hQ : Q) : P ∨ Q := by
  -- `right` 选择证明右边的析取支
  right
  exact hQ

example (P Q R : Prop) (h1 : P ∨ Q) (h2 : P → R) (h3 : Q → R) : R := by
  -- `cases` 对析取进行情况分析
  cases h1 with
  | inl hP =>
    -- 情况 1：P 成立
    exact h2 hP
  | inr hQ =>
    -- 情况 2：Q 成立
    exact h3 hQ

-- ============================================================================
-- 第六部分：量词
-- ============================================================================

/-
全称量词：`∀ x, P x`，表示对所有 x，P(x) 成立
存在量词：`∃ x, P x`，表示存在某个 x，P(x) 成立
-/

-- 全称量词
example : ∀ (n : Nat), n + 0 = n := by
  -- `intro` 引入变量
  intro n
  -- 使用 omega 证明算术等式
  omega

example : ∀ (a b : Nat), a + b = b + a := by
  intro a b
  omega

-- 存在量词
example : ∃ (n : Nat), n + 1 = 5 := by
  -- `use` 提供具体的见证值
  use 4
  -- 现在需要证明 4 + 1 = 5
  rfl

example : ∃ (n : Nat), n > 10 ∧ n < 20 := by
  -- 提供一个满足条件的值
  use 15
  -- 需要证明 15 > 10 ∧ 15 < 20
  constructor
  · -- 第一个子目标：15 > 10
    omega
  · -- 第二个子目标：15 < 20
    omega

-- ============================================================================
-- 第七部分：实战练习
-- ============================================================================

/-
现在尝试自己完成这些证明！
-/

-- 练习 1：证明等式传递性
theorem equality_transitive (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by
  sorry  -- 用 sorry 占位，尝试用 `rw` 或 `exact` 完成证明

-- 练习 2：证明简单的逻辑命题
theorem and_commutes (P Q : Prop) : P ∧ Q → Q ∧ P := by
  sorry  -- 尝试用 `intro`, `cases`, `constructor` 完成

-- 练习 3：证明存在性
theorem exists_double : ∃ (n : Nat), n = 2 * 5 := by
  sorry  -- 尝试用 `use` 完成

-- 练习 4：证明关于自然数的性质
theorem zero_add_right (n : Nat) : n + 0 = n := by
  sorry  -- 提示：试试 `omega` 或 `simp`

-- ============================================================================
-- 第八部分：常用策略速查
-- ============================================================================

/-
基础策略：
  - `rfl`         : 自反性 (x = x)
  - `trivial`     : 显然的命题
  - `assumption`  : 使用假设
  - `exact h`     : 精确匹配假设 h

逻辑策略：
  - `intro h`     : 引入假设或变量
  - `apply h`     : 应用蕴含式 h
  - `have h : P := ...` : 引入中间命题
  - `cases h`     : 对合取/析取/存在进行分情况
  - `constructor` : 构造合取
  - `left` / `right` : 选择析取支

代数策略：
  - `simp`        : 简化（使用 simp 规则）
  - `omega`       : 线性算术（自然数、整数）
  - `ring`        : 环论等式
  - `linarith`    : 线性不等式

重写策略：
  - `rw [h]`      : 用等式 h 重写
  - `rw [← h]`    : 反向重写（用 h 的右边替换左边）

证明终止：
  - `done`        : 确认所有目标都已证明
  - `sorry`       : 跳过证明（仅用于开发）
-/

-- ============================================================================
-- 下一步学习
-- ============================================================================

/-
恭喜你完成了 Lean 4 的基础入门！

接下来可以学习：
1. 归纳类型和模式匹配
2. 递归函数和结构归纳
3. 集合和函数
4. 使用 Mathlib4（Lean 的数学库）

推荐资源：
- 《The Natural Number Game》- 交互式学习 Lean 证明
- 《Mathematics in Lean》- 使用 Lean 进行数学形式化
- Lean 4 官方文档：https://lean-lang.org/lean4/doc/
- Mathlib4：https://github.com/leanprover-community/mathlib4
-/
