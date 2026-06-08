/-
  Logic.lean

  Lean 4 逻辑、类型论和证明入门

  读者假设：
  - 不需要学过数理逻辑
  - 不需要学过 Lean 编程
  - 不需要知道 Curry-Howard（命题即类型、证明即程序）

  阅读方式：
  1. 在 VS Code 中打开本文件。
  2. 把光标放在 `#check`、`#eval` 或证明代码附近，看 Lean Infoview 的输出。
  3. 不要急着记符号，先理解一个核心判断：

       x : A

     它读作：x 是 A 类型的一个项。

  本文件尽量不用高级策略，也不依赖 Mathlib。重点是把逻辑规则
  解释成最普通的“构造数据”和“使用函数”。
-/

namespace LogicTutorial

/-!
===============================================================================
第 0 章：Lean 文件里你会看到什么
===============================================================================

Lean 文件中有三类内容最常见：

1. 注释
   `/- ... -/` 是多行注释。
   `-- ...` 是单行注释。

2. 命令
   `#eval` 让 Lean 计算一个表达式。
   `#check` 让 Lean 告诉你一个表达式的类型。

3. 定义和证明
   `def` 定义一个值或函数。
   `theorem` 定义一个定理；在 Lean 中，定理本质上也是一个带类型的定义。

先从最普通的计算开始。
-/

#eval 1 + 1
#eval 2 * 3
#eval "hello"
#eval true
/- 定义一个自然数常量，x 的值在之后的计算中不能修改-/
def x : Nat := 42
#eval x

/-
#eval 只能求值可计算的项。在lean中，项的概念比一般编程中的表达式，
或者一阶逻辑中的term更广泛。它可以是一个数据值，也可以是一个函数，甚至可以是一个证明。
但在 #eval 中，只有那些可以被 Lean 计算出来的项才会被求值。
-/

/-!
`#check` 不计算值，而是问：“这个项是什么类型？” 因此它可以检查一切项。
-/

#check 1
#check 1 + 1
#check "hello"
#check true
#check false
#check x + 1 = 43

/-!
你会看到类似：

  1 : Nat
  "hello" : String
  true : Bool

这就是 Lean 里最基本的形式：

  项 : 类型

以后所有逻辑和证明都会回到这个形式。
这里 x + 1 = 43 也是一个项，它的类型是 Prop (命题)。

-/

/- 我们可以看到一些通过简单计算就可以判定的命题，可以直接用 #eval 求值。-/
#eval x + 1 = 43
/- 但在 lean 中，这个只是计算，不是证明，在这套逻辑体系中，
这只说明这个项（同时也是一个命题）有一个可计算的判定结果，而不是严格的逻辑证明。
如果一个命题（同时也是一个项），设计更加复杂的逻辑，那么 #eval 就无法求值了。
比如：
-/

/-这是一个命题-/
#check (∀ n : Nat, n = n)
/-但 #eval 无法求值，因为这里全称量词作用对象 Nat 是无限的，无法形成一个可计算的判定-/
#eval (∀ n : Nat, n = n)

/-!
===============================================================================
第 1 章：项和类型
===============================================================================

“项”（term）可以暂时理解成一个具体东西：

  0
  42
  true
  "Lean"
  fun n => n + 1

“类型”（type）是这些东西所属的类别：

  Nat     自然数
  Int     整数
  Bool    布尔值
  String  字符串

Lean 的基本任务就是检查“某个项是否真的属于某个类型”。
-/

#check (0 : Nat)
#check (42 : Nat)
#check (-3 : Int)
#check (true : Bool)
#check ("Lean" : String)

/-!
括号中的 `: Nat`、`: Int` 叫类型标注。
它是在告诉 Lean：“请把这个表达式看成这个类型。”

有些数字既可以被看成 Nat，也可以被看成 Int，所以类型标注有时很有用。
-/

#check (5 : Nat)
#check (5 : Int)

/-!
类型本身也可以被 Lean 检查。
-/

#check Nat
#check Int
#check Bool
#check String

/-!
你会看到：

  Nat : Type
  Bool : Type

这说明 Nat、Bool 这些“类型”自己也有一个更大的类型，叫 `Type`。

于是我们得到两层：

  0     : Nat
  Nat   : Type

这不是文字游戏，而是 Lean 类型论的基本骨架。
-/

#check Type
#check Type 1
/-...-/
#check Type 32

/-这个层级理论上是向上无限的，向下则到 Type 0，其实就是 Type，Type 下还有一级，
就是我们常识中的各种类型，如 Nat、Bool、String 等等，这些都是 Type 的项，
这其中最重要的是 Prop（命题） 也是一种类型。和其他类型如 Nat、Bool 处于同一层级，
都是这个类型宇宙的底层。
-/

/-!
===============================================================================
第 2 章：定义值和函数
===============================================================================

用 `def` 可以给一个项起名字。
-/

def smallNumber : Nat := 7
/-这个含义非常明确，我要定义一个名为 smallNumber 的项，类型是 Nat，值是 7。-/
/-在上下文明确的时候，可以省略类型标注，这个被称为类型推断-/
def lazySmallNumber := 7

def greeting : String := "hello, Lean"
def leanIsFun : Bool := true

#eval smallNumber
#eval lazySmallNumber + 1
#eval greeting
#eval leanIsFun

/-!
函数也是项。函数也有类型。

下面的函数输入一个自然数，输出它加一。
-/

/- 典型的一元函数，def 函数名 (参数 : 类型) : 返回类型 := 函数体（返回项） -/
def addOne (n : Nat) : Nat :=
  n + 1

/-注意在函数调用时括号可以省略-/
#eval addOne (5)

#eval addOne 5


/-这个函数有名字，因此在check时，类型以带参数名的方式显示-/
#check addOne

/-但本质上这样的函数类型是 Nat → Nat-/
#check (addOne : Nat → Nat)

/-!
在 VS Code 的 Message/Infoview 中，`#check addOne` 可能显示为：

  LogicTutorial.addOne (n : Nat) : Nat

这表示：

  addOne 接收一个参数 n，参数类型是 Nat，返回类型是 Nat。

同一个类型也可以写成：

  Nat → Nat

读作：

  输入 Nat，输出 Nat。

