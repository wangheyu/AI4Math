# Lean4 Discussion Notes

从此处开始记录本次关于 Lean4 基础概念的讨论。

## 2026-06-06

- 用户要求：从现在开始，将讨论记录到 `note.md`。
- 记录方式：后续关于 Lean4 概念的问答会继续追加到本文件。

### 类型宇宙与悖论

- 问题：Lean4 的类型宇宙是否本质上是为了避免类似“理发师只给不会给自己理发的人理发”的逻辑悖论？
- 要点：可以这样类比。类型宇宙层级的核心目的之一是避免自指导致的悖论，例如“所有类型组成的类型仍然属于自己”这类结构。Lean 使用 `Type u : Type (u+1)`，而不是 `Type : Type`，来阻止这种危险的自包含。

### 命题与证明的分层

- 问题：命题和证明的关系是否也有避免悖论方面的考虑？
- 要点：有。Lean 区分 `P : Prop` 和 `h : P`：前者表示 `P` 是一个命题，后者表示 `h` 是该命题的证明。命题不是自己的证明，证明也不是一个布尔真假值。这种分层能避免把“命题本身”“命题的证明”“关于命题的命题”混成同一层。
- 补充：Lean 的 `Prop` 是特殊宇宙，支持命题即类型、证明无关性，并限制从证明中提取普通计算数据。这些设计既服务于逻辑一致性，也服务于程序计算时擦除证明。

### 计算与证明的关系

- 问题：从 `Prop` 的证明一般不能随意提取 `Nat` 或 `Bool`，这是否意味着计算和证明完全分离？
- 要点：不是完全分离。Lean 中证明本身也是项，计算可以帮助证明，例如 `rfl`、`decide`、化简和函数求值都能产生证明；证明也可以通过等式改写影响后续项的类型。但 Lean 限制从普通 `Prop` 证明中提取计算数据。
- 例子：`h : ∃ n : Nat, n > 0` 不能直接通过模式匹配得到一个可计算的 `Nat`，因为 `Exists.elim` 只能消去到 `Prop`。若要携带可计算见证，应使用 `Subtype` 或 `Sigma` 等 `Type` 层数据；若使用 `Classical.choose`，可以从存在性证明得到见证，但这是非计算性的。

### 原子命题、True 与 False

- 问题：最原子的命题是否就是 `True` 和 `False`？
- 要点：不完全是。`True` 和 `False` 是最简单的命题常量：`True` 有一个无条件证明 `True.intro`，`False` 没有构造子。但逻辑里所谓原子命题通常指没有再用 `¬`、`∧`、`∨`、`→`、`∀`、`∃` 等逻辑连接词分解的命题，例如变量 `P : Prop`、等式 `n = 0`、谓词应用 `Prime p`。原子性更多是语法/分析角度，而不是 Lean 内核中只有 `True` 和 `False` 两个基础命题。

### 复合命题的宇宙层级

- 问题：一个复合命题的数据类型可以是 `Type 2` 吗？
- 要点：如果它真的是命题，那么它的类型仍然是 `Prop`，不会因为逻辑结构复杂就升到 `Type 1` 或 `Type 2`。例如 `P ∧ Q`、`P → Q`、`∀ n : Nat, P n`、`∃ n : Nat, P n` 都是 `Prop`。但如果把命题、类型或类型构造器作为数据对象再组成新的类型，例如 `Prop → Type`、`Type 1 → Type`，这些表达式本身可能位于更高宇宙，如 `Type 1` 或 `Type 2`。

### 介绍 Lean 逻辑体系的顺序

- 问题：介绍整个逻辑体系时，应先从类型宇宙开始，还是先从命题和证明的定义开始？
- 要点：更适合先从“项 : 类型”的判断开始，再讲 `Prop`、命题即类型、证明即项，然后讲逻辑连接词和归纳类型，最后系统介绍 `Prop : Type`、`Type : Type 1` 等宇宙层级。宇宙层级是保证一致性的背景机制，但一开始直接讲容易抽象；先理解命题和证明能让宇宙层级的必要性更自然。

## Lean4 逻辑体系入门教程

本教程建议按下面的路线理解 Lean4 的逻辑体系：

```text
项 : 类型
数据类型
命题 : Prop
证明 : 命题的项
逻辑连接词
归纳类型与归纳法
类型宇宙
```

### 1. 最基本的判断：项属于类型

Lean 中最基本的形式是：

```lean
x : A
```

读作：`x` 是类型 `A` 的一个项。

例如：

```lean
#check (0 : Nat)
-- 0 : Nat

#check true
-- true : Bool

#check Nat
-- Nat : Type

#check Bool
-- Bool : Type
```

这里有两层关系：

```text
0    : Nat
true : Bool

Nat  : Type
Bool : Type
```

也就是说，`0` 是自然数类型里的一个值，`true` 是布尔类型里的一个值；而 `Nat` 和 `Bool` 本身又是 `Type` 里的对象。

### 2. 数据类型：以 Bool 和 Nat 为例

`Bool` 是一个普通数据类型，它有两个构造子：

