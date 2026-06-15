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
def x : Int := 42
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
-- #eval 无法判定全称量词命题的可计算性，这里应该用 #check
-- #eval (∀ n : Nat, n = n)

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

#check (0 : Int)
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

#check Nat -> Nat

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
/-这个是错误的，addTwoNumbers 需要一个函数，但 (3 4) 尝试将 3 当作函数使用 -/
-- #eval addTwoNumbers (3 4)

#check (addTwoNumbers : Nat → Nat → Nat)

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
第 3 章：命题也是类型 Prop
===============================================================================

现在进入逻辑。

在日常语言里，我们说：

  “2 + 2 = 4” 是一个命题。
  “3 < 1” 是一个命题。
  “所有自然数都等于自己” 是一个命题。

"命题可能真，也可能假。"

在 Lean 中，命题的类型叫 `Prop`。
-/

#check true
#check True   -- true
#check False  -- false
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
#check (True.intro : True)  -- 5 : NAT
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

  n + 0 = n  ->   n = n

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
--  rfl

/-当然也有复杂的情况，需要使用归纳法或其他策略来证明。这个证明我们先不需要了解它的每一个细节：-/

theorem zeroAddByInduction (n : Nat) : 0 + n = n := by
  induction n with
  | zero =>
      rfl
  | succ n ih =>  -- 0 + (n + 1) = n + 1
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

-- Unit 是一个只有一个值的类型，叫 ()。

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

def anotherTrueProof : True := by
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

  P → Q  , 已知P成立，那么 Q 成立。
            p : P, 从 p 构建 Q 的证据. ->  T(p) : Q

读作“如果 P，那么 Q”。

Lean 把这两件事统一起来：

  证明 P → Q，就是写一个函数：
  输入 P 的证明，输出 Q 的证明。

这就是第一次真正看到“证明即程序”。
-/

/-这是一个自然数的恒等函数-/
def identityFunctionOnNat : Nat → Nat :=
  fun n => n

-- n : Nat -> n : Nat

#eval identityFunctionOnNat 5

/-!
上面是普通函数：

  输入 n : Nat
  输出 n : Nat

现在看逻辑函数：命题 P 总是蕴含命题 P 自己。
P -> P
-/

def identityProof (P : Prop) : P → P :=
  fun p => p
   -- 已知P成立，则P有证明p, 那么p 也是 P的证明

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
-- P -> Q -> P, (p: P, q: Q) -> p : P

-- 已知 P 成立，那么如果 Q 成立，那么 P 成立。
-- 核心要掉是证明 P 成立，而已知条件是 P, Q 都成立。
-- 因此证明的目标是从 P, Q 的证明中得到 P 的证明。
def ignoreSecondProof (P Q : Prop) : P → Q → P := -- (p, q) ↦  p
  fun p _q => p   -- 这里 p 和 _q 自动匹配两个已知的证明，p : P, _q : Q
                  -- 因为我们不需要 Q 的证明，所以用 _q 来表示这个参数存在但不使用它。
                  -- 如果不写下划线，Lean 会警告你，因为它会认为你忘了使用这个参数。
/-!
`P → Q → P` 读作：

  如果 P 成立，那么如果 Q 成立，那么 P 成立。

证明很简单：

  输入 p : P (已知 P 成立)
  输入 _q : Q (已知 Q 成立，但我们不需要它)
  返回 p (找到了 P 的成立的证据)
-/

-- 已知 P->Q 和 Q->R 成立，求证 P->R，即求证如果 P 成立，则 Q 成立。 （传递性）
-- 因此已知条件其实是 P->Q, Q->R, P 成立，证明目标是 R 成立。
-- pq : (P → Q) → qr : (Q → R) → p : P →  ??? R
def implicationTransitive (P Q R : Prop) : (P → Q) → (Q → R) → P → R :=
  fun pq qr p => qr (pq p)  -- pq 匹配到 P->Q 的证明，qr 匹配到 Q->R 的证明，p 匹配到 P 的证明
                            -- pq 是 P -> Q 的证明，同时也是 P -> Q 的函数，因此 pq p 是 Q 的证明
                            -- qr 是 Q -> R 的证明，同时也是 Q -> R 的函数，因此 qr (pq p) 就是是 R 的证明
-- pq : P → Q, (pq p) : Q
-- qr (pq p) -> r: R


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