`(n : Nat) : Nat` 是带参数名的显示方式。
`Nat → Nat` 是不写参数名的箭头显示方式。
因为返回类型里的 `Nat` 并不依赖参数名 `n`，所以这两个说的是同一件事。

箭头 `→` 在普通编程中表示函数类型。后面你会看到，
同一个箭头在逻辑中也表示“如果 ... 那么 ...”。
-/

/-来看个二元函数-/
def addTwoNumbers (a b : Nat) : Nat :=
  a + b

/-函数参数不用加括号-/
#eval addTwoNumbers 3 4
#eval addTwoNumbers (3) (4)
/-这个是错误的-/
#eval addTwoNumbers (3 4)

#check addTwoNumbers

/-!
`addTwoNumbers` 的类型大致是：

  Nat → Nat → Nat

注意这是一个默认右结合的运算，所以它的真正含义是：

  Nat → (Nat → Nat)

而不是

  (Nat → Nat) → Nat

因此：
-/

#check (addTwoNumbers : Nat → (Nat → Nat))

#check (addTwoNumbers : Nat → Nat → Nat)

#check (addTwoNumbers 3: Nat → Nat)

#check (addTwoNumbers 3 4 : Nat)

/-函数也可以省略函数名，直接给出函数映射，此时能看清函数的类型就是这个映射关系-/

#check (fun n : Nat => n + 1)

#eval (fun n : Nat => n + 1) 10

/-所以 Nat 和 Nat -> Nat 都是一种 Type，属于同一层级-/

/-!
`fun n : Nat => n + 1` 是匿名函数。
它没有名字，但依然是一个项，也依然有类型。
-/


/-!
===============================================================================
第 3 章：命题也是类型
===============================================================================

现在进入逻辑。

在日常语言里，我们说：

  “2 + 2 = 4” 是一个命题。
  “3 < 1” 是一个命题。
  “所有自然数都等于自己” 是一个命题。

命题可能真，也可能假。

在 Lean 中，命题的类型叫 `Prop`。
-/

#check True
#check False
#check (2 + 2 = 4)
#check (3 < 1)
#check (0 = 0)

/-!
你会看到：

  True : Prop
  False : Prop
  2 + 2 = 4 : Prop

这说明：

  True       是一个命题
  False      是一个命题
  2 + 2 = 4  是一个命题

而命题的“类型”是 `Prop`。

到这里先记住：

  数据类型属于 Type。
  命题属于 Prop。

  Nat  : Type
  Bool : Type

  True       : Prop
  2 + 2 = 4  : Prop
-/

/-!
先特别看 `True`。

`True` 不是布尔值 `true`。

  true : Bool
  True : Prop

小写 `true` 是一个可以参与计算的数据值。
大写 `True` 是一个命题，意思是“先天成立的命题”或“自带证明的命题”。

在 Lean 中，`True` 的结构可以近似理解成下面这个归纳定义：

  inductive True : Prop where
    | intro : True

这段定义包含两层意思：

1. `True : Prop`
   `True` 是一个命题。

2. `True.intro : True`
   `True.intro` 是这个命题的一个证明。

3. 注意 True.intro 的类型是 True，而不是 Prop，它是 True 的证明，而不是一个命题。

也就是说，`True` 这个命题之所以容易证明，是因为 Lean 已经给了
一个无参数构造器 `True.intro`。它不需要任何前提，直接构造出
`True` 的证明。

-/

#check (true : Bool)
#check (True : Prop)
#check (True.intro : True)
#check (fun _ : Unit => True.intro)

#check Prop
#check Type

/-!
`Prop` 自己也是一个类型层级里的对象。更准确地说：

  Prop : Type

Lean 使用宇宙层级来避免“所有类型的类型仍然是自己”这类悖论。
本文件后面会再慢慢解释。
这里首先要确认的是，Lean这个系统里，不是建立在命题真假的基础上的。
真(true)和假(false)只是数据类型 Bool 的两个值，
而命题 True 和 False 是 Prop 类型的两个命题。
True是自带证明的命题，而False没有任何证明。

False 的结构和 True 类似，但它连构造器都没有：

  inductive False : Prop where
    -- 没有构造器

这表示它形式上不存在被证明的方法，所以它是一个“永不成立的命题”。

-/

/-!
===============================================================================
第 4 章：证明是什么？
===============================================================================

Lean 的核心观点：

  一个命题如果有证明，就表示这个命题成立。

但是 Lean 不把证明看成一段自然语言解释。
Lean 把证明看成一个“项”。

也就是说，如果：

  P : Prop

那么：

  h : P

表示 h 是命题 P 的一个证明。

这和普通数据非常相似：

  5 : Nat

表示 5 是 Nat 类型的一个项。因此自然数的存在性得到了证明。

对应地：

  h : 2 + 2 = 4

表示 h 是命题 `2 + 2 = 4` 的一个证明。先不要管它具体应该是什么。

从这个角度，我们可以看到 True 的证明就是 `True.intro`，因此指出就可以了。

-/

def proofOfTrue : True :=
  True.intro

/-类型上看，这确实是命题 True 的一个证明-/
#check proofOfTrue

#check (proofOfTrue : True)

#check True.intro

#check (True.intro : True)

/-!
上面已经看过，`True` 是最简单的命题。
它的证明可以由构造器 `True.intro` 直接生成。

这正是“命题是类型，证明是对应类型的项”的例子。
-/

def proofTwoPlusTwo : 2 + 2 = 4 :=
  rfl

def addZeroByRfl (n : Nat) : n + 0 = n :=
  rfl

#check proofTwoPlusTwo

/-!
这里 `rfl` 是 reflexivity（自反性）的缩写。它是所有形如
“自己和自己相等” 这样的命题族的自带证明。

它能证明“左右两边计算后完全相同”的等式。
例如 `2 + 2` 计算后就是 `4`，所以 `rfl` 可以证明：

  2 + 2 = 4

`rfl` 还可以证明：

  n + 0 = n

这是因为 Lean 中自然数加法 `Nat.add` 的定义会对第二个参数递归。
当第二个参数是 `0` 时，`n + 0` 会按定义直接化简成 `n`。
所以第一个式子和第二个式子在 Lean 看来是“定义上相同”的。

