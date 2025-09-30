(forall lookup i1 (n1 k1) (n2 v1)
  (exists store i2 (n3 k1 v1) (n4)
    (and
      (not (before i1 i2))
      (not (meets i1 i2))
    )
  )
)