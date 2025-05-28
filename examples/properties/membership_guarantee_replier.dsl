// TODO: add generic functional operation type and merge conjuction

( and

/* Membership Guarantee (Replier, findnode) */
  ( forall findnode find (- -) (replier -)

    ( or
      (exists join join (join_node) () // nodes joins at the same time as the operation 
                                       // and replies during the join (before becoming a member)
        ( join_node = replier )
        ( intersects join find )
      )

                                             // or
     ( exists member member (member_node) () // the node is a full member during one instant of the operation
        ( member_node = replier ) 
        ( intersects member find )
     )
    )
  )

/* Membership Guarantee (Replier, lookup) */
  ( forall lookup lookup (- -) (replier -)

    ( or
      (exists join join (join_node) () // nodes joins at the same time as the operation 
                                       // and replies during the join (before becoming a member)
        ( join_node = replier )
        ( intersects join lookup )
      )

                                             // or
     ( exists member member (member_node) () // the node is a full member during one instant of the operation
        ( member_node = replier ) 
        ( intersects member lookup )
     )
    )
  )

/* Membership Guarantee (Replier, store) */
  ( forall store store (- - -) (replier)

    ( or
      (exists join join (join_node) () // nodes joins at the same time as the operation 
                                       // and replies during the join (before becoming a member)
        ( join_node = replier )
        ( intersects join store )
      )

                                             // or
     ( exists member member (member_node) () // the node is a full member during one instant of the operation
        ( member_node = replier ) 
        ( intersects member store )
     )
    )
  )
)