但这不表示 `rfl` 会做所有代数推理。比如：

  0 + n = n

对变量 `n` 来说，左边不会仅靠展开定义直接变成右边。这个命题当然是真的，
但通常需要归纳、已有定理或 `simp`。

因此，
def proofTwoPlusTwo : 2 + 2 = 4 :=
  rfl
这个证明相当于说，因为 `2 + 2` 和 `4` 在 Lean 看来是定义上相同的，所以它们相等。

这个就好像我们说 True.intro 是 True 的证明一样。

这里 rfl 和 True.intro 都是基本构造器，它们都是 Lean 语言的基本规则，可以直接使用。
-/

-- 取消下面这个定义的注释会报错：`rfl` 不能直接证明这个方向。
-- def zeroAddByRflFails (n : Nat) : 0 + n = n :=
--   rfl

/-当然也有复杂的情况，需要使用归纳法或其他策略来证明。这个证明我们先不需要了解它的每一个细节：-/

theorem zeroAddByInduction (n : Nat) : 0 + n = n := by
  induction n with
  | zero =>
      rfl
  | succ n ih =>
      simp [ih]


/-
这就是一个归纳法的基本证明。它分两种情况：

  第一种情况：n = zero

  | zero =>
      rfl

  这里要证明：

  0 + 0 = 0

  这个可以直接计算，所以 rfl 证明。

  第二种情况：succ n ih

  | succ n ih =>
      simp [ih]

  这里表示：假设当前自然数是 Nat.succ n，也就是 n + 1。
  Lean 给你两个东西：

  n  : Nat
  ih : 0 + n = n

  其中 ih 是 induction hypothesis，归纳假设。

  也就是说，在证明：

  0 + (n + 1) = n + 1

  时，你可以使用已经知道的：

  ih : 0 + n = n

  succ n ih => 的意思就是：

  在后继情况中：
  - n 是前一个自然数
  - ih 是对 n 已经成立的归纳假设

  然后：

  simp [ih]

  表示：

  用 Lean 的简化器 simp 简化目标，并允许它使用归纳假设 ih。

  直观过程是：

  需证：0 + (Nat.succ n) = Nat.succ n

  Lean 根据自然数加法定义，把左边化简为：

  Nat.succ (0 + n) = Nat.succ n

  再用归纳假设：

  ih : 0 + n = n

  把目标：
  Nat.succ (0 + n) = Nat.succ n
  中的 0 + n 改成 n，目标变成：

  Nat.succ n = Nat.succ n，

  而这个由自反性显然成立。

  到此是 simp [ih] 的作用，包括最后一步自反性的使用。
  -/

/-!
===============================================================================
第 5 章：命题即类型，证明即项
===============================================================================

现在可以说出 Lean 逻辑的中心思想：

  命题就是类型。
  证明就是这个类型的项。

这句话叫 Curry-Howard 对应。
你不需要先知道这个名字，只需要看下面的类比：

  普通编程：

    7 : Nat

    Nat 是类型。
    7 是这个类型的项。

  逻辑证明：

    proofOfTrue : True

    True 是命题，也被 Lean 看成一种类型。
    proofOfTrue 是这个命题的证明，也就是这个类型的项。

如果一个命题没有任何项，那么它没有证明。
如果一个命题有项，那么它有证明。
因此在 lean 中，命题是否有证明是比命题真假更加基础的概念。
相应真命题可以看作有证明的命题，而如果我们说 P 是假命题，
可以看作 ¬P 有证明。

不能认为没有证明的命题是假的。这只是命题的当前状态。
-/

#check (True : Prop)
#check (True.intro : True)

/-!
`False` 是最简单的假命题。
它没有构造方式，所以你无法直接写出：

  def bad : False := ...

除非你已经有了矛盾。
-/

-- 下面这行如果取消注释，会发现无法填出右边：
-- def impossible : False := _

-- False 可以被证明的唯一方式是从矛盾出发。这个其实就是爆炸原理。

def contradictionExample (h : 1 = 2) : False := by
  cases h

#check contradictionExample


/-!
===============================================================================
第 6 章：普通数据类型也是“由构造器制造出来”的
===============================================================================

为了理解 True 和 False，先看普通数据类型。

Lean 中很多类型是 inductive type（归纳类型）。
归纳类型通过列出“构造器”来说明怎样制造它的值。
-/

inductive MyUnit : Type where
  | unit : MyUnit
  deriving Repr

#check MyUnit
#check MyUnit.unit
#eval MyUnit.unit


/-!
`MyUnit` 只有一个构造器 `MyUnit.unit`。
所以它只有一个值。

  inductive MyUnit : Type where

  意思是：定义一个新的归纳类型，名字叫 MyUnit，它本身是一个普通类型：

  MyUnit : Type

  可以检查：

  #check MyUnit
  -- MyUnit : Type

  接着：

  | unit : MyUnit

  这是它的构造器。意思是：unit 可以构造出一个 MyUnit 类型的项。

  完整名字是：

  MyUnit.unit

  检查：

  #check MyUnit.unit
  -- MyUnit.unit : MyUnit

  因为 MyUnit 只有这一个构造器，而且这个构造器不需要任何参数，所以 MyUnit 只有一个基本值。

  类比标准库里的 Unit：

  #check ()
  Unit 是 Lean 内置的“只有一个值”的类型；你这里定义的 MyUnit 是自己写的类似版本。

  最后：

  deriving Repr

  意思是：让 Lean 自动为 MyUnit 生成一个 Repr 实例，这样它就可以被 #eval 显示出来。

  如果没有：

  deriving Repr

  你仍然可以写：

  #check MyUnit.unit

  但：

  #eval MyUnit.unit

  可能无法显示，因为 Lean 不知道如何把它打印成人能看的字符串。

  加上 deriving Repr 后：

  #eval MyUnit.unit
  -- MyUnit.unit

  整体理解：

  inductive MyUnit : Type where
    | unit : MyUnit
    deriving Repr

  定义了一个类型：

  类型名：MyUnit
  所在宇宙：Type
  构造器：MyUnit.unit
  构造器类型：MyUnit.unit : MyUnit
  值的数量：只有一个基本值
  可显示：因为 deriving Repr

  它和 True 很像，但处在不同宇宙：

  MyUnit : Type
  MyUnit.unit : MyUnit

  True : Prop
  True.intro : True

  区别：

  - MyUnit 是普通数据类型
  - True 是命题
  - MyUnit.unit 是数据值
  - True.intro 是证明项

  所以可以类比：

  MyUnit 是 Type 里的“只有一个值”的类型。
  True 是 Prop 里的“只有一个证明”的命题。
