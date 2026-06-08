import Mathlib

-- 使用 mathlib 中的 norm_num 策略
example : 2 + 2 = 4 := by norm_num

-- 使用 mathlib 中的实数理论
example (x : ℝ) : x + 0 = x := by simp

-- 使用 mathlib 中的集合论
example (s t : Set Nat) : s ∩ t ⊆ s := by
  intro x hx
  exact hx.1

def main : IO Unit := IO.println "Mathlib is working!"
