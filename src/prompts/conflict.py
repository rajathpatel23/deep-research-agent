V1 = {
    "version": "v1",
    "description": "Two claims → relationship classification",
    "system": """\
You compare two research claims and classify their relationship.
Return exactly one word: SUPPORT, CONTRADICT, COMPATIBLE, or UNRELATED.

SUPPORT: Claim B directly confirms or reinforces Claim A.
CONTRADICT: Claim B directly negates or is inconsistent with Claim A.
COMPATIBLE: Claims can both be true but address different angles.
UNRELATED: Claims are about different things.""",
}

CURRENT = V1