--/

def a : MyUnit := MyUnit.unit
def b : MyUnit := MyUnit.unit
#check a
#check b
#eval a
#eval b

/- MyUnit 只有一个值，所以 a 和 b 总是相等的。-/
example : a = b := rfl

/- Lean 内置的 Unit 类型也只有一个值。比如没有参数的函数，
可以用它表达。-/

def c : Unit := Unit.unit
def d : Unit := ()

/--
现在定义一个类似 Bool 的类型。
-/

inductive MyBool : Type where
  | false : MyBool
  | true : MyBool
  deriving Repr

#check MyBool.false
#check MyBool.true
#eval MyBool.false
#eval MyBool.true

/-!
`MyBool` 有两个构造器，所以有两个基本值。
-/

def myNot (b : MyBool) : MyBool :=
  match b with
  | MyBool.false => MyBool.true
  | MyBool.true => MyBool.false

#eval myNot MyBool.false
#eval myNot MyBool.true

/-!
`match` 的意思是：

  看输入是哪个构造器造出来的，然后分情况处理。
  | MyBool.false => MyBool.true
  | MyBool.true => MyBool.false


再看一个没有构造器的类型。
-/

inductive MyEmpty : Type where
  -- 没有任何构造器。

#check MyEmpty

-- def impossible : MyEmpty := _



/-!
`MyEmpty` 没有构造器，所以你无法制造 `MyEmpty` 类型的值。

普通数据类型里：

  MyUnit   有一个值
  MyBool   有两个值
  MyEmpty  没有值

命题世界里也有类似结构：

  True   有一个明显证明
  False  没有证明
-/

-- MyEmpty 没有构造器，本质上是自定义的 False
def MycontradictionExample (h : 1 = 2) : MyEmpty := by
  cases h


/-!
===============================================================================
第 7 章：True 和 False 的结构
===============================================================================

回顾 Lean 标准库中，`True` 大致像这样：

  inductive True : Prop where
    | intro : True

这表示：

  True 是一个命题。
  True.intro 是 True 的一个证明。

而 `False` 大致像这样：

  inductive False : Prop where
    -- 没有构造器

这表示：

  False 是一个命题。
  没有任何直接方法可以制造 False 的证明。
-/

#print True
#print False

def trueProofAgain : True :=
  True.intro

def anotherTrueProof : True :=
  trivial

/-!
`trivial` 是一个策略(tactic)。这里它自动完成了 True 的证明。
策略可以看成“帮助你构造证明项的小程序”。
这个tactic的作用是：如果目标是 True，那么它直接给出 True.intro 作为证明。

后面会专门讲 `by` 和策略。
-/


/-!
===============================================================================
第 8 章：函数类型和蕴含
===============================================================================

普通编程中：

  A → B

表示从 A 到 B 的函数类型。

逻辑中：

  P → Q

读作“如果 P，那么 Q”。

Lean 把这两件事统一起来：

  证明 P → Q，就是写一个函数：
  输入 P 的证明，输出 Q 的证明。

这就是第一次真正看到“证明即程序”。
-/

/-这是一个自然数的恒等函数-/
def identityFunctionOnNat : Nat → Nat :=
  fun n => n

#eval identityFunctionOnNat 5

/-!
上面是普通函数：

  输入 n : Nat
  输出 n : Nat

现在看逻辑函数：命题 P 总是蕴含命题 P 自己。
-/

def identityProof (P : Prop) : P → P :=
  fun p => p

#check identityProof

/-!
解释：

  P : Prop

表示 P 是任意命题。

目标：

  P → P

表示“如果 P 成立，那么 P 成立”。

证明：

  fun p => p

表示：

  假设给我一个 p : P，
  那我直接返回 p。

这就是最基本的推理规则：假设可以直接使用。然后返回我要的结果类型的项，即完成了证明。
-/

/-在Hibert公理体系中，P->(Q->P) 是一个公理 -/
def ignoreSecondProof (P Q : Prop) : P → Q → P :=
  fun p _q => p

/-!
`P → Q → P` 读作：

  如果 P 成立，那么如果 Q 成立，那么 P 成立。

证明很简单：

  输入 p : P (已知 P 成立)
  输入 _q : Q (已知 Q 成立，但我们不需要它)
  返回 p (找到了 P 的成立的证据)

`_q` 前面的下划线表示：这个参数存在，但我不使用它。如果不写下划线会有一个警告，
因为 Lean 会认为你忘了使用这个参数。
-/

def implicationTransitive (P Q R : Prop) : (P → Q) → (Q → R) → (P → R) :=
  fun pq qr p => qr (pq p)

/-!
这是蕴含传递：

  如果 P 能推出 Q，(存在一个函数 pq : P → Q)
  如果 Q 能推出 R，(存在一个函数 qr : Q → R)
  那么 P 能推出 R。(需要证明存在一个函数 pr : P → R, 即已知 p : P, 可以得到 R 的证明)

逐步看：

  pq : P → Q
  qr : Q → R
  p  : P

  pq p      : Q (已知 p : P，pq 可以把它变成 Q 的证明，因此 pq p 是 Q 的证明)
  qr (pq p) : R (已知 pq p : Q，qr 可以把它变成 R 的证明，因此 qr (pq p) 是 R 的证明)

所以 `fun pq qr p => qr (pq p)` 就是整个定理的证明。
-/


/-!
===============================================================================
第 9 章：用 theorem 写同样的东西
===============================================================================

`def` 和 `theorem` 在这里的差别主要是意图：

  def     常用于定义数据或函数。
  theorem 常用于声明“这是一个命题的证明”。

下面两个写法表达的证明非常接近。
-/

def idAsDef (P : Prop) : P → P :=
  fun p => p

theorem idAsTheorem (P : Prop) : P → P :=
  fun p => p

