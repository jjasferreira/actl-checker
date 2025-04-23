(forall store i1 (n1 k1 v1) (n2)
    (forall store i2 (n3 k2 v2) (n4)
        (implies
            (and
                (equal n1 n3)
                (and
                    (equal k1 k2)
                    (equal v1 v2)
                )
            )
            (or
                (or
                    (before i1 i2)
                    (meets i1 i2)
                )
                (or
                    (before i2 i1)
                    (meets i2 i1)
                )
            )
        )   
    )
)