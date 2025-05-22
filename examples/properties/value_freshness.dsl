/* Value Freshness */
(forall lookup l1 (n1 k1) (n2 v1)
  (implies 
    (and 
      (not (v1 = 'no_value)) // if the lookup returns a value
      (exists ideal i() () // and is during an ideal state
	(or (in l1 i) (equals l1 i))
      )
    )

    // then there exists an operation such that
    (exists store s1 (n3 k2 v2) (n4 )
      (and
	(v1 = v2)      // the lookup value matches the store value
	(k1 = k2)      // the lookup key matches the store key

	// and either
	(or 
	  (intersects s1 l1) // the store is concurrent with lookup
	  (and
	    (before s1 l1) // or the store precedes the lookup 
	    
	    // and it is the most recent store
	    (forall store s2 (n5 k3 v3) (n6)
	      (implies
		(and 
		  (not (equals s1 s2)) 
		  (k2 = k3)       
		  (before s2 l1) // if another store was executed before the lookup
		)
		(not (before s1 s2)) // then it was also before store s1 
	      )
	    )
	  )
	)
      )
    )
  )
)