#check idAsDef
#check idAsTheorem

/-!
Lean 关心的是右边是否真的构造出了左边类型要求的项。
如果左边是一个命题，那么右边就是这个命题的证明。
-/


/-!
===============================================================================
第 10 章：by 块和策略
===============================================================================

直接写 `fun p => p` 叫写证明项。

Lean 也允许你用 tactic（策略）一步步构造证明。
策略写在 `by` 后面。
-/

theorem idByTactic (P : Prop) : P → P := by
  intro p  -- 已知 P 成立，得到一个证明 p : P
  exact p  -- 直接用 p 作为证明完成目标

/-!
解释：

  intro p

把目标 `P → P` 的前提引入，得到一个假设：

  p : P

新目标变成：

  P

然后：

  exact p

告诉 Lean：目标正好就是 p 的类型，所以用 p 完成证明。

策略只是另一种写证明的方式。
它背后仍然是在构造一个项，类似：

  fun p => p
-/

theorem transByTactic (P Q R : Prop) : (P → Q) → (Q → R) → P → R := by
  intro pq
  intro qr
  intro p
  exact qr (pq p)

/-!
你可以把这段策略逐行读成：

  假设 pq : P → Q
  假设 qr : Q → R
  假设 p  : P
  那么 pq p 得到 Q
  再用 qr 得到 R
-/


/-!
===============================================================================
第 11 章：合取 And，也就是“并且”
===============================================================================

`P ∧ Q` 读作：

  P 并且 Q

要证明 `P ∧ Q`，必须同时给出：

  P 的证明
  Q 的证明

Lean 中 `P ∧ Q` 的构造器是 `And.intro`。
-/

def makeAnd (P Q : Prop) : P → Q → P ∧ Q :=
  fun p q => And.intro p q


/-!
也可以写成尖括号：

  ⟨p, q⟩

这只是 `And.intro p q` 的简写。
-/

def makeAndShort (P Q : Prop) : P → Q → P ∧ Q :=
  fun p q => ⟨p, q⟩

/-!
如果已有：

  h : P ∧ Q

那么可以取出左边证明和右边证明：

  h.left  : P
  h.right : Q
-/

def takeLeft (P Q : Prop) : P ∧ Q → P :=
  fun h => h.left

def takeRight (P Q : Prop) : P ∧ Q → Q :=
  fun h => h.right

def andCommutative (P Q : Prop) : P ∧ Q → Q ∧ P :=
  fun h => ⟨h.right, h.left⟩

/-!
这就是合取交换律：

  如果 P 且 Q，
  那么 Q 且 P。
-/

/-策略 (tactic) 的动机不是让证明更加简单，而是提供另一种构造证明的方式，
让证明更加直观，可读。-/

