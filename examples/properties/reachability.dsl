/* Reachability */
( forall findnode find ( - key) (- responsible)
  ( implies
    ( exists ideal ideal () ()
      ( or 
        ( in ideal find )     // findnode during ideal state
        ( equals ideal find )
      )

      ( exists member member (member_node) () 
        ( member_node = key )
        ( or 
          ( in ideal member )   // and key is the identifier of a member 
          ( equals ideal member )
        )
      )
    )
    ( key = responsible ) // then the member must be responsible for its own identifier 
  )
)
