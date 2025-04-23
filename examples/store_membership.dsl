(forall store i1 (n1 k1 v1) (n2)
    (exists member i2 (n3) ()
        (and
            (equal n1 n3)
            (or
                (or
                    (equals i1 i2)
                    (during i1 i2)
                )
                (or
                    (or
                        (starts i1 i2)
                        (finishes i1 i2)
                    )
                    (or
                        (overlaps i2 i1)
                        (starts i2 i1)
                    )
                )
            )
        )
    )
)