总结一下，命题即类型，证明即通过已知条件的证明（项），用函数来表达逻辑推理，最终得到结论的一个证明（项）。
-/


/-!
===============================================================================
第 9 章：用 theorem 和 example 写同样的东西
===============================================================================

`def`、`theorem` 和 `example` 在这里的差别主要是意图：

  def     常用于定义数据或函数。
  theorem 常用于声明“这是一个命题的证明”。
  example 常用于临时展示一个命题可以被证明，但不给它起全局名字。

下面三个写法表达的证明非常接近。
-/

/-命题映射的角度看，函数即证明-/
def idAsDef (P : Prop) : P → P :=
  fun p => p

/-一个命题间的映射对应我们经典逻辑中的定理-/
theorem idAsTheorem (P : Prop) : P → P :=
  fun p => p

/-省略了定理名或函数名，就是 example，它可以用来快速展示一个命题（一条逻辑链）可以被证明，
但不给它起全局名字。-/
example (P : Prop) : P → P :=
  fun p => p




#check idAsDef
#check idAsTheorem

/-!
Lean 关心的是右边是否真的构造出了左边类型要求的项。
如果左边是一个命题，那么右边就是这个命题的证明。

`example` 的特点是：Lean 会检查这个证明，但不会把它注册成一个
可以在后面用名字调用的定理。它非常适合讲义、草稿和小练习。

例如下面这个命题通过检查后，后面并没有一个叫 `thisExample` 的全局名字：
-/

example : 2 + 2 = 4 :=
  rfl

/-!
所以你可以频繁使用 `example` 来确认自己理解的推理规则，而不用担心污染全局命名空间：
-/

example (P Q : Prop) : P → Q → P :=
  fun p _q => p

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

example (P : Prop) : P → P := by
  intro p
  exact p

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
--  intro pq qr p
  intro pq qr
  intro p
  exact qr (pq p)

/-!
你可以把这段策略逐行读成：

  假设 pq : P → Q
  假设 qr : Q → R
  假设 p  : P
  那么 pq p 是 Q 的证明
  而 qr (pq p) 就是 R 的证明
-/


/-!
===============================================================================
第 11 章：合取 And，也就是“并且”
===============================================================================

`P ∧ Q` 读作：

  P 并且 Q

要证明 `P ∧ Q`，必须同时给出：

  p : P 的证明
  q :Q 的证明

Lean 中 `P ∧ Q` 的构造器是 `And.intro`。
-/

-- 已知 P 和 Q 都成立，那么 P ∧ Q 也成立。
def makeAnd (P Q : Prop) : P → Q → P ∧ Q :=
  fun p q => And.intro p q  -- 这里 p : P 是 P 的证明，q : Q 是 Q 的证明
                            -- 因此 And.intro p q 就是 P ∧ Q 的证明

/-!
也可以写成尖括号：

  ⟨p, q⟩

这只是 `And.intro p q` 的简写。
-/

def makeAndShort (P Q : Prop) : P → Q → P ∧ Q :=
  fun p q => ⟨p, q⟩

example (P Q : Prop) (p : P) (q : Q) : P ∧ Q :=
  ⟨p, q⟩

example (P Q : Prop) : P -> Q -> P ∧ Q := by
  intro p q
  exact ⟨p, q⟩

/-!
如果已有：

  h : P ∧ Q   -> P 成立且 Q 成立

那么可以取出左边证明和右边证明：

  h.left  : P
  h.right : Q
-/

def takeLeft (P Q : Prop) : P ∧ Q → P :=
  fun h => h.left

example (P Q : Prop) : P ∧ Q → P := by
  intro h
  exact h.left

def takeRight (P Q : Prop) : P ∧ Q → Q :=
  fun h => h.right

def andCommutative (P Q : Prop) : P ∧ Q → Q ∧ P :=
  fun h => ⟨h.right, h.left⟩

example (P Q : Prop) (h : P ∧ Q) : Q ∧ P :=
  ⟨h.right, h.left⟩

