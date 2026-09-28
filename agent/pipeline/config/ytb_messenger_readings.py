"""Attestation-scoped rejection of an endingless singular participle.

Tania Notarius, KTU 1.5 review (August–September 2026), rejects the
participle in I:9 and II:13 on agreement and negation grounds. Tropper
(2012), p. 634, lists yṯb as prefix-conjugation 3 m. du. at these two
references and the parallel 1.2 I:19; EUPT instead tags suffix conjugation
3 m. du. Both finite readings must survive. This is not a ban on yṯb
participles elsewhere or on participles following every occurrence of l.
"""

from pipeline.config.l_negation_exception_refs import normalize_ktu_ref


MESSENGER_YTB_REFS = frozenset({"KTU 1.2 I:19", "KTU 1.5 I:9", "KTU 1.5 II:13"})
YTB_PARTICIPLE_WARNING = (
    "Singular yṯb participle conflicts with the messenger clause here; "
    "compare Tania Notarius on KTU 1.5 I:9 / II:13 and Tropper (2012), p. 634"
)


def rejected_messenger_participle(ref: str, surface: str, analysis: str, pos: str) -> bool:
    ref = normalize_ktu_ref(ref).replace("CAT ", "KTU ", 1)
    return (
        ref in MESSENGER_YTB_REFS
        and surface.strip() == "yṯb"
        and analysis.strip() == "yṯb[/"
        and "act. ptcpl." in pos
        and "sg." in pos
    )
