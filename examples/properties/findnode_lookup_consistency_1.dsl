/* FindNode and Lookup Consistency */
(forall findnode f1 (n1 k1) (- r1)
  (exists responsible responsible (n2 k2) ()
    (n2 = r1)           // the responsible node matches the result of find
    (k1 = k2 )          // the node is responsible for the key
    (intersects f1 responsible)  // during a period where they intersect
  )
)
