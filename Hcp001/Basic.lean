import Std

namespace Hcp001

def vertexCount : Nat := 43

def baseDiffs : List Nat :=
  [1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21,
   22, 23, 25, 27, 29, 30, 31, 33, 36, 41, 42]

def deletedCycleIndices : List Nat :=
  [3, 4, 5, 6, 11, 12, 13, 14, 20, 21, 22, 23, 29, 30, 31, 37, 38, 39, 40]

def vertices : List Nat := List.range vertexCount

def unorderedPairs : List α → List (α × α)
  | [] => []
  | x :: xs => xs.map (fun y => (x, y)) ++ unorderedPairs xs

def combinations (k : Nat) (xs : List α) : List (List α) :=
  match k, xs with
  | 0, _ => [[]]
  | _ + 1, [] => []
  | k + 1, x :: rest =>
      (combinations k rest).map (fun ys => x :: ys) ++ combinations (k + 1) rest
termination_by xs.length

def countTrue (xs : List Bool) : Nat :=
  xs.foldl (fun total value => if value then total + 1 else total) 0

def baseEdge (u v : Nat) : Bool :=
  u != v && baseDiffs.contains ((v + vertexCount - u) % vertexCount)

def cycleIndex? (u v : Nat) : Option Nat :=
  if (v + vertexCount - u) % vertexCount == 1 then some u
  else if (u + vertexCount - v) % vertexCount == 1 then some v
  else none

def candidateEdge (u v : Nat) : Bool :=
  if !baseEdge u v then false
  else
    match cycleIndex? u v with
    | some i => !deletedCycleIndices.contains i
    | none => true

def edgeCountOn (vs : List Nat) : Nat :=
  countTrue ((unorderedPairs vs).map (fun edge => candidateEdge edge.1 edge.2))

def candidateEdgeCount : Nat := edgeCountOn vertices

def degree (u : Nat) : Nat :=
  countTrue (vertices.map (candidateEdge u))

def degrees : List Nat := vertices.map degree

def countNat (needle : Nat) (xs : List Nat) : Nat :=
  xs.foldl (fun total value => if value == needle then total + 1 else total) 0

def fiveSets : List (List Nat) := combinations 5 vertices

def k5Sets : List (List Nat) := fiveSets.filter (fun vs => edgeCountOn vs == 10)

def i5Sets : List (List Nat) := fiveSets.filter (fun vs => edgeCountOn vs == 0)

def expectedI5 : List (List Nat) :=
  [[3, 6, 7, 11, 12], [6, 7, 11, 12, 15]]

theorem candidate_edge_count : candidateEdgeCount = 454 := by
  native_decide

theorem candidate_degree_distribution :
    countNat 20 degrees = 14 ∧ countNat 21 degrees = 10 ∧ countNat 22 degrees = 19 := by
  native_decide

theorem candidate_has_no_k5 : k5Sets = [] := by
  native_decide

theorem candidate_has_exact_i5 : i5Sets = expectedI5 := by
  native_decide

#print axioms candidate_edge_count
#print axioms candidate_degree_distribution
#print axioms candidate_has_no_k5
#print axioms candidate_has_exact_i5

end Hcp001
