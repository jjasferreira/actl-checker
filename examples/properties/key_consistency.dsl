/* Key Consistency */
(forall findnode f1 (- k1) (- r1)
  (forall findnode f2 (- k2) (- r2) 
    (implies
      (and 
       (not (equals f1 f2)) // if the finds are different operations
       (k1 = k2) // and the finds are for the same key
       (exists ideal i () ()
          (or (in f1 i) (equals f1 i)) // and occur during an ideal state
          (or (in f2 i) (equals f2 i))
       )
       (exists stable s () ()
          (or (in f1 s) (equals f1 s)) // and occur during a stable regimen
          (or (in f2 s) (equals f2 s))
       )
      )
      ( r1 = r2 ) // then they must obtain the same responsible node
    )
  )
)

// TODO: adicionar definição de macros / predicados