```lean
inductive Bool : Type where
  | false : Bool
  | true  : Bool
```

所以：

```lean
false : Bool
true  : Bool
```

它们是两个数据值，可以用于计算：

```lean
def myNot (b : Bool) : Bool :=
  match b with
  | false => true
  | true  => false

#eval myNot true
-- false

#eval myNot false
-- true
```

`Nat` 也是归纳数据类型，核心结构是：

```lean
inductive Nat : Type where
  | zero : Nat
  | succ : Nat -> Nat
```

含义是：

```text
Nat.zero 是自然数；
如果 n 是自然数，那么 Nat.succ n 也是自然数。
```

所以自然数可理解为：

```lean
Nat.zero
Nat.succ Nat.zero
Nat.succ (Nat.succ Nat.zero)
```

分别对应：

```text
0, 1, 2
```

但字符 `0` 不是构造子本身，真正的构造子是：

```lean
Nat.zero
```

Lean 通过数字字面量机制和 `OfNat` 实例，让：

```lean
(0 : Nat)
```

对应到 `Nat.zero`。

可以验证：

```lean
example : (0 : Nat) = Nat.zero := by
  rfl
```

用户也可以增加新记号：

```lean
notation "零" => Nat.zero

example : 零 = (0 : Nat) := by
  rfl
```

### 3. 命题：Prop 中的对象

Lean 中，命题属于 `Prop`：

```lean
#check True
-- True : Prop

#check False
-- False : Prop

#check 2 + 2 = 4
-- 2 + 2 = 4 : Prop
```

所以：

```lean
True        : Prop
False       : Prop
2 + 2 = 4   : Prop
```

`Prop` 是命题的宇宙。Lean 的观点是：

```text
命题也是类型。
证明是这个类型的项。
```

因此，命题的“成立”不是说它等于 `true : Bool`，而是说它有证明。

### 4. True、False、true、false 的区别

`true` 和 `false` 是布尔数据：

```lean
true  : Bool
false : Bool
```

`True` 和 `False` 是命题：

```lean
True  : Prop
False : Prop
```

`True` 的定义大致是：

```lean
inductive True : Prop where
  | intro : True
```

所以它有一个无条件证明：

```lean
True.intro : True
```

`False` 没有构造子：

```lean
inductive False : Prop
```

所以没有办法直接构造：

```lean
h : False
```

这种证明。

对比：

```text
true        : Bool   -- 布尔数据值
True        : Prop   -- 命题
True.intro  : True   -- 命题 True 的证明
```

### 5. 证明：命题类型中的项

如果：

```lean
P : Prop
h : P
```

那么 `h` 就是命题 `P` 的证明。

例如：

```lean
example : True := by
  exact True.intro
```

这里目标是证明 `True`，而 `True.intro : True` 正好就是它的证明。

再看蕴含：

```lean
example (P : Prop) : P -> P := by
  intro h
  exact h
```

解释：

```text
目标：P -> P
intro h：假设 h : P
目标变成：P
exact h：用 h 完成目标
```

这段 tactic 证明对应的底层证明项大致是：

```lean
fun h : P => h
```

所以 `P -> P` 的证明本质上是一个函数：给它一个 `P` 的证明，它返回一个 `P` 的证明。

### 6. 蕴含、合取、析取

蕴含 `P -> Q` 的证明是一个函数：

```lean
example (P Q R : Prop) : (P -> Q) -> (Q -> R) -> P -> R := by
  intro hpq
  intro hqr
  intro hp
  exact hqr (hpq hp)
```

合取 `P ∧ Q` 的证明包含两个部分：一个 `P` 的证明和一个 `Q` 的证明。

```lean
example (P Q : Prop) : P -> Q -> P ∧ Q := by
  intro hp
  intro hq
  exact And.intro hp hq
```

从合取里取出左边或右边：

```lean
example (P Q : Prop) : P ∧ Q -> P := by
  intro h
  exact h.left

example (P Q : Prop) : P ∧ Q -> Q := by
  intro h
  exact h.right
```

析取 `P ∨ Q` 的证明分两种情况：要么证明左边，要么证明右边。

```lean
example (P Q : Prop) : P -> P ∨ Q := by
  intro hp
  exact Or.inl hp

example (P Q : Prop) : Q -> P ∨ Q := by
  intro hq
  exact Or.inr hq
```

### 7. 全称与存在

全称命题：

```lean
∀ n : Nat, n = n
```

意思是：对任意自然数 `n`，都有 `n = n`。

证明：

```lean
example : ∀ n : Nat, n = n := by
  intro n
  rfl
```

`intro n` 的含义是：任取一个自然数 `n`，然后证明目标。

存在命题：

```lean
∃ n : Nat, n = 0
```

意思是：存在一个自然数 `n`，使得 `n = 0`。

证明：

```lean
example : ∃ n : Nat, n = 0 := by
  exact Exists.intro 0 rfl
```

这里给出的见证是 `0`，然后用 `rfl` 证明 `0 = 0`。

