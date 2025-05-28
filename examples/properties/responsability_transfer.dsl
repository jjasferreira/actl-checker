/* Responsability Transfer */
( forall leave leave (left_node) ()
  ( forall findnode find (- -) (- responsible) 
    (implies
      (and 
       ( left_node = responsible ) // if the node that left is the result of a findnode operation
       ( before leave find ) // and the node left before findnode operation started
      )
     ( exists join join (joined_node) () // then the node must have rejoined
        ( left_node = joined_node ) 
        ( before leave join  ) // after leaving
        ( before join find  ) // and before the findnode operation started 
     )
    )
  )
)
