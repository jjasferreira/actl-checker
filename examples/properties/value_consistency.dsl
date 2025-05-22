(forall lookup l1 (n1 k1) (n3 v1)
  (forall lookup l2 (n2 k2) (n4 v2)
    (implies (not (equals l1 l2)) // if the lookups are not the same operation then
      
      (forall readonly r2 () ()
        (forall ideal i2 () ()
          (implies		  // if
	    (and (k1 = k2)	  // the lookups are for the same key 
	      (or (in l1 readonly) (equals l1 readonly)) // and happen during a readonly regimen 
	      (or (in l2 readonly) (equals l2 readonly))
	      (or (in l1 ideal) (equals l1 ideal))	 // and happen during an ideal state
	      (or (in l2 ideal) (equals l2 ideal))
	    )
	    (v1 = v2)		  // then the lookups obtain the same value
	  )
	)
      )
    )
  )
)