注意：`∃ n : Nat, n > 0` 是 `Prop`，它表达存在性，但不能一般地作为可计算数据来源。

如果想携带一个真的可计算自然数，以及它满足某性质的证明，应使用 `Subtype`：

```lean
def PositiveNat := { n : Nat // n > 0 }

def getNat (x : PositiveNat) : Nat :=
  x.val
```

这里 `PositiveNat` 是 `Type` 层的数据类型，里面真的包含一个 `Nat`。

### 8. 等式、计算和证明

等式也是命题：

```lean
#check true = true
-- true = true : Prop

#check 1 + 1 = 2
-- 1 + 1 = 2 : Prop
```

`rfl` 用来证明两边定义相等的等式：

```lean
example : 1 + 1 = 2 := by
  rfl
```

这里 Lean 计算 `1 + 1` 后发现它和 `2` 定义相等。

有些简单可判定命题可以用 `decide`：

```lean
example : 2 < 5 := by
  decide
```

这说明计算可以帮助证明。但这并不意味着命题本身是 `Bool`，而是 Lean 可以通过可判定过程生成相应证明。

### 9. 归纳类型与归纳法

归纳类型的定义会自动生成递归和归纳原则。

例如自定义自然数：

```lean
inductive MyNat : Type where
  | zero : MyNat
  | succ : MyNat -> MyNat
```

Lean 会生成类似：

```lean
MyNat.rec
```

它表达了对 `MyNat` 的递归/归纳原则。

对内置自然数，数学归纳法可以这样用：

```lean
example (n : Nat) : n + 0 = n := by
  induction n with
  | zero =>
      rfl
  | succ n ih =>
      simp [ih]
```

解释：

```text
zero 情况：证明 0 + 0 = 0
succ 情况：假设 ih : n + 0 = n，证明 Nat.succ n + 0 = Nat.succ n
```

这正是数学归纳法：

```text
证明 P 0；
证明 P n -> P (n+1)；
于是得到 ∀ n, P n。
```

### 10. 类型宇宙

前面一直在使用：

```lean
Nat  : Type
Bool : Type
True : Prop
```

但 `Prop` 和 `Type` 本身也有类型：

```lean
#check Prop
-- Prop : Type

#check Type
-- Type : Type 1

#check Type 1
-- Type 1 : Type 2
```

更完整地说：

```text
Prop   = Sort 0
Type   = Type 0 = Sort 1
Type 1 = Sort 2
Type 2 = Sort 3
```

Lean 不允许简单地把所有类型都放进同一个 `Type : Type` 里，因为这会导致自指悖论。于是它使用层级：

```text
Type 0 : Type 1
Type 1 : Type 2
Type 2 : Type 3
```

这是一种避免 Russell 悖论、理发师悖论这类自包含问题的分层机制。

注意：命题复杂度不会让命题升到 `Type 2`。只要它是命题，它仍然属于 `Prop`：

```lean
variable (P Q : Prop)

#check P ∧ Q
-- P ∧ Q : Prop

#check P -> Q
-- P -> Q : Prop

#check ∀ n : Nat, n = n
-- ∀ n : Nat, n = n : Prop
```

但类型构造器可能位于更高宇宙：

```lean
#check Type -> Type
-- Type -> Type : Type 1

#check Type 1 -> Type
-- Type 1 -> Type : Type 2
```

### 11. 总结表

| 形式 | 含义 |
| --- | --- |
| `x : A` | `x` 是类型 `A` 的项 |
| `0 : Nat` | `0` 是自然数 |
| `true : Bool` | `true` 是布尔数据 |
| `P : Prop` | `P` 是命题 |
| `h : P` | `h` 是命题 `P` 的证明 |
| `Nat : Type` | `Nat` 是一个数据类型 |
| `True : Prop` | `True` 是命题 |
| `True.intro : True` | `True.intro` 是 `True` 的证明 |
| `Prop : Type` | 命题宇宙本身是一个类型 |
| `Type : Type 1` | `Type 0` 位于更高宇宙 `Type 1` |

### 12. 练习

练习 1：证明 `P -> Q -> P`。

```lean
example (P Q : Prop) : P -> Q -> P := by
  intro hp
  intro hq
  exact hp
```

练习 2：交换合取的左右两边。

```lean
example (P Q : Prop) : P ∧ Q -> Q ∧ P := by
  intro h
  exact And.intro h.right h.left
```

练习 3：证明如果 `P` 和 `P -> Q` 都成立，那么 `Q` 成立。

```lean
example (P Q : Prop) : P -> (P -> Q) -> Q := by
  intro hp
  intro hpq
  exact hpq hp
```

练习 4：证明任意自然数都等于自身。

```lean
example : ∀ n : Nat, n = n := by
  intro n
  rfl
```

练习 5：给出一个存在性证明。

```lean
example : ∃ n : Nat, n = 0 := by
  exact Exists.intro 0 rfl
```

这套路线的核心是：

```text
先理解 x : A；
再理解 P : Prop；
再理解 h : P；
最后理解 Prop、Type、Type 1 的宇宙分层。
```
