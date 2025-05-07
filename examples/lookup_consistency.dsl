(forall lookup i1 (n1 k1) (n2 v1)
  (implies (not (equal v1 'no_value))
    (exists store i2 (n3 k2 v2) (n4)
      (and
        (and
          (equal k1 k2)
          (equal v1 v2)
        )
        (and 
          (not (before i1 i2))
          (not (meets i1 i2))
        )
      )
    )
  )
)