example (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  exact ⟨h.right, h.left⟩


/-!
这就是合取交换律：

  如果 P 且 Q，
  那么 Q 且 P。
-/

/-策略 (tactic) 的动机不是让证明更加简单，而是提供另一种构造证明的方式，
让证明更加直观，可读。-/

/-比上面的 example 更加详细的策略版 -/
theorem andCommutativeByTactic (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h  -- 已知 P ∧ Q 有证据 h
  constructor  -- 由定义，需证 Q 和 P 都成立，所以拆成两个小目标：
               -- 1. 证明 Q
               -- 2. 证明 P
  exact h.right  -- h.right 是 Q 的证明，完成第一个小目标
  exact h.left   -- h.left 是 P 的证明，完成第二个小目标

/- 详略由人 -/
example (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h
  constructor
  exact h.right
  exact h.left

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

都可以作为 P ∨ Q 的证明。
-/

def makeOrLeft (P Q : Prop) : P → P ∨ Q :=
  fun p => Or.inl p

def makeOrRight (P Q : Prop) : Q → P ∨ Q :=
  fun q => Or.inr q

example (P Q : Prop) (p : P) : P ∨ Q :=
  Or.inl p

example (P Q : Prop) (q : Q) : P ∨ Q :=
  Or.inr q

example (P Q : Prop) : Q → P ∨ Q := by
  intro q
  exact Or.inr q


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
/-cases 这个策略相当于说，需要讨论-/
theorem useOrByTactic (P Q R : Prop) (h : P ∨ Q) (pr : P → R) (qr : Q → R) : R := by
  cases h with  -- 很直接吧，对 h 的来源讨论
  | inl p =>      -- 若 h 是 inl p，说明有 p : P
      exact pr p    -- 则 pr p 是 R 的证明
  | inr q =>      -- 若 h 是 inr q，说明有 q : Q
      exact qr q    -- 则 qr q 是 R 的证明

example (P Q R : Prop) (h : P ∨ Q) (pr : P → R) (qr : Q → R) : R := by
  cases h with
  | inl p =>
      exact pr p
  | inr q =>
      exact qr q

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

-- 什么妖魔鬼怪都可以
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

-- #eval 无法评估 Prop 级别的相等性，这里应该用 #check
#check (Not True) = False

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

-- 自相矛盾(P ∧ ¬P) 蕴含 False
def contradictionFromPAndNotP (P : Prop) : P ∧ ¬ P → False :=
  fun h => h.right h.left -- h.right 作用在 h.left 上，得到 False，二者不可交换

example (P : Prop) (h : P ∧ ¬ P) : False :=
  h.right h.left

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

/-! 上面的命题的另一种写法就是排中律 em 。-/
def notBothPAndNotP (P : Prop) : ¬ (P ∧ ¬ P) :=
  --要证 P ∧ ¬ P -> False
  fun h => h.right h.left

example (P : Prop) : ¬ (P ∧ ¬ P) :=
  fun h => h.right h.left

/-!
这就是矛盾律的一种形式：

  任何命题，P 和 非 P 不可能同时成立。
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

-- 我们可以用 #print 来观察一个结构的内部构造
#print Iff
-- Iff 的构造器 intro (函数)需要有两个参数，一个提供 P → Q 的证明，另一个提供 Q → P 的证明

-- 证明 P <-> P
def iffRefl (P : Prop) : P ↔ P :=
  Iff.intro  -- 直接给构造
    (fun p => p)  -- P -> P 的证明
    (fun p => p)  -- P <- P 的证明

-- 回顾： P -> P 的证明是 fun p => p
example (P : Prop) : P -> P :=
    (fun p => p)

-- 证明 P <-> Q 蕴含 Q <-> P
def iffSymmExample (P Q : Prop) : (P ↔ Q) → (Q ↔ P) :=
  fun h => Iff.intro h.mpr h.mp   -- h 是 P ↔ Q 的证明，h.mp 是 P -> Q 的证明，h.mpr 是 Q -> P 的证明
                                  -- 现在要从 h 提供一个 Q ↔ P 的证明，所以需要提供 Q -> P 和 P -> Q 的证明
                                  -- Q -> P 的证明就是 h.mpr，P -> Q 的证明就是 h.mp

-- h:(P  ↔ Q), h.mp : P -> Q, h.mpr : Q -> P
-- Q  ↔ P,  intro 需要 Q -> P 和 P -> Q 的证明, 分别是： h.mpr 和 h.mp
-- 可以更进一步，证明 P <-> Q 当且仅当 Q <-> P

example (P Q : Prop) : (P ↔ Q) ↔ (Q ↔ P) :=
  Iff.intro
    (fun h => Iff.intro h.mpr h.mp)
    (fun h => Iff.intro h.mpr h.mp)

-- 自己理解一下？
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

也就是说，P x 是一个依赖于 x 的命题，∀ x : A, P x 就是一个函数类型：

  输入一个 x : A
  输出一个 P x 的证明


普通函数：

  Nat → Nat

输入 Nat，输出 Nat。

全称证明：

  ∀ n : Nat, n = n

输入一个自然数 n，输出 `n = n` 的证明。而 n = n 本身是一个命题，证明它的项就是 rfl。
-/

-- 这是一个命题，要证明它，先要引入一个 n : Nat，消除全称量词，然后证明 n = n。
#check ∀ n : Nat, n = n

example : ∀ n : Nat, n = n := by
  intro n -- 引入一个 n : Nat，到这里上下文是 n : Nat,  n = n，相当于全称量词被消除了
  exact rfl  -- rfl 是 n = n 的证明，这是熟悉的


-- 对应函数式，相当于对参数 n，我们给了一个证明 n = n 的函数，
-- 这个函数对任何 n 都返回 rfl 作为证明。

def everyNatEqualsItself : ∀ n : Nat, n = n :=
  fun _ => rfl -- 这里 _ 是一个占位符，表示我们不关心 n 的具体值，因为 rfl 对任何 n 都成立。

example : ∀ n : Nat, n = n :=
  fun _ => rfl

-- 如果换成一个具体的项，比如 p，它也可以工作，但会有一个未使用的参数警告。
example : ∀ n : Nat, n = n :=
  fun p => rfl



-- 如果已知一个带全称量词的命题的证明，比如：
-- 已知 everyNatEqualsItself 是 ∀ n : Nat, n = n 的证明
#check (everyNatEqualsItself : ∀ n : Nat, n = n)
-- 那么我们可以得到一个具体命题的证明，比如 0 = 0：

#check everyNatEqualsItself
#check everyNatEqualsItself 0 -- 具体化成 0 = 0 的证明
#check everyNatEqualsItself 10 -- 具体化成 10 = 10 的证明

/-!
`everyNatEqualsItself 10` 的类型是：

  10 = 10

所以它是命题 `10 = 10` 的证明。

所以：

  全称量词的使用方式 = 函数应用
-/

-- 直接应用全称证明来得到一个具体命题的证明。
def applyForallExample (h : ∀ n : Nat, n = n) : 5 = 5 :=
  h 5  -- 这里 h 是一个函数，输入一个 n : Nat，输出 n = n 的证明，所以 h 5 就是 5 = 5 的证明

-- 也可以这样
example : 5 = 5 :=
  everyNatEqualsItself 5

/-!
使用全称命题就是函数应用。

  h : ∀ n : Nat, n = n

给它一个具体输入 5：

  h 5 : 5 = 5
-/


-- 这种带参数的命题还可以构建谓词关系：
-- 例如：一个自然数集上的一元谓词（关系、子集），是否为零。

def predicateExample (n : Nat) : Prop :=
  n = 0

#check predicateExample
#check predicateExample 0
#check predicateExample 3

-- 但在 Lean, 谓词关系只负责构造命题，不是一个直接判定，所以它的类型是 Prop，而不是 Bool。

/-!
`predicateExample : Nat → Prop`

这叫谓词：输入一个数据，输出一个命题。

  predicateExample 0  是命题 `0 = 0`
  predicateExample 3  是命题 `3 = 0`

前者可证明，后者不可用 rfl 证明。
-/

def zeroSatisfiesPredicate : predicateExample 0 :=
  rfl

example : predicateExample 0 :=
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

-- 可以利用 Exists.intro 构造存在证明
def existsThree : ∃ n : Nat, n = 3 :=
  Exists.intro 3 rfl

example : ∃ n : Nat, n = 3 :=
  Exists.intro 3 rfl

/-!
也可以用尖括号写：
-/

def existsThreeShort : ∃ n : Nat, n = 3 :=
  ⟨3, rfl⟩

def existsDoubleThree : ∃ n : Nat, n + n = 6 :=
  ⟨3, rfl⟩

example : ∃ n : Nat, n + n = 6 :=
  ⟨3, rfl⟩


-- 使用存在构造器要同时提供见证和证明 <见证，证明>
#print Exists

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

-- 已知 ∃ n : Nat, n = 3，那么它的一个证明 h ，包含一个具体的 n 和证明 n = 3 的 hn。
-- 这个例子只是展示如何从存在证明中提取信息，对证明 True 没什么实际意义。
-- 因为任何存在证明的命题都可以用来证明 True。
def useExistsToProveTrue (h : ∃ n : Nat, n = 3) : True :=
  Exists.elim h (fun _n _hn => True.intro) -- 用 Exists.elim 来处理存在证明，
                                           -- _n 是存在的 n，_hn 是 n = 3 的证明，
                                           -- 但我们实际上不需要它们，所以用 _n 和 _hn 来表示未使用的参数

-- 这是一个更合理的例子：已知 ∃ n : Nat, n = 3，
-- 那么我们可以从这个存在证明中提取出一个具体的 m，使得 m = 3。
def useExistsToProveSelf (h : ∃ n : Nat, n = 3) : ∃ m : Nat, m = 3 :=
  Exists.elim h (fun n hn => ⟨n, hn⟩) -- 不光匹配到 n 和 hn，还直接用它们构造了一个新的存在证明 ⟨n, hn⟩，
                                     -- 说明存在一个 m（就是 n）使得 m = 3（就是 hn）

example (h : ∃ n : Nat, n = 3) : ∃ m : Nat, m = 3 :=
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

example (n : Nat) : n = n :=
  rfl

example : 1 + 2 = 3 :=
  rfl

/-!
如果有 `h : a = b`，可以把方向反过来，
那么 Eq.symm h 就是 b = a 的证明。
等式有交换律。
-/

#print Eq

#print Eq.symm

#check Eq.symm

def eqSymmNat (a b : Nat) : a = b → b = a :=
  fun h => Eq.symm h  -- h : a = b 的证明，Eq.symm h 就是 b = a 的证明
                      -- 可以理解为：若 a = b，那么 b = a 也是成立的。

example (a b : Nat) (h : a = b) : b = a :=
  Eq.symm h



/-!
如果有：

  h1 : a = b
  h2 : b = c

那么可以得到：

  a = c

这个是等式的传递性，Lean 中对应的函数是 Eq.trans。
-/

def eqTransNat (a b c : Nat) : a = b → b = c → a = c :=
  fun h1 h2 => Eq.trans h1 h2

example (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c :=
  Eq.trans h1 h2

/-策略证明-/
example (a b c : Nat) : a = b -> b = c -> a = c := by
  intro h1
  intro h2
  exact Eq.trans h1 h2

/-!
等式还可以用于“替换”。

如果：

  h  : a = b
  pa : P a

那么可以把 `pa` 中的 a 替换成 b，得到：

  P b
-/

-- 已知 P 是一个关于 Nat 的谓词（Lean 中的谓词未必是子集判定），a, b 是自然数，
-- h 是 a = b 的证明，pa 是 P a 的证明，那么我们可以得到 P b 的证明。
def eqSubstExample (P : Nat → Prop) (a b : Nat) (h : a = b) (pa : P a) : P b :=
  h ▸ pa  -- 这里 h ▸ pa 的意思是根据等式 h 把 pa 中的 a 替换成 b，得到 P b 的证明

-- 顺便说一句，▸ 在 Lean 中是一个特殊的符号，叫做“根据等式改写”，它的作用就是把等式左边的东西替换成右边的东西。
-- 它的输入方法是 `\` 加 `t`

example (P : Nat → Prop) (a b : Nat) (h : a = b) (pa : P a) : P b :=
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

-- 是不是偶数，函数
def isEvenBool (n : Nat) : Bool :=
  n % 2 == 0

#eval isEvenBool 4
#eval isEvenBool 5

#check isEvenBool
#check (isEvenBool : Nat -> Bool)


-- 是不是偶数，命题
def isEvenProp (n : Nat) : Prop :=
  n % 2 = 0

-- 命题无法求值
-- #eval isEvenProp 4

#check isEvenProp
#check isEvenProp 4
#check isEvenProp 5

#check (isEvenProp : Nat -> Prop)

-- 要证明 4 是偶数，我们需要证明 isEvenProp 4 成立，也就是证明 4 % 2 = 0。
-- = 左边 4 % 2 计算后确实是 0，所以这个证明可以用 rfl 来完成 0 = 0 的证明。
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
我们的经典逻辑在这个环节上就有漏洞。

所以 Lean 使用宇宙层级：

  Type 0 : Type 1
  Type 1 : Type 2
  Type 2 : Type 3
  ...

平常写的 `Type` 通常可以理解成某个 `Type u`。u 是一个隐式参数，Lean 会自动推断它。
-/

#check Type
#check Type 0
#check Type 1
#check Prop
#check Sort
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

我们再看一个普通归纳类型，巩固“构造”和“拆解”的思想。
-/

-- 定义一个交通信号灯的类型，有三个构造器：红灯、黄灯、绿灯。它们都是 TrafficLight 的具体值（证明）。
inductive TrafficLight : Type where
  | red : TrafficLight
  | yellow : TrafficLight
  | green : TrafficLight
  deriving Repr  -- 让 TrafficLight 可以被打印

-- 定义一个函数，输入一个 TrafficLight 的值，输出下一个 TrafficLight 的值。
def nextLight (light : TrafficLight) : TrafficLight :=
  match light with  -- 对 light 的来源进行分析，看看它是哪个构造器来的
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

/-
  对于一个归纳类型，构造就是使用它的构造器制造项；
  如果这个类型是命题，那么制造项就是给出证明。

  拆解就是：在已经有一个该类型的项/证明项时，
  按照它可能由哪个构造器生成来使用它，或者取出构造器携带的信息。

  关键点：

  构造：从部件得到整体。
  拆解：从整体得到部件，或按整体的构造来源分情况。

  例如：

  And 构造：P 的证明 + Q 的证明 → P ∧ Q 的证明
  And 拆解：P ∧ Q 的证明 → P 的证明 和 Q 的证明

  Or 构造：P 的证明 → P ∨ Q 的证明
         或 Q 的证明 → P ∨ Q 的证明
  Or 拆解：P ∨ Q 的证明 → 分左、右两种情况讨论
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
  那么 h p : Q。 （将 h 看作一个函数，作用于 p，得到 Q 的证明）


-------------------------------------------------------------------------------
合取 P ∧ Q
-------------------------------------------------------------------------------

引入：

  ⟨p, q⟩  -- 也就是 And.intro p q, p 是 P 的证明，q 是 Q 的证明

P 和 Q 都要有证明。

消除：

  h.left  : P
  h.right : Q

已知 h : P ∧ Q，那么 h.left 就是 P 的证明，h.right 就是 Q 的证明。
已知 P ∧ Q，那么 P 和 Q 都成立，所以可以分别取出它们的证明。

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

叫排中律。它在经典逻辑中成立，但在纯构造式逻辑中不是免费可得的。即必须接受一个额外的公理。

Lean 允许你显式进入经典逻辑。
-/

theorem excludedMiddleClassical (P : Prop) : P ∨ ¬ P := by
  classical   -- 进入经典逻辑
  exact Classical.em P -- Classical.em 是排中律的证明（没有这个，构造式逻辑无法证明）

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

/-！

在19世纪末到20世纪初的数学“基础危机”中，数学家们试图为数学寻找一个绝对可靠的基础，由此诞生了三大流派。
以下是它们的核心思想与代表人物：

### 1. 逻辑主义

核心思想是：**数学可以完全归约为逻辑**。所有数学概念（如自然数、实数）都能通过纯粹的逻辑定义推导出来，
所有数学定理也都能从逻辑公理中证明。数学是逻辑的延伸和分支。

- **代表人物**：戈特洛布·弗雷格、伯特兰·罗素。弗雷格是奠基者，
罗素及其老师怀特海在巨著《数学原理》中进行了系统化的宏大尝试。
- **代表思想**：最著名的是罗素提出的**罗素悖论**，它直接动摇了康托尔集合论的基础，
并促使逻辑主义者发展出“类型论”来规避悖论。他们试图用逻辑符号构建整个数学大厦。

### 2. 直觉主义

核心思想是：**数学存在于人的直觉构造中**。数学对象并非独立于思维而存在，
而是心智根据直觉（特别是对自然数序列的“时间直觉”）构造出来的。
只有能被有限步骤构造出来的东西（例如能写出前100位的圆周率）才是数学对象。
因此，它坚决反对“实无穷”，只承认“潜无穷”，
并因此**禁止使用排中律**（即不承认一个命题非真即假，除非我们能构造地证明它）。

- **代表人物**：鲁伊兹·布劳威尔、阿伦特·海廷和利奥波德·克罗内克 (Leopold Kronecker)。
布劳威尔是创始人，海廷为其直觉主义逻辑给出了形式化系统。
- **代表思想**：布劳威尔的名言是**“存在即是被构造”**。
一个经典例子：在直觉主义看来，“存在无理数a和b使得a^b是有理数”这个经典证明（通过√2^√2来论证）是无效的，
因为它未具体构造出a和b分别是哪个数，仅利用了排中律。克罗内克是一位彻底的构造主义者，
其核心思想由一句名言完美概括：“上帝创造了整数，其余一切都是人造的。”

### 3. 形式主义

核心思想是：**数学是无需赋予意义的符号游戏**。数学本身不讨论点、线、数的“本质”，
而只讨论公理和推理规则下的符号变形。只要这个形式系统是**一致**（无矛盾）的，其数学内容就是合法的。
数学的真理性等价于系统内推演的一致性。

- **代表人物**：大卫·希尔伯特、约翰·冯·诺依曼。希尔伯特是领袖，提出了著名的“希尔伯特计划”。
- **代表思想**：**希尔伯特纲领**：试图将全部数学形式化，然后用有限的、有穷的方法证明整个数学系统的一致性。
这个雄心勃勃的计划最终被哥德尔的不完备性定理（即任何足够强的系统都无法证明自身无矛盾）所终结。

### 简要对比

| 流派 | 对“数学是什么”的回答 | 如何看待“无穷” |
| :--- | :--- | :--- |
| **逻辑主义** | 逻辑的延伸 | 接受实无穷（作为逻辑概念） |
| **直觉主义** | 心智的构造活动 | 只接受潜无穷，排斥实无穷 |
| **形式主义** | 纯粹的符号游戏 | 作为规则允许使用，但不追问其本体 |

这三大流派的争论虽然未能给数学找到一个公认的绝对基础，但极大深化了我们对数学逻辑、可计算性以及形式系统局限性的理解，
直接催生了数理逻辑的黄金时代。


Lean 4 更接近**逻辑主义**。它通过强大的“命题即类型”思想，在计算机中实践了逻辑主义的梦想，
同时也吸收了直觉主义的构造性内核。它与三大流派的具体关系如下：

**核心：逻辑主义**：在罗素的分支类型论和“数学原理”基础上，
通过更现代且实用的**依值类型论**为构造全部分数学提供了一个统一、内洽的逻辑框架。最具代表性的体现是**Curry-Howard 同构**（即“命题即类型，证明即程序”），它将数学、逻辑和计算完美统一，构建了一个庞大的形式化数学知识库（如Mathlib），切实还原了逻辑主义将数学建基于逻辑之上的初衷。
**实践原则：构造主义（源自直觉主义）**：默认遵循了**构造主义**的传统。
这意味着要证明一个命题存在，必须给出明确的构造实例，这与直觉主义的“存在即是被构造”思想完全吻合。
不过，Lean 4 并未强制要求绝对构造主义，它仍是一个务实的工具，
当需要经典数学理论时，可以通过 `by_contra` 或 `by_cases` 策略调用**排中律**，随时切换到经典数学模式。
**方法工具：形式主义**：完美体现了形式主义“符号游戏”的实践方法。
任何数学陈述都可以用其精确的形式语言表述，证明过程被视为在严密规则下对符号的转换，
整个过程由计算机机械地检查。从这个角度看，Lean 4 堪称希尔伯特“形式主义纲领”在数字时代的终极实现。
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
    (P Q R S : Prop)        -- 假设 P, Q, R, S 是任意命题
    (h : P ∧ (Q ∨ R))       -- 假设 h 是 P ∧ (Q ∨ R) 的证明，即已知 P 且 (Q 或 R) 成立
    (pqToS : P → Q → S)     -- 假设 pqToS 是一个函数，输入 P 的证明和 Q 的证明，输出 S 的证明，即 P 且 Q 蕴含 S
    (prToS : P → R → S) :   -- 假设 prToS 是一个函数，输入 P 的证明和 R 的证明，输出 S 的证明，即 P 且 R 蕴含 S
    S := by                 -- 需证明 S， 通过
  have p : P := h.left        -- 先从 h 中取出 P 的证明，并命名为 p (have)
  have qr : Q ∨ R := h.right  -- 先从 h 中取出 Q ∨ R 的证明，并命名为 qr (have)
  cases qr with               -- 对 qr 进行分情况讨论
  | inl q =>                  -- 如果 qr 是 Q 的证明 q，
      exact pqToS p q         -- 那么就用 p 和 q 通过 pqToS 可得到 S
  | inr r =>                  -- 如果 qr 是 R 的证明 r，
      exact prToS p r         -- 那么就用 p 和 r 通过 prToS 可得到 S

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
