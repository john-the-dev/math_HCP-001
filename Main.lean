import Hcp001

open Hcp001

def main : IO Unit := do
  IO.println s!"candidate_edges={candidateEdgeCount}"
  IO.println s!"degree_counts=20:{countNat 20 degrees},21:{countNat 21 degrees},22:{countNat 22 degrees}"
  IO.println s!"candidate_K5={k5Sets.length} candidate_I5={i5Sets.length} F={k5Sets.length + i5Sets.length}"
  IO.println s!"candidate_I5_sets={repr i5Sets}"
