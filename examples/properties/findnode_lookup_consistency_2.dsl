/* FindNode and Lookup Consistency */
(forall lookup l1 (n1 k1) (r1 v1)
  (exists responsible responsible (n2 k2) ()
    (n2 = r1)           // the responsible node matches the result of find
    (k1 = k2 )          // the node is responsible for the key
    (intersects l1 responsible)  // during a period where they intersect
  )
)