theorem andCommutativeByTactic (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h  -- 已知 P ∧ Q 有证据 h
  constructor  -- 有定义，需证 Q 和 P 都成立，所以拆成两个小目标：
               -- 1. 证明 Q
               -- 2. 证明 P
  exact h.right  -- h.right 是 Q 的证明，完成第一个小目标
  exact h.left   -- h.left 是 P 的证明，完成第二个小目标

/-!
策略版解释：

  intro h

得到：

  h : P ∧ Q

目标：

  Q ∧ P

  constructor

把目标拆成两个小目标：

  1. Q
  2. P

然后分别用：

  h.right : Q
  h.left  : P
-/


/-!
===============================================================================
第 12 章：析取 Or，也就是“或者”
===============================================================================

`P ∨ Q` 读作：

  P 或者 Q

要证明 `P ∨ Q`，不需要同时证明 P 和 Q。
只要证明其中一个就够了。

Lean 中有两个构造器：

  Or.inl p : P ∨ Q     如果你有 p : P
  Or.inr q : P ∨ Q     如果你有 q : Q
-/

def makeOrLeft (P Q : Prop) : P → P ∨ Q :=
  fun p => Or.inl p

def makeOrRight (P Q : Prop) : Q → P ∨ Q :=
  fun q => Or.inr q

/-!
使用析取时，必须分情况讨论：

  如果 h 是左边来的，就按 P 的情况处理。
  如果 h 是右边来的，就按 Q 的情况处理。
-/

/-已知 P Q R 是命题，且 P ∨ Q，P → R 和 Q → R 都成立，那么 R 也成立。-/
/-函数式写法-/
def useOr (P Q R : Prop) : P ∨ Q → (P → R) → (Q → R) → R :=
  fun h pr qr =>  -- h 是 P ∨ Q 的证明，pr 是 P → R 的证明，qr 是 Q → R 的证明
    match h with  -- h 是 P ∨ Q 的证明，则要么存在 P 的证明，要么存在 Q 的证明
    | Or.inl p => pr p  -- 如果 h 是 Or.inl p，说明有 P 的证明 p，于是 pr p 是 R 的证明
    | Or.inr q => qr q  -- 如果 h 是 Or.inr q，说明有 Q 的证明 q，于是 qr q 是 R 的证明

/-!
解释：

  h  : P ∨ Q
  pr : P → R
  qr : Q → R

如果 h 是 `Or.inl p`，说明有 p : P，于是 `pr p : R`。
如果 h 是 `Or.inr q`，说明有 q : Q，于是 `qr q : R`。
-/
/-tactic 写法，注意连词是我脑补的，lean 不需要连词-/
theorem useOrByTactic (P Q R : Prop) (h : P ∨ Q) (pr : P → R) (qr : Q → R) : R := by
  cases h with  -- 很直接吧，对 h 的来源讨论
  | inl p =>      -- 若 h 是 inl p，说明有 p : P
      exact pr p    -- 则 pr p 是 R 的证明
  | inr q =>      -- 若 h 是 inr q，说明有 q : Q
      exact qr q    -- 则 qr q 是 R 的证明

/-!
`cases h` 对 h 的来源做情况分析。
这是析取的“使用规则”。
-/

/-这里 ∧ 和∨ 其实都是记号，真正的构造器是 And 和 Or。 -/
/-从形式上， Or 和 And 都可以看成是函数类型的特殊情况，
输入两个命题 P 和 Q，输出一个命题。
不过它们的构造器和使用规则不同，也就是合取和析取的具体构造，
所以我们把它们单独拿出来讲。
-/

/-!
===============================================================================
第 13 章：False、矛盾和爆炸原理
===============================================================================

`False` 是没有证明的命题。

如果你真的拿到了：

  f : False

那说明上下文已经矛盾了。
在矛盾上下文里，可以推出任何命题。

经典逻辑里这叫爆炸原理：

  False → P

错误的前提可以得到任何结论。
-/

/-已知 P 是命题，若 False 成立，那么 P 也成立。-/
def falseElimExample (P : Prop) : False → P :=
  fun f => False.elim f

/-!
为什么这合理？

False 是一个类型，但
因为 `False` 没有构造器，所以 `f : False` 这种输入永远不会在正常情况下出现。
一个函数如果输入永远不可能出现，它就可以“返回任何类型”。

Lean 的 `False.elim f` 表示：

  从矛盾 f 出发，得到任何目标。这和 True.intro 是一样的道理，都是基本构造器，直接用。
-/

def falseImpliesTrue : False → True :=
  fun f => False.elim f

def falseImpliesAnyNat : False → Type 22 :=
  fun f => False.elim f

/-!
第二个例子返回 Nat，不是 Prop。
第三个例子更是扯淡。
这只是说明“矛盾真的什么都能推出”。
但是你无法真正调用它，因为你无法正常构造出 `False` 的证明。
-/


/-!
===============================================================================
第 14 章：否定 Not
===============================================================================

`¬ P` 读作“非 P”。

在 Lean 中，否定不是一个神秘的新概念。
它只是下面这个函数类型的简写：

  P → False

也就是说：

  ¬ P

表示：

  如果 P 成立，就会推出 False。
-/

/- ¬ 也是记号，对应的构造是 Not ，它确实可以看成一个函数-/
#check Not
#check (Not : Prop → Prop)

#eval (Not True) = False

-- ¬P 是 P → False 的简写
-- ¬ False 就是 False → False 的简写

def notFalse : ¬ False :=
  fun f => f  -- 假如 False 有证明 f，那么就直接返回这个证明 f 就好了。因为目标就是 False。
-- 这里 f 并不是 False 的证明，而只是一个假设。

-- 这个证明逻辑和 P -> P 是一样的，都是假设一个证明，然后直接返回这个证明。
def sameAsIdentityProof : P → P :=  -- 这里缩写了 P : Prop，表示对任意命题 P 都成立
  fun f => f

example : False -> False := fun f => f

/-!
`notFalse` 的目标是：

  ¬ False

展开后就是：

  False → False

所以证明就是：

  fun f => f
-/

-- 自相矛盾(P ∧ ¬P)蕴含 False
def contradictionFromPAndNotP (P : Prop) : P ∧ ¬ P → False :=
  fun h => h.right h.left -- h.right 作用在 h.left 上，得到 False，二者不可交换

/-!
逐步看：

  h       : P ∧ ¬ P
  h.left  : P
  h.right : ¬ P, 它是 P -> False 的函数

而 `¬ P` 展开就是：

  P → False

所以：

  h.right h.left : False
-/

/-! 上面的命题的另一种写法就是排中律 em -/
def notBothPAndNotP (P : Prop) : ¬ (P ∧ ¬ P) :=
  --要证 P ∧ ¬ P -> False
  fun h => h.right h.left

/-!
这就是矛盾律的一种形式：

  P 和 非 P 不可能同时成立。
-/


/-!
===============================================================================
第 15 章：等价 Iff，也就是“当且仅当”
===============================================================================

`P ↔ Q` 读作：

  P 当且仅当 Q

意思是两边可以互相推出：

  P → Q
  Q → P

Lean 中可以用 `Iff.intro` 构造等价。
-/

def iffRefl (P : Prop) : P ↔ P :=
  Iff.intro
    (fun p => p)
    (fun p => p)

def iffSymmExample (P Q : Prop) : (P ↔ Q) → (Q ↔ P) :=
  fun h => Iff.intro h.mpr h.mp

def andCommIff (P Q : Prop) : P ∧ Q ↔ Q ∧ P :=
  Iff.intro
    (fun h => ⟨h.right, h.left⟩)
    (fun h => ⟨h.right, h.left⟩)

/-!
如果：

  h : P ↔ Q

那么：

  h.mp  : P → Q
  h.mpr : Q → P

名字含义：

  mp  = modus ponens，正向使用
  mpr = modus ponens reversed，反向使用
-/


/-!
===============================================================================
第 16 章：全称量词 forall
===============================================================================

`∀ x : A, P x` 读作：

  对所有 x : A，P x 成立。

在 Lean 中，全称量词本质上是依赖函数类型。

普通函数：

  Nat → Nat

输入 Nat，输出 Nat。

全称证明：

  ∀ n : Nat, n = n

输入一个自然数 n，输出 `n = n` 的证明。
-/

def everyNatEqualsItself : ∀ n : Nat, n = n :=
  fun _ => rfl

#check everyNatEqualsItself
#check everyNatEqualsItself 0
#check everyNatEqualsItself 10

/-!
`everyNatEqualsItself 10` 的类型是：

  10 = 10

所以它是命题 `10 = 10` 的证明。
-/

def applyForallExample (h : ∀ n : Nat, n = n) : 5 = 5 :=
  h 5

/-!
使用全称命题就是函数应用。

  h : ∀ n : Nat, n = n

给它一个具体输入 5：

  h 5 : 5 = 5
-/

def predicateExample (n : Nat) : Prop :=
  n = 0

#check predicateExample
#check predicateExample 0
#check predicateExample 3

/-!
`predicateExample : Nat → Prop`

这叫谓词：输入一个数据，输出一个命题。

  predicateExample 0  是命题 `0 = 0`
  predicateExample 3  是命题 `3 = 0`

前者可证明，后者不可用 rfl 证明。
-/

def zeroSatisfiesPredicate : predicateExample 0 :=
  rfl


/-!
===============================================================================
第 17 章：存在量词 exists
===============================================================================

`∃ x : A, P x` 读作：

  存在某个 x : A，使得 P x 成立。

要证明存在命题，你需要给两样东西：

1. 一个具体见证 witness
2. 这个 witness 满足性质的证明

例如：

  ∃ n : Nat, n = 3

证明方式是：

  见证：3
  证明：3 = 3
-/

def existsThree : ∃ n : Nat, n = 3 :=
  Exists.intro 3 rfl

/-!
也可以用尖括号写：
-/

def existsThreeShort : ∃ n : Nat, n = 3 :=
  ⟨3, rfl⟩

def existsDoubleThree : ∃ n : Nat, n + n = 6 :=
  ⟨3, rfl⟩

/-!
使用存在证明时，需要拆开：

  h : ∃ n : Nat, P n

它里面有：

  一个 n
  一个证明 hn : P n

但是注意：在 Lean 的 `Prop` 中，存在证明主要用于继续证明命题。
一般不能把 `Prop` 中的存在证明当作可计算数据随便取出来运行。
这是 Lean 区分“证明”和“程序数据”的重要设计。
-/

def useExistsToProveTrue (h : ∃ n : Nat, n = 3) : True :=
  Exists.elim h (fun _n _hn => True.intro)

def useExistsToProveSelf (h : ∃ n : Nat, n = 3) : ∃ m : Nat, m = 3 :=
  Exists.elim h (fun n hn => ⟨n, hn⟩)


/-!
===============================================================================
第 18 章：等式
===============================================================================

等式 `a = b` 也是命题。

最基本的等式证明是：

  rfl

它证明“一个东西等于它自己”，或者“左右两边计算后一样”。
-/

def eqReflNat (n : Nat) : n = n :=
  rfl

def eqCalculation : 1 + 2 = 3 :=
  rfl

/-!
如果有 `h : a = b`，可以把方向反过来：
-/

def eqSymmNat (a b : Nat) : a = b → b = a :=
  fun h => Eq.symm h

/-!
如果有：

  h1 : a = b
  h2 : b = c

那么可以得到：

  a = c
-/

def eqTransNat (a b c : Nat) : a = b → b = c → a = c :=
  fun h1 h2 => Eq.trans h1 h2

/-!
等式还可以用于“替换”。

如果：

  h  : a = b
  pa : P a

那么可以把 `pa` 中的 a 替换成 b，得到：

  P b
-/

def eqSubstExample (P : Nat → Prop) (a b : Nat) (h : a = b) (pa : P a) : P b :=
  h ▸ pa

/-!
符号 `▸` 读作“根据等式改写”。
这是 Lean 中使用等式的核心能力。
-/


/-!
===============================================================================
第 19 章：Bool 和 Prop 不一样
===============================================================================

初学者很容易把 `Bool` 和 `Prop` 混在一起。

`Bool` 是普通数据类型，只有两个值：

  true  : Bool
  false : Bool

`Prop` 是命题的类型：

  2 + 2 = 4 : Prop
  True      : Prop
  False     : Prop

Bool 用来计算。
Prop 用来证明。
-/

def isEvenBool (n : Nat) : Bool :=
  n % 2 == 0

#eval isEvenBool 4
#eval isEvenBool 5

def isEvenProp (n : Nat) : Prop :=
  n % 2 = 0

#check isEvenProp
#check isEvenProp 4
#check isEvenProp 5

def fourIsEvenProof : isEvenProp 4 :=
  rfl

/-!
`isEvenBool 4` 会计算出 `true`。

`isEvenProp 4` 不是 true 或 false，而是一个命题：

  4 % 2 = 0

要让 Lean 接受它，需要给出证明。
这里 `rfl` 可以证明，因为 4 % 2 计算后就是 0。
-/


/-!
===============================================================================
第 20 章：类型宇宙 Type、Prop、Sort
===============================================================================

到现在为止，我们已经见过：

  5       : Nat
  Nat     : Type
  True    : Prop
  Prop    : Type

那么 `Type` 自己是什么类型？

Lean 不能让：

  Type : Type

无限自包含会导致悖论。

所以 Lean 使用宇宙层级：

  Type 0 : Type 1
  Type 1 : Type 2
  Type 2 : Type 3
  ...

平常写的 `Type` 通常可以理解成某个 `Type u`。
-/

#check Type
#check Type 0
#check Type 1
#check Prop
#check Sort 0
#check Sort 1

/-!
关系大致是：

  Prop   = Sort 0
  Type 0 = Sort 1
  Type 1 = Sort 2

你不需要一开始就熟练操纵宇宙层级。
先理解它为什么存在：

  它阻止“所有类型组成的类型又属于自己”这种危险循环。

在日常 Lean 证明中，大多数时候 Lean 会自动处理宇宙。
-/


/-!
===============================================================================
第 21 章：归纳类型和模式匹配
===============================================================================

逻辑连接词之所以能工作，是因为它们背后是归纳类型。

我们再看一个普通归纳类型，巩固“构造”和“拆解”的思想。
-/

inductive TrafficLight : Type where
  | red : TrafficLight
  | yellow : TrafficLight
  | green : TrafficLight
  deriving Repr

def nextLight (light : TrafficLight) : TrafficLight :=
  match light with
  | TrafficLight.red => TrafficLight.green
  | TrafficLight.yellow => TrafficLight.red
  | TrafficLight.green => TrafficLight.yellow

#eval nextLight TrafficLight.red
#eval nextLight TrafficLight.green

/-!
构造：

  TrafficLight.red
  TrafficLight.yellow
  TrafficLight.green

拆解：

  match light with
  | TrafficLight.red => ...
  | TrafficLight.yellow => ...
  | TrafficLight.green => ...

逻辑中的 `P ∨ Q` 也是类似的：

构造：

  Or.inl p
  Or.inr q

拆解：

  match h with
  | Or.inl p => ...
  | Or.inr q => ...
-/


/-!
===============================================================================
第 22 章：自然演绎规则的 Lean 版本
===============================================================================

自然演绎是一种组织逻辑推理规则的方法。
不需要先学形式逻辑术语，只要记住每个连接词有两类规则：

1. 引入规则：怎样证明它？
2. 消除规则：已经有它时，怎样使用它？

在 Lean 中，这些规则对应构造器、函数和模式匹配。

-------------------------------------------------------------------------------
命题 True
-------------------------------------------------------------------------------

引入：

  True.intro : True

消除：

  True 没有什么有用信息，所以一般不需要消除。

-------------------------------------------------------------------------------
命题 False
-------------------------------------------------------------------------------

引入：

  没有直接引入规则，因为 False 没有构造器。

消除：

  False.elim : False → P

-------------------------------------------------------------------------------
蕴含 P → Q
-------------------------------------------------------------------------------

引入：

  fun p => ...

也就是假设 p : P，然后构造 Q。

消除：

  如果 h : P → Q，且 p : P，
  那么 h p : Q。

-------------------------------------------------------------------------------
合取 P ∧ Q
-------------------------------------------------------------------------------

引入：

  ⟨p, q⟩

消除：

  h.left  : P
  h.right : Q

-------------------------------------------------------------------------------
析取 P ∨ Q
-------------------------------------------------------------------------------

引入：

  Or.inl p : P ∨ Q
  Or.inr q : P ∨ Q

消除：

  cases 或 match 分情况讨论。

-------------------------------------------------------------------------------
否定 ¬P
-------------------------------------------------------------------------------

定义：

  ¬P = P → False

所以证明 ¬P，就是假设 P，然后推出矛盾。

-------------------------------------------------------------------------------
等价 P ↔ Q
-------------------------------------------------------------------------------

引入：

  Iff.intro (P → Q 的证明) (Q → P 的证明)

消除：

  h.mp  : P → Q
  h.mpr : Q → P
-/


/-!
===============================================================================
第 23 章：构造式逻辑和经典逻辑
===============================================================================

Lean 的核心逻辑偏构造式。

构造式证明强调：

  要证明 P ∨ Q，就必须真的给出左边证明或右边证明。
  要证明 ∃ x, P x，就必须真的给出见证 x 和证明。

因此下面这个命题：

  P ∨ ¬ P

叫排中律。它在经典逻辑中成立，但在纯构造式逻辑中不是免费可得的。

Lean 允许你显式进入经典逻辑。
-/

theorem excludedMiddleClassical (P : Prop) : P ∨ ¬ P := by
  classical
  exact Classical.em P

/-!
`classical` 表示：接下来的证明允许使用经典逻辑原则。

这不是说经典逻辑“不好”，而是 Lean 希望你知道自己什么时候使用了它。

初学阶段可以先掌握构造式规则：

  fun
  函数应用
  And.intro / h.left / h.right
  Or.inl / Or.inr / cases
  False.elim
  Exists.intro / Exists.elim

这些已经足够理解 Lean 证明的大部分基本形状。
-/


/-!
===============================================================================
第 24 章：一个完整例子
===============================================================================

证明：

  如果 P 且 (Q 或 R)，
  并且 P → Q → S，
  并且 P → R → S，
  那么 S。

自然语言推理：

  假设 h : P ∧ (Q ∨ R)。
  从 h 取出 p : P。
  从 h 取出 qr : Q ∨ R。
  对 qr 分情况：

  - 如果有 q : Q，那么用 p 和 q 得到 S。
  - 如果有 r : R，那么用 p 和 r 得到 S。
-/

theorem completeExample
    (P Q R S : Prop)
    (h : P ∧ (Q ∨ R))
    (pqToS : P → Q → S)
    (prToS : P → R → S) :
    S := by
  have p : P := h.left
  have qr : Q ∨ R := h.right
  cases qr with
  | inl q =>
      exact pqToS p q
  | inr r =>
      exact prToS p r

/-!
这里出现了 `have`。

`have name : Type := value`

意思是先构造一个中间项，并给它命名。

  have p : P := h.left

就是从 h 中取出 P 的证明，并命名为 p。
-/


/-!
===============================================================================
第 25 章：练习
===============================================================================

下面的练习都注释掉了，所以本文件可以直接通过 Lean 检查。
你可以逐个取消注释，把右边补出来。

建议先用证明项写，再尝试改成 by 策略。
-/

/- 练习 1：假设可以直接使用

def ex1 (P : Prop) : P → P :=
  fun p => ?

-/

/- 练习 2：忽略不需要的假设

def ex2 (P Q : Prop) : P → Q → P :=
  fun p q => ?

-/

/- 练习 3：合取构造

def ex3 (P Q : Prop) : P → Q → P ∧ Q :=
  fun p q => ?

-/

/- 练习 4：合取交换

def ex4 (P Q : Prop) : P ∧ Q → Q ∧ P :=
  fun h => ?

-/

/- 练习 5：析取左引入

def ex5 (P Q : Prop) : P → P ∨ Q :=
  fun p => ?

-/

/- 练习 6：析取消除

def ex6 (P Q R : Prop) : P ∨ Q → (P → R) → (Q → R) → R :=
  fun h pr qr =>
    match h with
    | Or.inl p => ?
    | Or.inr q => ?

-/

/- 练习 7：否定就是推出 False

def ex7 (P : Prop) : P ∧ ¬ P → False :=
  fun h => ?

-/

/- 练习 8：等价构造

def ex8 (P Q : Prop) : (P → Q) → (Q → P) → (P ↔ Q) :=
  fun pq qp => ?

-/

/- 练习 9：全称量词

def ex9 : ∀ n : Nat, n = n :=
  fun n => ?

-/

/- 练习 10：存在量词

def ex10 : ∃ n : Nat, n + n = 8 :=
  ?

-/

/-!
===============================================================================
第 26 章：学习路线
===============================================================================

如果你完全从零开始，建议顺序是：

1. `Intro.lean`
   学会 `#eval`、`#check`、`def`、函数、结构体、模式匹配。

2. 本文件 `Logic.lean`
   理解 `项 : 类型`、`命题 : Prop`、`证明 : 命题`，
   以及逻辑连接词的构造和使用规则。

3. `Tutorial.lean`
   学习 tactic 风格证明，也就是用 `by`、`intro`、`exact`、
   `constructor`、`cases`、`rw`、`simp` 等命令更高效地写证明。

最重要的心法：

  不要把证明想成一段说服人的文字。
  在 Lean 中，证明首先是一个类型检查通过的项。

  目标是什么类型？
  当前有哪些项可以用？
  应该构造函数、构造合取、分情况，还是使用已有函数？

把每一步都翻译回 `x : A`，Lean 证明就会变得清楚很多。
-/

end LogicTutorial
