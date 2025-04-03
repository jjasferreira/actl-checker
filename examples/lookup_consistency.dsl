(forall (i x y)
  (implies
    (lookup i (x) (y))
    (exists (j)
      (and
        (store j (x y) ())
        (before j i)
      )
    )
  )
)
