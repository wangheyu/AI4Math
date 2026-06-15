/-
  MathlibTutorial.lean

  一个很短的 Mathlib 入门教程。

  读者假设：
  - 已经知道 Lean 文件可以用 `#check` 查看类型，用 `example` 写小证明。
  - 不需要熟悉高等数学。

  使用方式：
  1. 在项目根目录打开本文件。
  2. 在 VS Code 中逐行查看 Infoview。
  3. 或运行：

       lake env lean MathlibTutorial.lean

  本文件依赖 Mathlib，所以需要通过 Lake 环境检查。
-/

import Mathlib

namespace MathlibTutorial

/-!
===============================================================================
第 0 章：Mathlib 是什么
===============================================================================

Mathlib 是 Lean 社区维护的大型数学库。

可以把 Lean 核心看成“语言 + 逻辑内核 + 基础数据类型”，而把 Mathlib
看成建立在 Lean 之上的数学知识库。它提供：

1. 大量数学定义
   例如集合、函数、群、环、域、拓扑空间、测度、范畴等。

2. 大量已经证明好的定理
   例如加法交换律、集合包含关系、实数基本性质、整除性质等。

3. 很多实用 tactic
   例如 `norm_num`、`ring`、`linarith`、`omega`、`simp` 等。

初学者可以先把 Mathlib 理解成：

  Lean 的“标准数学百科 + 自动化证明工具箱”。
-/


/-!
===============================================================================
第 1 章：数值命题和 norm_num
===============================================================================

`norm_num` 适合证明具体数字的算术命题。
它来自 Mathlib。
意思是这玩意和数字有关，俺寻思是对的...
-/

example : 2 + 4 = 6 := by
  norm_num

example : 7 * 8 = 56 := by
  norm_num

example : (3 : ℤ) - 10 = -7 := by
  norm_num

example : (2 : ℚ) + 3 / 4 = 11 / 4 := by
  norm_num

/-!
`#check` 可以查看 Mathlib 中的类型和定理。
-/

#check Int
#check Rat
#check Real
#check norm_num


/-!
===============================================================================
第 2 章：代数恒等式和 ring
===============================================================================

`ring` 适合证明交换环里的多项式恒等式。

例如整数、 有理数、实数都可以用 `ring` 处理很多代数恒等式。

这玩意和多项式有关，俺寻思也是对的...
-/

example (x y : ℤ) : x + y = y + x := by
  ring

example (x y : ℚ) : (x + y) ^ 2 = x ^ 2 + 2 * x * y + y ^ 2 := by
  ring

example (x y z : ℝ) : (x + y) + z = x + (y + z) := by
  ring

example (x : ℝ) : (x + 1) * (x - 1) = x ^ 2 - 1 := by
  ring

-- ring 的俺寻思之力可以覆盖 norm_num 的范围了...
example : (3 : ℝ)  = 3 := by
  ring

/-!
===============================================================================
第 3 章：线性不等式和 linarith
===============================================================================

`linarith` 适合处理线性等式和线性不等式。simp 似乎是个终极俺寻思之力，
但它覆盖不了一些简单的线性不等式，所以 linarith 就很有用。
linarith 自动处理由加法、减法、常数倍、≤、<、= 组成的线性关系。
-/

example (a b : ℤ) (h : a ≤ b) : a + 1 ≤ b + 1 := by
  linarith

example (x y : ℚ) (h1 : x ≤ y) (h2 : y ≤ 10) : x ≤ 10 := by
  linarith

example (x : ℝ) (h : x ≥ 3) : x + 2 ≥ 5 := by
  linarith


/-!
===============================================================================
第 4 章：自然数算术和 omega
===============================================================================

`omega` 适合处理自然数、整数上的线性算术。
-/

example (a b : Nat) : a + b = b + a := by
  omega

-- 这里用 ring 也可以，但 omega 更直接。

example (a b : Nat) : a + b = b + a := by
  ring


example (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by
  omega

example (n : Nat) : n + 0 = n := by
  omega

example (n : Nat) : 0 + n = n := by
  omega


/-!
===============================================================================
第 5 章：simp 和简化规则
===============================================================================

`simp` 使用库中标记好的简化定理，把目标化简。

初学时可以把 `simp` 理解为： it's trivial...

  按照 Mathlib/Lean 已知的常用规则自动整理目标。
-/

example (n : Nat) : n + 0 = n := by
  simp

example (n : Nat) : 0 + n = n := by
  simp

example (P : Prop) : True ∧ P ↔ P := by
  simp

-- xs 是一个 Nat 的列表，++ 是列表连接，[] 是空列表。
-- 因此 xs ++ [] 就是把 xs 和空列表连接起来，结果应该还是 xs。
example (xs : List Nat) : xs ++ [] = xs := by
  simp


/-!
===============================================================================
第 6 章：集合 Set
===============================================================================

Mathlib 提供了集合 `Set α`。

`Set Nat` 表示自然数集合。元素属于集合写成 `x ∈ s`。
-/

#check Set
#check Set Nat
#check (fun x : Nat => x = 0)

-- 要证明 s ∩ t ⊆ s
-- ∀ x, x ∈ s ∩ t → x ∈ s
example (s t : Set Nat) : s ∩ t ⊆ s := by
-- 要证明 s ∩ t ⊆ s，按照包含关系的定义，
-- 我们需要证明对于∀ x，x ∈ s ∩ t : x ∈ s。
  intro x hx  -- 按量词要求，先引入一个任意元素 x 消去量词，得到 x ∈ s ∩ t 的假设 hx
              -- 再由集合论，x ∈ s ∩ t 其实就是 x ∈ s ∧ x ∈ t 的意思，
              -- 所以 hx 是一个合取，包含了 x ∈ s 和 x ∈ t 两个信息。
  exact hx.1  -- 所以 hx.1 就是 x ∈ s 的证明。

-- 也可以这么写
example (s t : Set Nat) : s ∩ t ⊆ s := by
  intro x hx  -- 按量词要求，先引入一个任意元素 x 和 x ∈ s ∩ t 的假设 hx
  exact And.left hx

-- 集合论属于 simp 覆盖...
example (s t : Set Nat) : s ∩ t ⊆ s := by
  simp

-- 这些证明都要脑补量词
example (s t : Set Nat) : s ∩ t ⊆ t := by
  intro x hx
  exact hx.2

example (s t : Set Nat) : s ⊆ s ∪ t := by
  intro x hx
  exact Or.inl hx

example (s t : Set Nat) : t ⊆ s ∪ t := by
  intro x hx
  exact Or.inr hx

/-!
集合的交并补、包含关系等在 Mathlib 中都有大量定理。
很多简单集合目标也可以用 `simp` 完成。
-/
-- 证明 s ∩ Set.univ = s
-- 这是证明两个集合相等
-- 即证：∀ x, x ∈ s ∩ Set.univ ↔ x ∈ s
-- 这个转换，可以用 Set.ext 定义的集合相等来完成
-- apply Set.ext
-- 或者 直接用 ext tactic
-- 即 ext x
-- Set.univ 是全集的意思，任何元素都在 Set.univ 中
-- 但它具体指哪个全集，需要看上下文，这里是 Nat 的全集

#check Set.univ

example (s : Set Nat) : s ∩ Set.univ = s := by
  apply Set.ext  -- Set.ext 的意思是：要证明两个集合相等，只需要证明它们的元素逐个等价。\
                 -- 也就是说，证明 ∀ x, x ∈ s ∩ Set.univ ↔ x ∈ s 就能证明 s ∩ Set.univ = s。
                 -- 即将集合论的证明对象自动从集合等式转化为元素逐个等价的形式。
  intro x                     -- 引入任意元素 x，目标变成 x ∈ s ∩ Set.univ ↔ x ∈ s，消除了量词绑定
--  ext x
  apply Iff.intro             -- 证明 x ∈ s ∩ Set.univ ↔ x ∈ s，
                              -- 分两部分：证明 x ∈ s ∩ Set.univ → x ∈ s 和 x ∈ s → x ∈ s ∩ Set.univ
  · intro hx                  -- 证明 x ∈ s ∩ Set.univ → x ∈ s，假设 hx : x ∈ s ∩ Set.univ
    exact hx.1                --  hx 是一个合取，hx.1 就是 x ∈ s
  · intro hx                   -- 证明 x ∈ s → x ∈ s ∩ Set.univ，假设 hx : x ∈ s
    exact And.intro hx True.intro   -- 要证明 x ∈ s ∩ Set.univ 就要证明 x ∈ s 和 x ∈ Set.univ。前者就是 hx，
                                    -- 后者因为 Set.univ 是全体集合，所以 x ∈ Set.univ 是 trivially true 的，
                                    -- 所以用 True.intro 来证明。
/-
这里注意 · 的用法：

  · 是一个标记，表示下面的证明是第一个分支的证明。
  · 是一个标记，表示下面的证明是第二个分支的证明。

  这在证明双向蕴含（↔）时很常见，因为我们需要分别证明两个方向。
-/
--=============================================================================

/-!
这里 apply 的意思是：用一个已有定理/函数来匹配当前目标，把目标变成这个定理还需要的前提。

  可以理解为：

  当前目标是 B。
  如果你有一个东西 h : A → B，
  那么 apply h 会把目标 B 变成目标 A。

  因为只要证明了 A，就可以通过 h 得到 B。

  ———

  最简单例子：（其实就是我们经常用的条件和结论往一起凑）
-/
  example (P Q : Prop) (h : P → Q) (p : P) : Q := by
    apply h   -- 已知 h : P → Q，故有 Q 即有 P
    exact p   -- 已知 p : P，证明 P 就完成了

/-！
再看刚才的例子：

  example (s : Set Nat) : s ∩ Set.univ = s := by
    apply Set.ext

  当前目标是：

  s ∩ Set.univ = s

  而 Set.ext 是：

  (∀ x, x ∈ s ∩ Set.univ ↔ x ∈ s) → (s ∩ Set.univ = s)

  所以：

  apply Set.ext

  意思是：

  我准备用 Set.ext 来证明集合相等。
  Set.ext 说：只要证明逐元素等价，就能证明集合相等。

  于是目标从：

  s ∩ Set.univ = s

  变成：

  ∀ x, x ∈ s ∩ Set.univ ↔ x ∈ s

-/

#check Set.ext

example (s : Set Nat) : s ∩ Set.univ = s := by
  apply Set.ext                       -- 欲证 s ∩ Set.univ = s，只需 ∀ x, x ∈ s ∩ Set.univ ↔ x ∈ s
  intro x                             -- 引入任意元素 x，目标变成 x ∈ s ∩ Set.univ ↔ x ∈ s，消除了量词绑定
--  ext x
  apply Iff.intro                     -- 证明 x ∈ s ∩ Set.univ ↔ x ∈ s，分两部分：证明 x ∈ s ∩ Set.univ → x ∈ s 和 x ∈ s → x ∈ s ∩ Set.univ
  . intro hx                          -- 证明 x ∈ s ∩ Set.univ → x ∈ s，假设 hx : x ∈ s ∩ Set.univ
    exact hx.1                        --  hx 是一个合取，hx.1 就是 x ∈ s
  · intro hx                          -- 证明 x ∈ s → x ∈ s ∩ Set.univ，假设 hx : x ∈ s
    exact And.intro hx True.intro     -- 要证明 x ∈ s ∩ Set.univ 就要证明 x ∈ s 和 x ∈ Set.univ。前者就是 hx，后者因为 Set.univ 是全体集合，所以 x ∈ Set.univ 是 trivially true 的，所以用 True.intro 来证明。


-- 这个也可以simp一下
example (s : Set Nat) : s ∩ Set.univ = s := by
  ext x
  simp

-- 甚至
example (s : Set Nat) : s ∩ Set.univ = s := by
  simp

-- simp 的意思就是有人做过了，你别折腾了...
-- 但新手应该少用 simp，多练习

/-!
===============================================================================
第 7 章：函数
===============================================================================

Mathlib 中有很多关于函数的定义和定理，比如单射、满射、复合函数等。
-/

#check Function.Injective     -- 单射
#check Function.Surjective    -- 满射
#check Function.LeftInverse   -- 左逆
#check Function.RightInverse  -- 右逆

-- 这是一个定理，说明如果 f 是单射，那么对于任意 a b，如果 f a = f b，那么 a = b。
#print Function.Injective

-- 证明 n ↦ n + 1 是单射
example : Function.Injective (fun n : Nat => n + 1) := by
  intro a b h           -- 已知对任意 a，b ∈ Nat，有 (f a = f b) → (a = b)。
                        -- 这里 f 是 n ↦ n + 1，所以假设 h : a + 1 = b + 1，
                        -- 需要证明 a = b。
  exact Nat.succ.inj h  -- Nat.succ.inj 是一个定理，
                        -- ∀ m n : Nat, m + 1 = n + 1 → m = n。
                        -- 对定理 Nat.succ.inj 应用 h，就得到了 a = b 的证明。

#print Nat.succ.inj -- Nat.succ.inj 是一个定理

example : Function.Injective (fun x : ℤ => x + 3) := by
  intro a b h                -- 已知对任意 a，b ∈ ℤ，求证 (f a = f b) → (a = b)。
                             -- 这里 f 是 x ↦ x + 3，所以假设 h : a + 3 = b + 3，
                             -- 需要证明 a = b。
  exact add_right_cancel h  -- add_right_cancel 是一个定理，说明如果 a + c = b + c，那么 a = b。

#print add_right_cancel -- add_right_cancel 是一个定理

/-!
函数复合写作 `g ∘ f`。
-/

example (f : Nat → Int) (g : Int → String) (n : Nat) :
    (g ∘ f) n = g (f n) := by   -- 复合函数的定义就是 (g ∘ f) n = g (f n)，所以这个等式是恒成立的。
  rfl


/-!
===============================================================================
第 8 章：整除和素数
===============================================================================

Mathlib 中已经定义了整除 `∣` 和素数 `Nat.Prime`。
-/

#check Dvd.dvd
#print Dvd.dvd

#check Nat.Prime
#print Nat.Prime


-- Dvd.dvd a b 的意思是 a 整除 b，即存在 k 使得 b = a * k。
-- 也可以用 a ∣ b 来表示 a 整除 b。
-- 证明引入可以使用 norm_num.
example : Dvd.dvd 3 12 := by
  norm_num

example : 3 ∣ 12 := by
  norm_num

-- 也可以直接证明
example : Dvd.dvd 3 12 :=
  ⟨4, rfl⟩  -- 证明存在 k = 4，使得 12 = 3 * 4

-- 展开解释：
-- Dvd.dvd 3 12 的意思是存在一个整数 k，使得 12 = 3 * k。即
-- ∃ k : ℤ, 12 = 3 * k，这是一个存在量词命题证明。
-- 所以需要给出一个具体的 k 和证明 12 = 3 * k。

-- 这里的关键是指出 4 是因子，因此也可以这么写：
example : Dvd.dvd 3 12 := by
  use 4

-- 除不尽
example : ¬ 5 ∣ 12 := by
  norm_num

-- 展开结构，但用 omega 处理算术矛盾
example : ¬ 5 ∣ 12 := by
  intro h  -- 假设 5 ∣ 12，即存在 k 使得 12 = 5 * k
  rcases h with ⟨k, hk⟩  -- 从存在量词中提取 k 和等式 hk : 12 = 5 * k
  omega  -- 这里的 omega 会发现 12 = 5 * k 没有整数解，从而得出矛盾，证明 ¬ 5 ∣ 12。

-- 2 是素数
example : Nat.Prime 2 := by
  norm_num

-- 1 不是素数
example : ¬ Nat.Prime 1 := by
  norm_num

/-!
符号 `∣` 可以输入为：

  \dvd

符号 `¬` 可以输入为：

  \not
-/


/-!
===============================================================================
第 9 章：实数和常见数集
===============================================================================

Mathlib 提供了常见数系和它们的结构：

  Nat  自然数
  Int  整数
  Rat  有理数
  Real 实数
  Complex 复数
-/

#check Nat
#check Int
#check Rat
#check Real
#check Complex

example (x : ℝ) : x + 0 = x := by
  simp

example (x : ℝ) : x * 1 = x := by
  simp

example (x y : ℝ) : x + y = y + x := by
  ring

example (x : ℝ) (h : x > 0) : x + 1 > 0 := by
  linarith


-- 下一章，我们介绍如何建议一整套理论，以我们最熟悉的平面几何为例。

/-!
===============================================================================
第 10 章：如何引入平面几何
===============================================================================

Lean/Mathlib 中引入平面几何，有两条常见路线：

1. 坐标几何路线
   把平面点定义为实数二元组 `ℝ × ℝ`，然后用代数公式定义距离、
   共线、垂直等概念。

2. 抽象几何/欧氏空间路线
   使用 Mathlib 中更一般的度量空间、内积空间、欧氏空间等结构。

初学者建议先从坐标几何路线开始，因为它直观，而且很多证明可以交给
`norm_num`、`ring`、`linarith` 处理。
-/

/-!
我们先定义平面上的点。

`ℝ × ℝ` 是实数对，表示坐标 `(x, y)`。
-/

abbrev Point2D := ℝ × ℝ

def O : Point2D := (0, 0)
def A : Point2D := (1, 0)
def B : Point2D := (0, 1)

#check Point2D
#check O
#check A
#check B

/-!
距离中有平方根。初学时为了避免处理平方根，可以先定义“距离平方”。

`distSq P Q` 表示点 P 和 Q 的距离的平方：

  (x_P - x_Q)^2 + (y_P - y_Q)^2
-/

def distSq (P Q : Point2D) : ℝ :=
  (P.1 - Q.1)^2 + (P.2 - Q.2)^2

-- 这个就是硬算
example : distSq O A = 1 := by
  unfold distSq O A   -- unfold 的意思是：把 distSq O A 展开成定义中的表达式。
  norm_num

example : distSq O B = 1 := by
  unfold distSq O B
  norm_num

/-!
定义“从 A 到 B 和从 A 到 C 等距”。
-/
def equidistant (A B C : Point2D) : Prop :=
  distSq A B = distSq A C

example : equidistant O A B := by
  unfold equidistant distSq O A B
  norm_num

/-!
定义三点共线。

坐标几何中，A、B、C 共线可以用二维行列式为 0 来表达：

  (B.x - A.x) * (C.y - A.y)
    =
  (B.y - A.y) * (C.x - A.x)

这表示向量 AB 和 AC 的方向成比例。
-/
def collinear (A B C : Point2D) : Prop :=
  (B.1 - A.1) * (C.2 - A.2) =
  (B.2 - A.2) * (C.1 - A.1)

example : collinear (0, 0) (1, 1) (2, 2) := by
  unfold collinear
  norm_num

example : collinear (0, 0) (2, 3) (4, 6) := by
  unfold collinear
  norm_num

/-!
定义垂直。

向量 AB 和 AC 垂直，可以用点积为 0 表达：

  AB · AC = 0

也就是：

  (B.x - A.x) * (C.x - A.x)
    +
  (B.y - A.y) * (C.y - A.y)
  = 0
-/

def perpendicular (A B C : Point2D) : Prop :=
  (B.1 - A.1) * (C.1 - A.1) +
  (B.2 - A.2) * (C.2 - A.2) = 0

example : perpendicular O A B := by
  unfold perpendicular O A B
  norm_num

example : perpendicular (0, 0) (2, 0) (0, 5) := by
  unfold perpendicular
  norm_num

/-!
也可以证明带变量的坐标几何命题。

下面的例子说：

  对任意实数 x，如果点 B = (x, 0)，C = (0, 1)，
  那么 OB 和 OC 垂直。

原因是向量 OB = (x, 0)，OC = (0, 1)，点积为 x*0 + 0*1 = 0。
-/

example (x : ℝ) : perpendicular (0, 0) (x, 0) (0, 1) := by
  unfold perpendicular
  ring

/-!
===============================================================================
第 11 章：抽象平面几何和勾股定理
===============================================================================

上一章的坐标几何路线，把点写成 `(x, y)`，然后把距离、共线、垂直都写成
坐标公式。

这种方式很直观，但也有一个缺点：每次都要展开坐标计算。

抽象几何路线换一种视角：

  点不一定先写成坐标。
  我们只要求这些点所在的空间有“向量加法、减法、长度、内积”。

也就是说，我们不再从：

  点 = 实数二元组

出发，而是从：

  点所在的空间 V 是一个实内积空间

出发。

内积空间可以理解为一个能谈论下面这些事情的空间：

1. 两点相减得到向量；
2. 向量有长度，写作 `‖u‖`；
3. 两个向量可以做内积；
4. 内积为 0 表示垂直。

在普通平面中，向量 `(x₁, y₁)` 和 `(x₂, y₂)` 的内积就是：

  x₁ * x₂ + y₁ * y₂

所以“内积为 0”正是上一章坐标垂直公式的抽象版本。
-/

/-!
先看 Mathlib 已经有的抽象对象。
-/

#check InnerProductSpace
#check EuclideanSpace
#check @inner
#check norm_add_sq_eq_norm_sq_add_norm_sq_of_inner_eq_zero

/-!
`EuclideanSpace ℝ (Fin 2)` 可以理解为“二维欧氏空间”。

这里的 `Fin 2` 表示只有两个坐标位置：0 和 1。
所以它对应通常的二维平面。

不过本章的定理会写得更一般：不仅适用于二维平面，也适用于任意实内积空间。
-/

abbrev AbstractPlane := EuclideanSpace ℝ (Fin 2)

#check AbstractPlane

/-!
在抽象空间里，我们先定义“从 A 指向 B 的向量”。

如果 A、B 是点，那么 `B - A` 就是从 A 到 B 的位移向量。
-/
-- 定义从 A 指向 B 的位移向量
-- V 是一个抽象空间，Sub V 表示 V 上有向量加法和减法
-- 这是一个输入两个向量，输出一个向量的函数
def displacement {V : Type*} [Sub V] (A B : V) : V :=
  B - A

/-!
接下来定义内积。

这里写成 `@inner ℝ V _ u v` 是为了明确告诉 Lean：

  我们使用的是实数域 ℝ 上的内积。

对初学者来说，可以把它读成：

  向量 u 和向量 v 的点积。
-/
-- [NormedAddCommGroup V] 表示 V 是一个“带范数的加法交换群”。
-- [InnerProductSpace ℝ V] 表示 V 是一个定义了实内积的空间。
def realInner {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (u v : V) : ℝ :=
  @inner ℝ V _ u v   -- 这里的 _ 是 Lean 的占位符，表示让 Lean 自动推断这个参数。
                     -- 这里的参数是 InnerProductSpace ℝ V 的实例，也就是 V 上定义的实内积的结构。
                     -- 所以这句话完整意思是：引用在实数域 ℝ 上的内积空间 V 中，向量 u 和 v 的内积。

/-!
现在可以定义“两个向量垂直”。

垂直不是 Lean 内置的神秘概念；在内积空间中，我们直接把它定义为：

  内积 = 0
-/

def VectorOrthogonal {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (u v : V) : Prop :=
  realInner u v = 0

/-!
再定义“在 A 点形成直角”。

`RightAngleAt A B C` 的意思是：

  从 A 指向 B 的向量

和

  从 A 指向 C 的向量

互相垂直。
-/

def RightAngleAt {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (A B C : V) : Prop :=
  VectorOrthogonal (displacement A B) (displacement A C)

/-!
这就是抽象几何概念的建立过程：

1. 不先规定坐标；
2. 只假设空间有内积；
3. 用内积定义垂直；
4. 用位移向量定义角。

下面给出一个非常小的例子。

任意向量 u，如果 `u` 和 `v` 垂直，那么 `v` 和 `u` 也垂直。

这个结论在实内积空间中成立，因为实内积是对称的。
-/

example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (u v : V) (h : VectorOrthogonal u v) :
    VectorOrthogonal v u := by
  unfold VectorOrthogonal realInner at * -- 展开 VectorOrthogonal 和 realInner 的定义，
                                         -- 得到 h : @inner ℝ V _ u v = 0
  rwa [real_inner_comm]                  -- real_inner_comm 是一个定理，
                                         -- 说明 @inner ℝ V _ u v = @inner ℝ V _ v u。
                                         -- 直接引用了实内积空间的内积对称性。
                                         -- 所以用 real_inner_comm 把 h 中的 @inner ℝ V _ u v
                                         -- 替换成 @inner ℝ V _ v u，
                                         -- 就得到了 @inner ℝ V _ v u = 0 的结论，
                                         -- 也就是 VectorOrthogonal v u。



/-!
现在引出勾股定理。

普通语言里的勾股定理说：

  如果两条边互相垂直，那么斜边长度的平方
  等于两条直角边长度平方之和。

在向量语言中，它可以写成：

  如果 u ⟂ v，
  那么 u + v 的长度平方 =
  u 的长度平方 + v 的长度平方。

这里 `u + v` 可以理解为：

  先沿着 u 走，再沿着 v 走，最后得到的对角线向量。

Mathlib 中已经有这个定理：

  norm_add_sq_eq_norm_sq_add_norm_sq_of_inner_eq_zero

它的名字很长，但可以按英文拆开读：

  norm_add_sq
    加法向量的范数平方

  eq_norm_sq_add_norm_sq
    等于两个范数平方之和

  of_inner_eq_zero
    前提是内积等于 0

注意：Mathlib 这个定理把“平方”写成乘法形式：

  ‖u‖ * ‖u‖

而不是：

  ‖u‖ ^ 2

数学意义是一样的。
-/

theorem pythagorean_vectors
    {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    {u v : V} (h : VectorOrthogonal u v) :
    ‖u + v‖ * ‖u + v‖ = ‖u‖ * ‖u‖ + ‖v‖ * ‖v‖ := by
  simpa [VectorOrthogonal, realInner] using
    norm_add_sq_eq_norm_sq_add_norm_sq_of_inner_eq_zero u v h

/-!
这段证明很短，因为核心数学定理已经在 Mathlib 中证明好了。

Lean 做的事情是：

1. 展开我们自己定义的 `VectorOrthogonal`；
2. 发现它正好就是 Mathlib 定理需要的前提；
3. 用现成定理得到结论。

这不是“Lean 猜出来了勾股定理”，而是：

  我们把自己的几何语言翻译成 Mathlib 的内积空间语言，
  然后调用 Mathlib 中已经形式化证明过的定理。
-/

/-!
最后，把向量版勾股定理改写成“点”的语言。

设 A 是直角顶点：

  u = B - A
  v = C - A

如果 AB 和 AC 垂直，那么从 A 出发，先走 AB 再走 AC 得到的对角线向量

  (B - A) + (C - A)

的长度平方等于两条直角边长度平方之和。
-/

theorem pythagorean_from_right_angle
    {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    {A B C : V} (h : RightAngleAt A B C) :
    ‖displacement A B + displacement A C‖ *
      ‖displacement A B + displacement A C‖ =
    ‖displacement A B‖ * ‖displacement A B‖ +
      ‖displacement A C‖ * ‖displacement A C‖ := by
  simpa [RightAngleAt] using pythagorean_vectors h

/-!
这就是一个抽象平面几何证明的基本样子：

1. 把“点”放在一个有足够结构的空间中；
2. 用空间结构定义几何概念；
3. 把几何命题转化为内积、范数、代数等命题；
4. 调用 Mathlib 中已有的抽象定理完成证明。

坐标几何和抽象几何不是互相排斥的。

坐标几何适合初学和具体计算；
抽象几何适合表达一般结构，并复用更强的库定理。
-/


example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    {u v : V} (h : VectorOrthogonal u v) :
    ‖u + v‖ ^ 2 = ‖u‖ ^ 2 + ‖v‖ ^ 2 := by   -- 这个其实是一般内积空间中的勾股定理
  unfold VectorOrthogonal realInner at h    -- 展开 VectorOrthogonal 和 realInner 的定义，
                                            -- 得到 h : @inner ℝ V _ u v = 0

  rw [norm_sq_eq_inner (𝕜 := ℝ) (u + v)]    -- 用定理 norm_sq_eq_inner 把目标中的 ‖u + v‖ ^ 2 改写成对应的内积形式。
  rw [norm_sq_eq_inner (𝕜 := ℝ) u]          -- 同理，把 ‖u‖ ^ 2 改写成内积形式。
  rw [norm_sq_eq_inner (𝕜 := ℝ) v]

  simp only [RCLike.re_to_real]  -- 这个定理说明实内积空间中的内积是实数，
                                 -- 所以可以把内积表达式中的实部提取出来，简化计算。

  rw [inner_add_left, inner_add_right, inner_add_right]

  rw [h]
  rw [real_inner_comm u v]
  rw [h]

  ring


/-
  simp only [RCLike.re_to_real]

  意思是：

  > 只使用 RCLike.re_to_real 这一条简化规则，把实数的“取实部”去掉。

  背景是前面用了：

  rw [norm_sq_eq_inner (𝕜 := ℝ) (u + v)]

  这个定理的一般形式其实是：

  ‖x‖ ^ 2 = RCLike.re (inner x x)

  因为 Mathlib 的内积空间既支持实数内积，也支持复数内积。

  对于复数内积：

  inner x x : ℂ

  所以要取实部：

  RCLike.re (inner x x)

  才能得到一个实数。

  但是我们这里的标量域是：

  ℝ

  所以：

  inner x x : ℝ

  已经是实数了。

  这时：

  RCLike.re (inner x x)

  只是“把一个实数看成实数的实部”。

  这显然等于它自己。

  Mathlib 里的定理：

  RCLike.re_to_real

  表达的就是：

  RCLike.re x = x

  在 x : ℝ 时成立。

  所以：

  simp only [RCLike.re_to_real]

  会把目标中的：

  RCLike.re (inner (u + v) (u + v))

  简化成：

  inner (u + v) (u + v)

  同理也会把：

  RCLike.re (inner u u)
  RCLike.re (inner v v)

  简化成：

  inner u u
  inner v v

  这里为什么写：

  simp only [...]

  而不是：

  simp

  因为：

  simp

  会使用很多默认简化规则，可能做很多额外事情。

  而：

  simp only [RCLike.re_to_real]

  表示：

  > 我只允许 simp 使用 RCLike.re_to_real 这一条规则。

  这样证明更可控。
-/

/-!
===============================================================================
第 12 章：基本群论，并引出线性空间
===============================================================================

前面我们一直在使用很多“结构”：

  自然数可以加法；
  实数可以加法、乘法；
  向量可以加法、减法；
  向量还可以乘以实数。

群论的目标，就是把这些运算背后的共同规则抽象出来。

最基本的想法是：

  一个集合/类型上，如果有一种运算，并且这个运算满足一些规则，
  那么它就形成一种代数结构。

在 Lean/Mathlib 中，这些代数结构不是口头约定，而是类型类。
-/

#check Monoid -- 幺半群

/-
  Monoid M

  表示类型 M 上有一种乘法结构，并且满足一些基本规则。

  直观地说，Monoid M 需要：

  1. 一个乘法运算：

  a * b

  2. 一个单位元：

  1

  3. 乘法满足结合律：

  (a * b) * c = a * (b * c)

  4. 单位元满足：

  1 * a = a
  a * 1 = a

  所以可以把 Monoid 理解为：

  > 一个可以连续相乘，并且有单位元 1 的代数结构。

  例如自然数在乘法下是一个 Monoid
-/

#check Monoid Nat

-- 以下依次是群、交换群、加法群、加法交换群的定义。
#check Group
#check CommGroup
#check AddGroup
#check AddCommGroup

/-!
先从乘法记号讲起。

一个 `Group G` 可以粗略理解为：

  G 中有乘法 `*`；
  有单位元 `1`；
  每个元素 a 有逆元 `a⁻¹`；
  乘法满足结合律；
  a * 1 = a，1 * a = a；
  a * a⁻¹ = 1，a⁻¹ * a = 1。

注意：这里的 `*` 不一定是普通数字乘法。
它只是这个类型上的某种二元运算。
-/

-- 断言 G 是一个群，有右单位元 1
example {G : Type*} [Group G]  (a : G) : a * 1 = a := by
  simp

-- 也可全称量词
example {G : Type*} [Group G] : ∀ a : G, a * 1 = a := by
  simp

-- 断言 G 是一个群，有左单位元 1
example {G : Type*} [Group G] (a : G) : 1 * a = a := by
  simp

-- 断言 G 是一个群，有右逆元 a⁻¹
example {G : Type*} [Group G] (a : G) : a * a⁻¹ = 1 := by
  simp

-- 断言 G 是一个群，有左逆元 a⁻¹
example {G : Type*} [Group G] (a : G) : a⁻¹ * a = 1 := by
  simp

-- 断言 G 是一个群，乘法满足结合律
example {G : Type*} [Group G] (a b c : G) :
    (a * b) * c = a * (b * c) := by
  exact mul_assoc a b c  -- 结合律，并没有被吸收到 simp 里，所以需要直接引用 mul_assoc 定理。

#check mul_assoc -- mul_assoc 是一个定理，说明在任何群 G 中，乘法满足结合律。

/-!
上面的例子里，`{G : Type*}` 表示 G 是任意类型；
`[Group G]` 表示 Lean 可以把 G 当作一个群来使用。

所以这些定理不是只对实数成立，而是对所有群成立。

如果群的运算还满足交换律：

  a * b = b * a

那么它叫交换群，Mathlib 中写作 `CommGroup`。
如果写成一般的 Group 就会错。
-/

example {G : Type*} [CommGroup G] (a b : G) :
    a * b = b * a := by
  exact mul_comm a b

/-!
很多数学对象更习惯用加法记号，而不是乘法记号。

例如整数、实数、向量，都常常写：

  a + b
  0
  -a

这时对应的是加法群。

`AddGroup A` 是“用加法记号写的群”；
`AddCommGroup A` 是“用加法记号写的交换群”。
-/

example {A : Type*} [AddCommGroup A] (a : A) :
    a + 0 = a := by
  simp

example {A : Type*} [AddCommGroup A] (a : A) :
    0 + a = a := by
  simp

example {A : Type*} [AddCommGroup A] (a : A) :
    a + (-a) = 0 := by
  simp

example {A : Type*} [AddCommGroup A] (a b : A) :
    a + b = b + a := by
  exact add_comm a b

example {A : Type*} [AddCommGroup A] (a b c : A) :
    (a + b) + c = a + (b + c) := by
  exact add_assoc a b c

/-!
这里有一个重要观念：

  群论不是在研究某一种具体对象，
  而是在研究“只要满足群规则，就一定成立”的结论。

所以 Lean 中的证明经常长这样：

  {G : Type*} [Group G] ...

意思是：

  对任意类型 G，只要 G 有群结构，下面的命题就成立。
-/

/-!
群同态（homomorphism）：保持结构的函数
===============================================================================

有了群之后，自然要研究群之间的函数。

普通函数只要求：

  输入一个元素，输出一个元素。

群同态则要求这个函数保持运算结构。

加法版本的群同态大致是：

  f (x + y) = f x + f y
  f 0 = 0

Mathlib 中加法同态写作 `M →+ N`。
-/

#check AddMonoidHom  -- 加法同态
#check MonoidHom  -- 乘法同态

-- 下面两种写法是等价的，都是表示“从 Nat 到 Nat 的加法同态”。
#check AddMonoidHom Nat Nat
#check ℕ →+ ℕ   -- 注意 →+ 要连在一起写

/-!
下面定义一个整数到整数的加法同态：

  x ↦ 2 * x

也就是“把整数翻倍”。

它保持加法，因为：

  2 * (x + y) = 2 * x + 2 * y
-/

def doubleAddHom : ℤ →+ ℤ where
  toFun := fun x => 2 * x   -- 定义函数部分，输入 x 输出 2 * x，求证这是一个 Z 上的加法同态。
  map_zero' := by    -- 验证 map_zero' 这个属性，即验证 f 0 = 0。
    ring             -- 直接用 ring 处理 2 * 0 = 0 的等式。
  map_add' := by     -- 验证 map_add' 这个属性，即验证 f (x + y) = f x + f y。
    intro x y        -- 引入任意整数 x 和 y（消除全称），准备验证 2 * (x + y) = 2 * x + 2 * y。
    ring             -- 直接用 ring 处理这个等式，证明它成立。

example : doubleAddHom 3 = 6 := by  -- 验证 doubleAddHom 这个函数在输入 3 时输出 6。
  norm_num [doubleAddHom]           -- 直接用 norm_num 处理 doubleAddHom 3 的计算，得到 6。

example (x y : ℤ) :          -- 验证 doubleAddHom 对加法的保持，
                             -- 即验证 doubleAddHom (x + y) = doubleAddHom x + doubleAddHom y。
    doubleAddHom (x + y) = doubleAddHom x + doubleAddHom y := by
  exact map_add doubleAddHom x y   -- 直接引用 doubleAddHom 的 map_add 属性，说明它确实保持加法。

/-!
这说明：

  `doubleAddHom` 不只是一个函数 `ℤ → ℤ`，
  它还携带了“保持加法”的证明。

这正是 Lean/Mathlib 中代数对象的特点：

  一个结构 = 数据 + 公理证明。

例如群结构中不仅有乘法、单位元、逆元这些数据，
还包含结合律、单位元律、逆元律等证明。
-/

/-!
从群到线性空间
===============================================================================

现在可以引出线性空间。

高中或线性代数中说的向量空间，核心有两部分：

1. 向量之间可以相加；
2. 数可以乘向量。

第一部分“向量可以相加，并且有 0 和相反向量”，在抽象代数里就是：

  向量形成一个加法交换群。

也就是说，如果 V 是一个向量空间，那么 V 至少应该有：

  v + w
  0
  -v

并且满足加法交换群的规则。

第二部分是标量乘法：

  a • v

这里 a 是标量，例如实数；
v 是向量。

在 Lean 中，标量乘法使用符号 `•`。
可以输入：

  \smul
-/

#check SMul
/-
 SMul：标量乘法结构

  SMul R V

  表示：

  > 类型 R 中的元素可以“作用”在类型 V 的元素上。

  这个作用写作：

  r • v

  输入：

  r : R
  v : V

  输出：

  r • v : V

  所以 SMul R V 只说明：

  > 有一个运算 R → V → V。
-/

#check Module

/-!
Mathlib 中通常用 `Module R V` 表达“R 上的模”。

如果 R 是一个域，例如 `ℝ`，那么 `Module ℝ V` 就是通常意义上的
实向量空间。

所以可以把下面这组假设读成：

  [AddCommGroup V] [Module ℝ V]

V 的向量加法形成加法交换群；
同时 V 可以被实数标量乘。
-/

-- 线性空间需要的性质，直接就可以从加法交换群和 Module ℝ V 里得到。

-- 定义 V 是一个实向量空间，也就是 V 是一个加法交换群，并且有实数标量乘法。
example {V : Type*} [AddCommGroup V] [Module ℝ V] (v : V) :
    (1 : ℝ) • v = v := by  -- 验证标量乘法的单位律：1 • v = v
  simp

example {V : Type*} [AddCommGroup V] [Module ℝ V] (v : V) :
    (0 : ℝ) • v = 0 := by  -- 验证标量乘法的零律：0 • v = 0
  simp

example {V : Type*} [AddCommGroup V] [Module ℝ V] (a b : ℝ) (v : V) :
    (a + b) • v = a • v + b • v := by   -- 验证标量乘法的分配律： (a + b) • v = a • v + b • v
  exact add_smul a b v

example {V : Type*} [AddCommGroup V] [Module ℝ V] (a : ℝ) (v w : V) :
    a • (v + w) = a • v + a • w := by  -- 验证标量乘法对向量加法的分配律： a • (v + w) = a • v + a • w
  exact smul_add a v w

example {V : Type*} [AddCommGroup V] [Module ℝ V] (a b : ℝ) (v : V) :
    (a * b) • v = a • (b • v) := by   -- 验证标量乘法的结合律： (a * b) • v = a • (b • v)
  exact mul_smul a b v

/-!
这些就是线性空间的基本规则：

  1 • v = v
  0 • v = 0
  (a + b) • v = a • v + b • v
  a • (v + w) = a • v + a • w
  (a * b) • v = a • (b • v)

它们说明标量乘法和向量加法之间是相容的。

所以从群论到线性空间的路线可以总结为：

  群
    抽象出一种可逆运算。

  加法交换群
    抽象出向量加法的基本规则。

  Module ℝ V
    在加法交换群上加入实数标量乘法，并要求它满足分配律、结合律、单位律。

  实向量空间
    可以看作 `AddCommGroup V` + `Module ℝ V`。

后面如果继续发展，就可以在向量空间上再加入内积：

  InnerProductSpace ℝ V

这就回到了第 11 章使用的抽象几何语言。

因此，内积空间的结构链条大致是：

  加法交换群
    → 实向量空间
    → 实内积空间
    → 可以谈论长度、角度、垂直和勾股定理。
-/

/-!
===============================================================================
第 13 章：实数理论
===============================================================================

在 Lean/Mathlib 中，`ℝ` 表示数学意义上的实数。

它不是计算机里的浮点数 `Float`，也不是只能近似计算的小数。
`ℝ` 是一个已经形式化好的数学对象，带有大量结构和定理。

初学时可以先把 Mathlib 中的实数理解为：

  一个完备的有序域。

这句话可以拆成三部分：

1. 域
   可以做加、减、乘、除，并满足通常的代数规则。

2. 有序
   可以比较大小，并且加法、乘法和大小关系相容。

3. 完备
   没有“有理数中的空洞”；很多极限、上确界、连续性定理可以成立。

本章只介绍入门层面的实数性质。
-/

#check Real
#check LinearOrderedField

/-!
`LinearOrderedField ℝ` 可以理解为：

  ℝ 是一个线性有序域。

线性有序的意思是任意两个实数都可以比较。
域的意思是可以做四则运算，并满足代数规则。

很多实数代数恒等式可以用 `ring` 证明。
-/

example (x y : ℝ) : x + y = y + x := by
  ring

example (x y z : ℝ) :
    x * (y + z) = x * y + x * z := by
  ring

example (x : ℝ) :
    (x + 1) * (x - 1) = x^2 - 1 := by
  ring

/-!
实数还有大小关系。

`≤` 和 `<` 是数学中的小于等于和小于。
因为实数是线性有序的，所以任意两个实数 x y，必有：

  x ≤ y 或 y ≤ x

更精细地说，三种情况恰有一种：

  x < y，x = y，y < x
-/

#check le_total  -- 任意两个实数 x y，必有 x ≤ y 或 y ≤ x
#check lt_trichotomy  -- 任意两个实数 x y，恰有一种情况：x < y，x = y，y < x

-- 验证
example (x y : ℝ) :
    x ≤ y ∨ y ≤ x := by
  exact le_total x y

-- 验证
example (x y : ℝ) :
    x < y ∨ x = y ∨ y < x := by
  exact lt_trichotomy x y

/-!
平方非负是实数理论中最常用的事实之一。

任意实数 x，都有：

  x^2 ≥ 0

在 Mathlib 中，常用定理是 `sq_nonneg`。
-/

#check sq_nonneg  -- sq_nonneg : ∀ x : ℝ, 0 ≤ x ^ 2

-- 验证平方非负
example (x : ℝ) :
    x^2 ≥ 0 := by
  exact sq_nonneg x

-- 利用平方非负证明一个不等式
example (x : ℝ) :
    x^2 + 1 > 0 := by
  nlinarith [sq_nonneg x] -- nlinarith 是一个强大的工具，可以处理包含乘法平方的非线性算术。
                          -- 这里我们用它来证明 x^2 + 1 > 0，前提是 sq_nonneg x 告诉我们 x^2 ≥ 0。

-- 其实 nlinarith 也可以直接证明 x^2 + 1 > 0
example (x : ℝ) :
    x^2 + 1 > 0 := by
  nlinarith
-- 但可以为了展示 nlinarith 的前提输入，和可读性，写成上面那个样子。

-- 用于量词的版本
example :
    ∀ x : ℝ, x^2 + 1 > 0 := by
  intro x
  nlinarith [sq_nonneg x]

/-!
这里的 `nlinarith` 适合处理包含乘法平方的非线性算术。

它不是任意数学问题都能自动证明，但对许多初等不等式非常有用。
-/

/-!
绝对值
===============================================================================

实数的绝对值写作：

  |x|

它表示 x 到 0 的距离。

常用事实包括：

  0 ≤ |x|
  x ≤ |x|
  -x ≤ |x|
  |x + y| ≤ |x| + |y|

最后一条就是三角不等式。
-/

#check abs_nonneg    -- abs_nonneg : ∀ x : ℝ, 0 ≤ |x|
#check le_abs_self   -- le_abs_self : ∀ x : ℝ, x ≤ |x|
#check neg_le_abs    -- neg_le_abs : ∀ x : ℝ, -x ≤ |x|
#check abs_add       -- abs_add : ∀ x y : ℝ, |x + y| ≤ |x| + |y|

example (x : ℝ) :
    |x| ≥ 0 := by
  exact abs_nonneg x

example (x : ℝ) :
    x ≤ |x| := by
  exact le_abs_self x

example (x : ℝ) :
    -x ≤ |x| := by
  exact neg_le_abs x

example (x y : ℝ) :
    |x + y| ≤ |x| + |y| := by
  exact abs_add x y

-- 来一个不那么直接的例子：
example (x y : ℝ) : |x - y| ≤ |x| + |y| := by  -- 验证 |x - y| ≤ |x| + |y|
  calc  -- calc 是 Lean 中的一个证明工具，可以用来写链式计算，逐步推导出结论。
    |x - y| = |x + (-y)| := by ring_nf  -- 先把 x - y 改写成 x + (-y)，这样就可以直接应用 abs_add 定理了。
                                        -- ring_nf 是一个工具，可以把表达式改写成“正常形式”，
                                        -- 在这里就是把 x - y 改写成 x + (-y)，类似恒等变形，但不是一切都行。
    _ ≤ |x| + |-y| := by     -- 接下来应用 abs_add 定理，得到 |x + (-y)| ≤ |x| + |-y|。、
                             -- 这里的 _ 是 Lean 的占位符，表示前面计算得到的表达式 |x + (-y)|。
                             -- 这是一种简写，也可以直接写成 |x + (-y)| ≤ |x| + |-y|。
      exact abs_add x (-y)   -- 指出由 abs_add 定理得到这个不等式。
    _= |x| + |y| := by       -- 最后把 |-y| 改写成 |y|，因为绝对值满足 | -a | = | a |。
      rw [abs_neg]           -- abs_neg 是一个定理，说明对于任何实数 a，都有 |-a| = |a|。
                             -- 也可以直接用 norm_num [abs_neg] 来处理这个等式。

-- 下面这么写更接近初中生学习时的习惯：
example (x y : ℝ) : |x - y| ≤ |x| + |y| := by  -- 验证 |x - y| ≤ |x| + |y|
  calc
    |x - y| = |x + (-y)| := by ring_nf
    |x + (-y)| ≤ |x| + |-y| := by
      exact abs_add x (-y)
    |x| + |-y| = |x| + |y| := by
      rw [abs_neg]


/-!
平方根
===============================================================================

实数理论中还可以谈论平方根。

Mathlib 中实数平方根是：

  Real.sqrt x

也可以显示成：

  √x

注意：实数平方根默认返回非负平方根。
-/

#check Real.sqrt            -- Real.sqrt : ℝ → ℝ，这是定义，下面两个是定理
#check Real.sq_sqrt         -- Real.sq_sqrt : ∀ x : ℝ, 0 ≤ x → (Real.sqrt x) ^ 2 = x
#check Real.sqrt_sq_eq_abs  -- Real.sqrt_sq_eq_abs : ∀ x : ℝ, Real.sqrt (x ^ 2) = |x|


example (x : ℝ) (h : 0 ≤ x) :
    (Real.sqrt x)^2 = x := by
  exact Real.sq_sqrt h

example (x : ℝ) :
    Real.sqrt (x^2) = |x| := by
  exact Real.sqrt_sq_eq_abs x

example (x : ℝ) (h : 0 ≤ x) :
    Real.sqrt (x^2) = x := by
  rw [Real.sqrt_sq_eq_abs]
  exact abs_of_nonneg h

/-!
这三个例子表达的是：

1. 如果 `0 ≤ x`，那么 `√x` 的平方等于 x；
2. 任意实数 x，都有 `√(x^2) = |x|`；
3. 如果 x 非负，那么 `√(x^2) = x`。

第三条需要非负条件，因为如果 x = -3，那么：

  √((-3)^2) = √9 = 3

而不是 -3。
-/

/-!
上确界和完备性
===============================================================================

实数和有理数最重要的区别之一是完备性。

直观地说：

  如果一个实数集合非空并且有上界，那么它有最小上界。

这个最小上界叫上确界，英文是 supremum。

在 Mathlib 中，上确界相关对象包括：

  sSup
  IsLUB

其中 `IsLUB s a` 的意思是：

  a 是集合 s 的 least upper bound，也就是最小上界。它就是用上确界定义的。
-/

#check sSup   -- sSup : Set ℝ → ℝ，sSup s 是集合 s 的上确界，前提是 s 非空并且有上界。
#check IsLUB  -- IsLUB : Set ℝ → ℝ → Prop，IsLUB s a 表示 a 是集合 s 的最小上界。

#print sSup
#print IsLUB

/-!
下面证明一个非常具体的上确界例子：

  闭区间 [0, 1] 的上确界是 1。

`Set.Icc (0 : ℝ) 1` 表示闭区间：

  {x : ℝ | 0 ≤ x ∧ x ≤ 1}
-/

example :
    IsLUB (Set.Icc (0 : ℝ) 1) 1 := by
  constructor
  · intro x hx
    exact hx.2
  · intro y hy
    apply hy
    constructor <;> norm_num

/-!
解释一下这个证明。

`IsLUB s 1` 包含两件事：

1. `1` 是 s 的一个上界；
2. 任何其他上界 y，都必须满足 `1 ≤ y`。

第一部分：

  intro x hx
  exact hx.2

因为 `hx : x ∈ Set.Icc 0 1`，展开后就是：

  hx : 0 ≤ x ∧ x ≤ 1

所以 `hx.2` 正是 `x ≤ 1`。

第二部分：

  intro y hy
  apply hy

这里 `hy` 表示 y 是这个区间的上界。
为了证明 `1 ≤ y`，只要证明 `1` 自己属于这个区间，
然后把 `hy` 应用于这个元素即可。

最后：

  constructor <;> norm_num

证明：

  0 ≤ 1
  1 ≤ 1

也就是说 `1 ∈ [0, 1]`。
-/

-- 注意在 lean 的定义中，实数集不包含无穷，因此 sSup s 只能在 s 非空且有上界时定义。
-- 也就是说，当前的定义不支持上确界是无穷的情况。
-- 对非空有上界的实数集，sSup s 和 IsLUB s (sSup s) 是等价的。
example (s : Set ℝ) (hne : s.Nonempty) -- 假设 s 是一个非空实数集合
(hbdd : BddAbove s) :                  -- 假设 s 有上界
    IsLUB s (sSup s) := by             -- 证明 sSup s 就是 s 的最小上界
  exact isLUB_csSup hne hbdd           -- isLUB_csSup 是一个定理，说明对于任何非空有上界的实数集合 s，
                                       -- sSup s 就是 s 的最小上界。

-- 由 IsLUB 的最小性，蕴含了上确界的唯一性。

example {s : Set ℝ} {a b : ℝ}         -- 假设 s 是一个实数集合，a 和 b 是实数
  (ha : IsLUB s a) (hb : IsLUB s b) : -- 假设 a 和 b 都是 s 的最小上界
    a = b := by                       -- 证明 a 和 b 必须相等
  apply le_antisymm                   -- le_antisymm 是一个定理，说明如果 a ≤ b 且 b ≤ a，那么 a = b。
  · exact ha.2 hb.1                   -- ha.2 表示 a 是 s 的一个上界，hb.1 表示 b 是 s 的一个下界，所以 a ≤ b。
  · exact hb.2 ha.1                   -- 同理，hb.2 表示 b 是 s 的一个上界，ha.1 表示 a 是 s 的一个下界，所以 b ≤ a。

/-!
极限入口
===============================================================================

实数完备性最终支撑了极限、连续、导数、积分等理论。

Mathlib 中极限通常用滤子语言表达。
初学者不必马上掌握滤子，但可以先认识这个名字：
-/

#check Filter.Tendsto

/-!
`Filter.Tendsto f l₁ l₂` 大致表示：

  f 的自变量 x 在趋向 l₁ 的时候，其函数值趋向 l₂。

即：

  x → l₁，f(x) → l₂，或者 lim_{x → l₁} f(x) = l₂

在 Mathlib 中往往会用 `Tendsto` 表达。

这比高中教材里的 ε-δ 写法更抽象，但适用范围更大。

因此，实数理论在 Mathlib 中大致可以这样分层理解：

1. 代数层：
   实数是域，可以做四则运算。

2. 顺序层：
   实数可以比较大小，并且大小关系和运算相容。

3. 度量层：
   可以谈论距离、绝对值、邻近。

4. 完备层：
   可以谈论上确界、极限、连续性等。

5. 分析层：
   可以进一步发展微积分、级数、测度、积分等。
-/

open Filter
open Topology

example (a : ℝ) :
    Filter.Tendsto (fun x : ℝ => x + 1) (𝓝 a) (𝓝 (a + 1)) := by
  simpa using (Filter.Tendsto.add tendsto_id tendsto_const_nhds)

/-
  1. open Filter

  open Filter

  打开 Filter 命名空间。

  这样可以直接使用一些滤子相关名字，例如：

  tendsto_id
  tendsto_const_nhds

  否则有些名字可能需要写完整路径。

  比如：

  Filter.tendsto_id

  打开之后可以写：

  tendsto_id

  2. open Topology

  open Topology

  打开拓扑相关记号和名字。

  这里最重要的是让 Lean 能识别：

  𝓝 a

  这个记号。

  𝓝 a 表示 a 的邻域滤子，直观读作：

  x 趋近于 a

  如果没有：

  open Topology

  Lean 可能不能正确解析 𝓝 a

  3. 命题主体

  Filter.Tendsto (fun x : ℝ => x + 1) (𝓝 a) (𝓝 (a + 1))

  这是整个命题。

  它由三部分组成：

  fun x : ℝ => x + 1

  这是函数：

  f(x) = x + 1

  𝓝 a

  是输入侧的趋近方式：

  x 趋近于 a

  𝓝 (a + 1)

  是输出侧的趋近方式：

  函数值趋近于 a + 1

  所以整句读成：

  函数 x ↦ x + 1 在 x 趋近于 a 时，趋近于 a + 1。

  也就是：

  lim_{x → a} (x + 1) = a + 1

  4. 证明部分

  := by
    simpa using (Filter.Tendsto.add tendsto_id tendsto_const_nhds)

  证明使用的是极限的加法法则。

  先看：

  Filter.Tendsto.add

  它的大意是：

  如果 f → A，并且 g → B，
  那么 f + g → A + B。

  形式上类似：

  Filter.Tendsto.add :
    Tendsto f l (𝓝 A) →
    Tendsto g l (𝓝 B) →
    Tendsto (fun x => f x + g x) l (𝓝 (A + B))

  这里我们想证明：

  x + 1 → a + 1

  把它看成两个函数相加：

  x + 1 = id x + constant 1

  第一部分：

  tendsto_id

  表示恒等函数的极限：

  x → a 时，x → a。

  更形式化地说，在滤子 𝓝 a 下：

  Filter.Tendsto id (𝓝 a) (𝓝 a)

  第二部分：

  tendsto_const_nhds

  表示常数函数的极限：

  x → a 时，常数 1 → 1。

  所以：

  Filter.Tendsto.add tendsto_id tendsto_const_nhds

  合起来得到：

  x ↦ x + 1

  趋近于：

  a + 1

  6. simpa using ...

  simpa using (...)

  意思是：

  > 使用括号里的证明，并让 simp 做一些形式整理，使它匹配当前目标。

  为什么需要 simpa？

  因为 Filter.Tendsto.add tendsto_id tendsto_const_nhds 得到的表达式可能在形式上长得像：

  Filter.Tendsto (fun x => id x + 1) (𝓝 a) (𝓝 (a + 1))

  而目标是：

  Filter.Tendsto (fun x : ℝ => x + 1) (𝓝 a) (𝓝 (a + 1))

  二者数学上一样，但 Lean 需要把：

  id x

  化简成：

  x

  simpa 就负责这个整理。

  总结成一句话：

  example (a : ℝ) :
      Filter.Tendsto (fun x : ℝ => x + 1) (𝓝 a) (𝓝 (a + 1)) := by
    simpa using (Filter.Tendsto.add tendsto_id tendsto_const_nhds)

  意思是：

  > 由恒等函数 x ↦ x 在 a 处趋近于 a，以及常数函数 1 趋近于 1，再用极限加法法则，得到函数 x ↦ x + 1 在 a 处趋近于 a + 1。

-/

end MathlibTutorial
