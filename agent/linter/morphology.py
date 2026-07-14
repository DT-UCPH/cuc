import enum


stems = {
    "G": "basic (ground) verbal stem; corresponds to BH Qal",
    "Gt": "verbal G stem with -t infixed; generally reflexive; appears in Moabite, Phoenician, and Aramaic",
    "Gpass.": "G passive; appears in Arabic and the Amarna letters from Canaan",
    "N": "verbal stem with n-prefix; reflexive-passive; corresponds to BH Niphʿal and Akkadian Niprusu",
    "D": "triconsonantal verbal stem with long (geminated) second radical; factitive, causative, intensive; corresponds to BH Piʿʿēl",
    "Dpass.": "D passive",
    "tD": "verbal D stem with t-prefix; corresponds to BH Hithpaʿʿēl",
    "Dt": "verbal stem D with infixed -t-",
    "L": "biconsonantal verbal stem with lengthened second radical; corresponds to the D stem, but only used with hollow roots; evidently characterized by a long vowel after the first radical and the reduplication of the second radical; corresponds to BH Pôlēl",
    "Lt": "verbal L stem with infix -t-",
    "tL": "verbal L stem with t-prefix",
    "Lpass.": "L passive",
    "R": "reduplicated verbal biconsonantal stem; corresponds to the D stem, but only used with hollow roots; characterized by the reduplication of both radicals resulting in a quadraliteral stem",
    "Š": "verbal stem with š-prefix; causative; corresponds to Akkadian Š-stem and functions as BH Hiphʿîl",
    "Špass.": "Š passive",
    "Št": "verbal stem with š-prefix and infixed -t-; rarely documented",
}


class VerbalStem(enum.Enum):
    G = "G"
    Gt = "Gt"
    Gpass = "Gpass."
    N = "N"
    D = "D"
    Dpass = "Dpass."
    tD = "tD"
    Dt = "Dt"
    L = "L"
    Lt = "Lt"
    tL = "tL"
    Lpass = "Lpass."
    R = "R"
    Š = "Š"
    Špass = "Špass."
    Št = "Št"

    def description(self) -> str:
        return stems[self.value]


cases = {
    "nom.": "nominative",
    "gen.": "genetive",
    "acc.": "accusative",
    "gen., acc.": "oblique",
}


class Case(enum.Enum):
    N = "nom."
    G = "gen."
    A = "acc."
    GA = "gen., acc."

    def description(self) -> str:
        return cases[self.value]


persons = {"1": "1st person", "2": "2nd person", "3": "3rd person"}


class Person(enum.Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"

    def description(self) -> str:
        return persons[self.value]


genders = {"m.": "masculine", "f.": "feminine", "c. n.": "common"}


class Gender(enum.Enum):
    MASCULINE = "m."
    FEMININE = "f."
    COMMON = "c. n."

    def description(self) -> str:
        return genders[self.value]


numbers = {"s": "singular", "d": "dual", "p": "plural"}


class Number(enum.Enum):
    SINGULAR = "s"
    DUAL = "d"
    PLURAL = "p"

    def description(self) -> str:
        return numbers[self.value]


states = {
    "emph.": "emphatic",  # 'non-construct',
    "cstr.": "construct state,",
    "suff.": "suffix construct",
}


class State(enum.Enum):
    EMPHATIC = "emph."
    CONSTRUCT = "cstr."
    SUFFIX_CONSTRUCT = "suff."

    def description(self) -> str:
        return states[self.value]


pronominal_types = {
    "p.": "personal pronoun",
    "dem.": "demonstrative pronoun",
    "interr.": "interrogative pronoun",
    "rel.": "relative pronoun",
    "indef.": "indefinite pronoun",
}


class PronominalType(enum.Enum):
    PERSONAL = "p."
    DEMONSTRATIVE = "dem."
    INTERROGATIVE = "interr."
    RELATIVE = "rel."
    INDEFINITE = "indef."

    def description(self) -> str:
        return pronominal_types[self.value]


adjective_degrees = {
    "P": "positive",
    "R": "comparative",
    "S": "superlative",
}


class AdjectiveDegree(enum.Enum):
    POSITIVE = "P"
    COMPARATIVE = "R"
    SUPERLATIVE = "S"

    def description(self) -> str:
        return adjective_degrees[self.value]


verb_tenses = {
    "suffc.": "suffix conjugation",
    "pref.": "prefix conjugation",
    "inf.": "infinitive",
    "impv.": "imperative",
    "ptcpl.": "participle",
}


class Tense(enum.Enum):
    SUFFICIENT = "suffc."
    PREFIX = "pref."
    INFINITIVE = "inf."
    IMPERATIVE = "impv."
    PARTICIPLE = "ptcpl."

    def description(self) -> str:
        return verb_tenses[self.value]


pref_conj_moods = {
    "indic.": "indicative",
    "juss.-pret.": "jussive-preterite",
    "vol.": "volitive",
}


class Mood(enum.Enum):
    INDICATIVE = "indic."
    JUSSIVE_PRETERITE = "juss.-pret."
    VOLITIVE = "vol."

    def description(self) -> str:
        return pref_conj_moods[self.value]


participle_voices = {
    "act. ptcpl.": "active participle",
    "pass. ptcpl.": "passive participle",
}


class Voice(enum.Enum):
    ACTIVE_PARTICIPLE = "act. ptcpl."
    PASSIVE_PARTICIPLE = "pass. ptcpl."

    def description(self) -> str:
        return participle_voices[self.value]


stem = {
    "u": "qatal",
    "i": "qatil",
    "a": "qatul",
}


class Stem(enum.Enum):
    QATUL = "u"  # qatul
    QATIL = "i"  # qatil
    QATAL = "a"  # qatal

    def description(self) -> str:
        return stem[self.value]


morphology = {
    "pos": {
        "pn": {
            "name": "Pronoun",
            "type": pronominal_types,
            "case": cases,
            "person": persons,
            "gender": genders,
            "number": numbers,
        },
        "PSS": {
            "name": "Pronominal suffix",
            "case": cases,
            "person": persons,
            "gender": genders,
            "number": numbers,
        },
        "NN": {
            "name": "Noun",
            "case": cases,
            "gender": genders,
            "number": numbers,
            "state": states,
        },
        "adj.": {
            "name": "Adjective",
            "case": cases,
            "gender": genders,
            "number": numbers,
            "state": states,
            "degree": adjective_degrees,
        },
        "adv.": {},
        "vb. n.": {
            "name": "Verbal noun/Infinitive",
            "case": cases,
            "gender": genders,
            "stem": stems,
            "state": states,
            "number": numbers,
        },
        "vb.": {
            "name": "Verb",
            "mood": pref_conj_moods,
            "tense": verb_tenses,
            "voice": participle_voices,
            "person": persons,
            "gender": genders,
            "number": numbers,
            "stem": stems,
        },
    }
}


class POS(enum.Enum):
    PRONOUN = "pn"
    PRONOMINAL_SUFFIX = "PSS"
    NOUN = "NN"
    PROPER_NOUN = "PN"
    ADJECTIVE = "adj."
    ADVERB = "adv."
    VERBAL_NOUN = "vb. n."
    VERB = "vb."


class MorphType:
    pos: POS


class VerbalMorphType(MorphType):
    person: Person
    gender: Gender
    number: Number
    mood: Mood
    tense: Tense
    voice: Voice
    stem: VerbalStem


class NominalMorphType(MorphType):
    nominal_case: Case
    gender: Gender
    number: Number
    state: State


# G stem

# paradigm_G_suffc_qatal_strong = '''
# translit	transcript	gloss	pos	stem	conjugation	form
# ktb	/kataba/	‘he wrote’	vb.	G	suffc.	3ms
# ktbt	/katabat/	‘she wrote’	vb.	G	suffc.	3fs
# ktbt	/katabtā̆/	‘you wrote’	vb.	G	suffc.	2ms
# ktbt	/katabtī̆/	‘you wrote’	vb.	G	suffc.	2fs
# ktbt	/katabtū̆/(?)	‘I wrote’	vb.	G	suffc.	1cs
# ktb	/katabā/	‘they two wrote’	vb.	G	suffc.	3md
# ktbt	/katabtā/	‘they two wrote’	vb.	G	suffc.	3fd
# ktbtm	/katabtumā/	‘you two wrote’	vb.	G	suffc.	2cd
# ktbny	/katabnV̄yā/(?)	‘we two wrote’	vb.	G	suffc.	1cd
# ktb	/katabū/	‘they wrote’	vb.	G	suffc.	3mp
# ktb	/katabā/(?)	‘they wrote’	vb.	G	suffc.	3fp
# ktbtm	/katabtum(ū)/(?)	‘you wrote’	vb.	G	suffc.	2mp
# ktbtn	/katabtin(ā/nā̆)/(?)	‘you wrote’	vb.	G	suffc.	2fp
# ktbn	/katabnV̄̆/	‘we wrote’	vb.	G	suffc.	1cp
# '''

paradigm_G_suffc_qatal_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qatala/	‘he killed’	vb.	G	suffc.	3ms
qtlt	/qatalat/	‘she killed’	vb.	G	suffc.	3fs
qtlt	/qataltā̆/	‘you killed’	vb.	G	suffc.	2ms
qtlt	/qataltī̆/	‘you killed’	vb.	G	suffc.	2fs
qtlt	/qataltū̆/(?)	‘I killed’	vb.	G	suffc.	1cs
qtl	/qatalā/	‘they two killed’	vb.	G	suffc.	3md
qtlt	/qataltā/	‘they two killed’	vb.	G	suffc.	3fd
qtltm	/qataltumā/	‘you two killed’	vb.	G	suffc.	2cd
qtlny	/qatalnV̄yā/(?)	‘we two killed’	vb.	G	suffc.	1cd
qtl	/qatalū/	‘they killed’	vb.	G	suffc.	3mp
qtl	/qatalā/(?)	‘they killed’	vb.	G	suffc.	3fp
qtltm	/qataltum(ū)/(?)	‘you killed’	vb.	G	suffc.	2mp
qtltn	/qataltin(ā/nā̆)/(?)	‘you killed’	vb.	G	suffc.	2fp
qtln	/qatalnV̄̆/	‘we killed’	vb.	G	suffc.	1cp
"""


# V stands for a variable vowel
pattern_G_suffc_qatal_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1a2a3a/	‘he Xed’	vb.	G	suffc.	3ms
123t	/1a2a3at/	‘she Xed’	vb.	G	suffc.	3fs
123t	/1a2a3atā̆/	‘you Xed’	vb.	G	suffc.	2ms
123t	/1a2a3atī̆/	‘you Xed’	vb.	G	suffc.	2fs
123t	/1a2a3atū̆/(?)	‘I Xed’	vb.	G	suffc.	1cs
123	/1a2a3ā/	‘they two Xed’	vb.	G	suffc.	3md
123t	/1a2a3atā/	‘they two Xed’	vb.	G	suffc.	3fd
123tm	/1a2a3tumā/	‘you two Xed’	vb.	G	suffc.	2cd
123ny	/1a2a3nV̄yā/(?)	‘we two Xed’	vb.	G	suffc.	1cd
123	/1a2a3ū/	‘they Xed’	vb.	G	suffc.	3mp
123	/1a2a3ā/(?)	‘they Xed’	vb.	G	suffc.	3fp
123tm	/1a2a3tum(ū)/(?)	‘you Xed’	vb.	G	suffc.	2mp
123tn	/1a2a3tin(ā/nā̆)/(?)	‘you Xed’	vb.	G	suffc.	2fp
123n	/1a2a3nV̄̆/	‘we Xed’	vb.	G	suffc.	1cp
"""

paradigm_G_suffc_qatil_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
šỉl	/šaˀila/	‘he asked’	vb.	G	suffc.	3ms
šỉlt	/šaˀilat/	‘she asked’	vb.	G	suffc.	3fs
šỉlt	/šaˀiltā̆/	‘you asked’	vb.	G	suffc.	2ms
šỉlt	/šaˀiltī̆/	‘you asked’	vb.	G	suffc.	2fs
šỉlt	/šaˀiltū̆/(?)	‘I asked’	vb.	G	suffc.	1cs
šỉl	/šaˀilā/	‘they two asked’	vb.	G	suffc.	3md
šỉlt	/šaˀiltā/	‘they two asked’	vb.	G	suffc.	3fd
šỉltm	/šaˀiltumā/(?)	‘you two asked’	vb.	G	suffc.	2cd
šỉlny	/šaˀilnV̄yā/(?)	‘we two asked’	vb.	G	suffc.	1cd
šỉl	/šaˀilū/	‘they asked’	vb.	G	suffc.	3mp
šỉl	/šaˀilā/(?)	‘they asked’	vb.	G	suffc.	3fp
šỉltm	/šaˀiltum(ū)/(?)	‘you asked’	vb.	G	suffc.	2mp
šỉltn	/šaˀiltin(ā/nā̆)/(?)	‘you asked’	vb.	G	suffc.	2fp
šỉln	/šaˀilnV̄̆/	‘we asked’	vb.	G	suffc.	1cp
"""

pattern_G_suffc_qatil_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1a2i3a/	‘he Xed’	vb.	G	suffc.	3ms
123t	/1a2i3at/	‘she Xed’	vb.	G	suffc.	3fs
123t	/1a2i3tā̆/	‘you Xed’	vb.	G	suffc.	2ms
123t	/1a2i3tī̆/	‘you Xed’	vb.	G	suffc.	2fs
123t	/1a2i3tū̆/(?)	‘I Xed’	vb.	G	suffc.	1cs
123	/1a2i3ā/	‘they two Xed’	vb.	G	suffc.	3md
123t	/1a2i3tā/	‘they two Xed’	vb.	G	suffc.	3fd
123tm	/1a2i3tumā/(?)	‘you two Xed’	vb.	G	suffc.	2cd
123ny	/1a2i3nV̄yā/(?)	‘we two Xed’	vb.	G	suffc.	1cd
123	/1a2i3ū/	‘they Xed’	vb.	G	suffc.	3mp
123	/1a2i3ā/(?)	‘they Xed’	vb.	G	suffc.	3fp
123tm	/1a2i3tum(ū)/(?)	‘you Xed’	vb.	G	suffc.	2mp
123tn	/1a2i3tin(ā/nā̆)/(?)	‘you Xed’	vb.	G	suffc.	2fp
123n	/1a2i3nV̄̆/	‘we Xed’	vb.	G	suffc.	1cp
"""

paradigm_G_suffc_qatul_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
mrṣ	/maruṣa/	‘he fell ill’	vb.	G	suffc.	3ms
mrṣt	/maruṣat/	‘she fell ill’	vb.	G	suffc.	3fs
mrṣt	/maruṣtā̆/	‘you fell ill’	vb.	G	suffc.	2ms
mrṣt	/maruṣtī̆/	‘you fell ill’	vb.	G	suffc.	2fs
mrṣt	/maruṣtū̆/(?)	‘I fell ill’	vb.	G	suffc.	1cs
mrṣ	/maruṣā/	‘they two fell ill’	vb.	G	suffc.	3md
mrṣt	/maruṣtā/	‘they two fell ill’	vb.	G	suffc.	3fd
mrṣtm	/maruṣtumā/(?)	‘you two fell ill’	vb.	G	suffc.	2cd
mrṣny	/maruṣnV̄yā/(?)	‘we two fell ill’	vb.	G	suffc.	1cd
mrṣ	/maruṣū/	‘they fell ill’	vb.	G	suffc.	3mp
mrṣ	/maruṣā/(?)	‘they fell ill’	vb.	G	suffc.	3fp
mrṣtm	/maruṣtum(ū)/(?)	‘you fell ill’	vb.	G	suffc.	2mp
mrṣtn	/maruṣtin(ā/nā̆)/(?)	‘you fell ill’	vb.	G	suffc.	2fp
mṛsn	/maruṣnV̄̆/	‘we fell ill’	vb.	G	suffc.	1cp
"""

pattern_G_suffc_qatul_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1a2u3a/	‘he Xed’	vb.	G	suffc.	3ms
123t	/1a2u3at/	‘she Xed’	vb.	G	suffc.	3fs
123t	/1a2u3tā̆/	‘you Xed’	vb.	G	suffc.	2ms
123t	/1a2u3tī̆/	‘you Xed’	vb.	G	suffc.	2fs
123t	/1a2u3tū̆/(?)	‘I Xed’	vb.	G	suffc.	1cs
123	/1a2u3ā/	‘they two Xed’	vb.	G	suffc.	3md
123t	/1a2u3tā/	‘they two Xed’	vb.	G	suffc.	3fd
123tm	/1a2u3tumā/(?)	‘you two Xed’	vb.	G	suffc.	2cd
123ny	/1a2u3nV̄yā/(?)	‘we two Xed’	vb.	G	suffc.	1cd
123	/1a2u3ū/	‘they Xed’	vb.	G	suffc.	3mp
123	/1a2u3ā/(?)	‘they Xed’	vb.	G	suffc.	3fp
123tm	/1a2u3tum(ū)/(?)	‘you Xed’	vb.	G	suffc.	2mp
123tn	/1a2u3tin(ā/nā̆)/(?)	‘you Xed’	vb.	G	suffc.	2fp
123n	/1a2u3nV̄̆/	‘we Xed’	vb.	G	suffc.	1cp
"""

paradigm_G_pref_qatul_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtulu/	‘he kills’	vb.	G	pref.	3ms
tqtl	/taqtulu/	‘she kills’	vb.	G	pref.	3fs
tqtl	/taqtulu/	‘you kill’	vb.	G	pref.	2ms
tqtln	/taqtulīna/	‘you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtulu/	‘I kill’	vb.	G	pref.	1cs
y/tqtln	/y/taqtulāna/	‘they two kill’	vb.	G	pref.	3md
tqtln	/taqtulāna/	‘they two kill’	vb.	G	pref.	3fd
tqtln	/taqtulāna/	‘you two kill’	vb.	G	pref.	2cd
?	/?/	‘we two kill’	vb.	G	pref.	1cd
tqtln	/taqtulūna/	‘they kill’	vb.	G	pref.	3mp
tqtln	/taqtulna/(?)	‘they kill’	vb.	G	pref.	3fp
tqtln	/taqtulūna/	‘you kill’	vb.	G	pref.	2mp
tqtln	/taqtulna/(?)	‘you kill’	vb.	G	pref.	2fp
nqtl	/naqtulu/	‘we kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatul_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12u3u/	‘he Xs’	vb.	G	pref.	3ms
t123	/ta12u3u/	‘she Xs’	vb.	G	pref.	3fs
t123	/ta12u3u/	‘you X’	vb.	G	pref.	2ms
t123n	/ta12u3īna/	‘you X’	vb.	G	pref.	2fs
ả123	/ˀa12u3u/	‘I X’	vb.	G	pref.	1cs
y/t123n	/y/ta12u3āna/	‘they two X’	vb.	G	pref.	3md
t123n	/ta12u3āna/	‘they two X’	vb.	G	pref.	3fd
t123n	/ta12u3āna/	‘you two X’	vb.	G	pref.	2cd
?	/?/	‘we two X’	vb.	G	pref.	1cd
t123n	/ta12u3ūna/	‘they X’	vb.	G	pref.	3mp
t123n	/ta12u3na/(?)	‘they X’	vb.	G	pref.	3fp
t123n	/ta12u3ūna/	‘you X’	vb.	G	pref.	2mp
t123n	/ta12u3na/(?)	‘you X’	vb.	G	pref.	2fp
n123	/na12u3u/	‘we X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatul_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtul/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtul/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtul/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtulī/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtul/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtulā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtulā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtulā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtulā/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtulū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtulna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtulū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtulna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtul/	‘let us kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatul_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12u3/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12u3/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12u3/	‘let you X’	vb.	G	pref.	2ms
t123	/ta12u3ī/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12u3/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12u3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12u3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12u3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12u3ā/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12u3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12u3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12u3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12u3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12u3/	‘let us X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatul_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtula/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtula/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtula/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtulī/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtula/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtulā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtulā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtulā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtulā/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtulū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtulna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtulū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtulna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtula/	‘let us kill’	vb.	G	pref.	1cp
"""


pattern_G_pref_qatul_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12u3a/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12u3a/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12u3a/	‘let you X’	vb.	G	pref.	2ms
t123	/ta12u3ī/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12u3a/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12u3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12u3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12u3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12u3ā/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12u3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12u3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12u3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12u3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12u3a/	‘let us X’	vb.	G	pref.	1cp
"""

### qatil

paradigm_G_pref_qatil_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtilu/	‘he kills’	vb.	G	pref.	3ms
tqtl	/taqtilu/	‘she kills’	vb.	G	pref.	3fs
tqtl	/taqtilu/	‘you kill’	vb.	G	pref.	2ms
tqtln	/taqtilīna/	‘you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtilu/	‘I kill’	vb.	G	pref.	1cs
y/tqtln	/y/taqtilāna/	‘they two kill’	vb.	G	pref.	3md
tqtln	/taqtilāna/	‘they two kill’	vb.	G	pref.	3fd
tqtln	/taqtilāna/	‘you two kill’	vb.	G	pref.	2cd
?	/?/	‘we two kill’	vb.	G	pref.	1cd
tqtln	/taqtilūna/	‘they kill’	vb.	G	pref.	3mp
tqtln	/taqtilna/(?)	‘they kill’	vb.	G	pref.	3fp
tqtln	/taqtilūna/	‘you kill’	vb.	G	pref.	2mp
tqtln	/taqtilna/(?)	‘you kill’	vb.	G	pref.	2fp
nqtl	/naqtilu/	‘we kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatil_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12i3u/	‘he Xs’	vb.	G	pref.	3ms
t123	/ta12i3u/	‘she Xs’	vb.	G	pref.	3fs
t123	/ta12i3u/	‘you X’	vb.	G	pref.	2ms
t123n	/ta12i3īna/	‘you X’	vb.	G	pref.	2fs
ả123	/ˀa12i3u/	‘I X’	vb.	G	pref.	1cs
y/t123n	/y/ta12i3āna/	‘they two X’	vb.	G	pref.	3md
t123n	/ta12i3āna/	‘they two X’	vb.	G	pref.	3fd
t123n	/ta12i3āna/	‘you two X’	vb.	G	pref.	2cd
?	/?/	‘we two X’	vb.	G	pref.	1cd
t123n	/ta12i3ūna/	‘they X’	vb.	G	pref.	3mp
t123n	/ta12i3na/(?)	‘they X’	vb.	G	pref.	3fp
t123n	/ta12i3ūna/	‘you X’	vb.	G	pref.	2mp
t123n	/ta12i3na/(?)	‘you X’	vb.	G	pref.	2fp
n123	/na12i3u/	‘we X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatil_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtil/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtil/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtil/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtilī/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtil/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtilā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtilā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtilā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtilā/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtilū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtilna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtilū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtilna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtil/	‘let us kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatil_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12i3/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12i3/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12i3/	‘let you X’	vb.	G	pref.	2ms
t123	/ta12i3ī/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12i3/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12i3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12i3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12i3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12i3ā/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12i3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12i3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12i3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12i3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12i3/	‘let us X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatil_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtila/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtila/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtila/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtīla/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtila/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtilā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtilā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtilā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtilā/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtilū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtilna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtilū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtilna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtila/	‘let us kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatil_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12i3a/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12i3a/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12i3a/	‘let you X’	vb.	G	pref.	2ms
t123	/taqtīla/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12i3a/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12i3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12i3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12i3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12i3ā/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12i3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12i3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12i3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12i3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12i3a/	‘let us X’	vb.	G	pref.	1cp
"""

# qatal

paradigm_G_pref_qatal_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtalu/	‘he kills’	vb.	G	pref.	3ms
tqtl	/taqtalu/	‘she kills’	vb.	G	pref.	3fs
tqtl	/taqtalu/	‘you kill’	vb.	G	pref.	2ms
tqtln	/taqtalīna/	‘you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtalu/	‘I kill’	vb.	G	pref.	1cs
y/tqtln	/y/taqtalāna/	‘they two kill’	vb.	G	pref.	3md
tqtln	/taqtalāna/	‘they two kill’	vb.	G	pref.	3fd
tqtln	/taqtalāna/	‘you two kill’	vb.	G	pref.	2cd
?	/?/	‘we two kill’	vb.	G	pref.	1cd
tqtln	/taqtalūna/	‘they kill’	vb.	G	pref.	3mp
tqtln	/taqtalna/(?)	‘they kill’	vb.	G	pref.	3fp
tqtln	/taqtalūna/	‘you kill’	vb.	G	pref.	2mp
tqtln	/taqtalna/(?)	‘you kill’	vb.	G	pref.	2fp
nqtl	/naqtalu/	‘we kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatal_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12a3u/	‘he Xs’	vb.	G	pref.	3ms
t123	/ta12a3u/	‘she Xs’	vb.	G	pref.	3fs
t123	/ta12a3u/	‘you X’	vb.	G	pref.	2ms
t123n	/ta12a3īna/	‘you X’	vb.	G	pref.	2fs
ả123	/ˀa12a3u/	‘I X’	vb.	G	pref.	1cs
y/t123n	/y/ta12a3āna/	‘they two X’	vb.	G	pref.	3md
t123n	/ta12a3āna/	‘they two X’	vb.	G	pref.	3fd
t123n	/ta12a3āna/	‘you two X’	vb.	G	pref.	2cd
?	/?/	‘we two X’	vb.	G	pref.	1cd
t123n	/ta12a3ūna/	‘they X’	vb.	G	pref.	3mp
t123n	/ta12a3na/(?)	‘they X’	vb.	G	pref.	3fp
t123n	/ta12a3ūna/	‘you X’	vb.	G	pref.	2mp
t123n	/ta12a3na/(?)	‘you X’	vb.	G	pref.	2fp
n123	/na12a3u/	‘we X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatal_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtal/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtal/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtal/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtalī/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtal/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtalā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtalā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtalā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtalā/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtalū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtalna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtalū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtalna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtala/	‘let us kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatal_strong_jussive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12a3/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12a3/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12a3/	‘let you X’	vb.	G	pref.	2ms
t123	/ta12a3ī/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12a3/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12a3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12a3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12a3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12a3ā/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12a3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12a3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12a3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12a3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12a3a/	‘let us X’	vb.	G	pref.	1cp
"""

paradigm_G_pref_qatal_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yaqtala/	‘let him kill’	vb.	G	pref.	3ms
tqtl	/taqtala/	‘let her kill’	vb.	G	pref.	3fs
tqtl	/taqtala/	‘let you kill’	vb.	G	pref.	2ms
tqtl	/taqtalī/	‘let you kill’	vb.	G	pref.	2fs
ảqtl	/ˀaqtala/	‘let me kill’	vb.	G	pref.	1cs
y/tqtl	/y/taqtalā/	‘let them two kill’	vb.	G	pref.	3md
tqtl	/taqtalā/	‘let them two kill’	vb.	G	pref.	3fd
tqtl	/taqtalā/	‘let you two kill’	vb.	G	pref.	2cd
nqtl	/naqtala/(?)	‘let we two kill’	vb.	G	pref.	1cd
tqtl	/taqtalū/	‘let them kill’	vb.	G	pref.	3mp
tqtln	/taqtalna/(?)	‘let them kill’	vb.	G	pref.	3fp
tqtl	/taqtalū/	‘let you kill’	vb.	G	pref.	2mp
tqtln	/taqtalna/(?)	‘let you kill’	vb.	G	pref.	2fp
nqtl	/naqtala/	‘let us kill’	vb.	G	pref.	1cp
"""

pattern_G_pref_qatal_strong_volitive = """
translit	transcript	gloss	pos	stem	conjugation	form
y123	/ya12a3a/	‘let him X’	vb.	G	pref.	3ms
t123	/ta12a3a/	‘let her X’	vb.	G	pref.	3fs
t123	/ta12a3a/	‘let you X’	vb.	G	pref.	2ms
t123	/ta12a3ī/	‘let you X’	vb.	G	pref.	2fs
ả123	/ˀa12a3a/	‘let me X’	vb.	G	pref.	1cs
y/t123	/y/ta12a3ā/	‘let them two X’	vb.	G	pref.	3md
t123	/ta12a3ā/	‘let them two X’	vb.	G	pref.	3fd
t123	/ta12a3ā/	‘let you two X’	vb.	G	pref.	2cd
n123	/na12a3a/(?)	‘let we two X’	vb.	G	pref.	1cd
t123	/ta12a3ū/	‘let them X’	vb.	G	pref.	3mp
t123n	/ta12a3na/(?)	‘let them X’	vb.	G	pref.	3fp
t123	/ta12a3ū/	‘let you X’	vb.	G	pref.	2mp
t123n	/ta12a3na/(?)	‘let you X’	vb.	G	pref.	2fp
n123	/na12a3a/	‘let us X’	vb.	G	pref.	1cp
"""

# G Imperative

paradigm_G_impv_qatul_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qutul/, /qut(u)la/	‘kill!’	vb.	G	impv.	2ms
qtl	/qut(u)lī/	‘kill!’	vb.	G	impv.	2fs
qtl	/qut(u)lā/	‘kill!’	vb.	G	impv.	2cd
qtl	/qut(u)lū/	‘kill!’	vb.	G	impv.	2mp
?	/?/	‘kill!’	vb.	G	impv.	2fp
"""

paradigm_G_impv_qatil_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qitil/, /qit(i)la/	‘kill!’	vb.	G	impv.	2ms
qtl	/qit(i)lī/	‘kill!’	vb.	G	impv.	2fs
qtl	/qit(i)lā/	‘kill!’	vb.	G	impv.	2cd
qtl	/qit(i)lū/	‘kill!’	vb.	G	impv.	2mp
?	/?/	‘kill!’	vb.	G	impv.	2fp
"""

paradigm_G_impv_qatal_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qatal/, /qat(a)la/	‘kill!’	vb.	G	impv.	2ms
qtl	/qat(a)lī/	‘kill!’	vb.	G	impv.	2fs
qtl	/qat(a)lā/	‘kill!’	vb.	G	impv.	2cd
qtl	/qat(a)lū/	‘kill!’	vb.	G	impv.	2mp
?	/?/	‘kill!’	vb.	G	impv.	2fp
"""

pattern_G_impv_qatul_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1u2u3/, /1u2(u)3a/	‘X!’	vb.	G	impv.	2ms
123	/1u2(u)3ī/	‘X!’	vb.	G	impv.	2fs
123	/1u2(u)3ā/	‘X!’	vb.	G	impv.	2cd
123	/1u2(u)3ū/	‘X!’	vb.	G	impv.	2mp
?	/?/	‘X!’	vb.	G	impv.	2fp
"""

pattern_G_impv_qatil_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1i2i3/, /1i2(i)3a/	‘X!’	vb.	G	impv.	2ms
123	/1i2(i)3ī/	‘X!’	vb.	G	impv.	2fs
123	/1i2(i)3ā/	‘X!’	vb.	G	impv.	2cd
123	/1i2(i)3ū/	‘X!’	vb.	G	impv.	2mp
?	/?/	‘X!’	vb.	G	impv.	2fp
"""

pattern_G_impv_qatal_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1a2a3/, /1a2(a)3a/	‘X!’	vb.	G	impv.	2ms
123	/1a2(a)3ī/	‘X!’	vb.	G	impv.	2fs
123	/1a2(a)3ā/	‘X!’	vb.	G	impv.	2cd
123	/1a2(a)3ū/	‘X!’	vb.	G	impv.	2mp
?	/?/	‘X!’	vb.	G	impv.	2fp
"""

# G Participle

paradigm_G_act_ptcpl_strong = """
translit	transcript	gloss	pos	stem	conjugation	form	state	case
qtl	/qātilu/	‘killing’	vb.	G	act. ptcpl	ms	abs	nom.
qtl	/qātili/	‘killing’	vb.	G	act. ptcpl	ms	abs	gen.
qtl	/qātila/	‘killing’	vb.	G	act. ptcpl	ms	abs	acc.
qtl	/qātilu/	‘killing of’	vb.	G	act. ptcpl	ms	cstr	nom.
qtl	/qātili/	‘killing of’	vb.	G	act. ptcpl	ms	cstr	gen.
qtl	/qātila/	‘killing of’	vb.	G	act. ptcpl	ms	cstr	acc.
qtlt	/qātil(a)tu/	‘killing’	vb.	G	act. ptcpl	fs	abs	nom.
qtlt	/qātil(a)ti/	‘killing’	vb.	G	act. ptcpl	fs	abs	gen.
qtlt	/qātil(a)ta/	‘killing’	vb.	G	act. ptcpl	fs	abs	acc.
qtlt	/qātil(a)tu/	‘killing of’	vb.	G	act. ptcpl	fs	cstr	nom.
qtlt	/qātil(a)ti/	‘killing of’	vb.	G	act. ptcpl	fs	cstr	gen.
qtlt	/qātil(a)ta/	‘killing of’	vb.	G	act. ptcpl	fs	cstr	acc.
qtlm	/qātilūma/	‘killing’	vb.	G	act. ptcpl	mp	abs	nom.
qtlm	/qātilīma/	‘killing’	vb.	G	act. ptcpl	mp	abs	gen., acc.
qtl	/qātilū/	‘killing of’	vb.	G	act. ptcpl	mp	cstr	nom.
qtl	/qātilī/	‘killing of’	vb.	G	act. ptcpl	mp	cstr	gen., acc.
qtlt	/qātilātu/	‘killing’	vb.	G	act. ptcpl	fp	abs	nom.
qtlt	/qātilāti/	‘killing’	vb.	G	act. ptcpl	fp	abs	gen., acc.
qtlt	/qātilātu/	‘killing of’	vb.	G	act. ptcpl	fp	cstr	nom.
qtlt	/qātilāti/	‘killing of’	vb.	G	act. ptcpl	fp	cstr	gen., acc.
qtlm	/qātilāma/i/	‘killing’	vb.	G	act. ptcpl	md	abs	nom.
qtlm	/qātilêma/i/	‘killing’	vb.	G	act. ptcpl	md	abs	gen., acc.
qtl	/qātilā/	‘killing of’	vb.	G	act. ptcpl	md	cstr	nom.
qtl	/qātilê/	‘killing of’	vb.	G	act. ptcpl	md	cstr	gen., acc.
qtlt	/qātilatāma/i/	‘killing’	vb.	G	act. ptcpl	fd	abs	nom.
qtlt	/qātilatêma/i/	‘killing’	vb.	G	act. ptcpl	fd	abs	gen., acc.
qtlt	/qātilatā/	‘killing of’	vb.	G	act. ptcpl	fd	cstr	nom.
qtlt	/qātilatê/	‘killing of’	vb.	G	act. ptcpl	fd	cstr	gen., acc.
"""

pattern_G_act_ptcpl_strong = """
translit	transcript	gloss	pos	stem	conjugation	form	state	case
123	/1ā2i3u/	‘Xing’	vb.	G	act. ptcpl	ms	abs	nom.
123	/1ā2i3i/	‘Xing’	vb.	G	act. ptcpl	ms	abs	gen.
123	/1ā2i3a/	‘Xing’	vb.	G	act. ptcpl	ms	abs	acc.
123	/1ā2i3u/	‘Xing of’	vb.	G	act. ptcpl	ms	cstr	nom.
123	/1ā2i3i/	‘Xing of’	vb.	G	act. ptcpl	ms	cstr	gen.
123	/1ā2i3a/	‘Xing of’	vb.	G	act. ptcpl	ms	cstr	acc.
123t	/1ā2i3(a)tu/	‘Xing’	vb.	G	act. ptcpl	fs	abs	nom.
123t	/1ā2i3(a)ti/	‘Xing’	vb.	G	act. ptcpl	fs	abs	gen.
123t	/1ā2i3(a)ta/	‘Xing’	vb.	G	act. ptcpl	fs	abs	acc.
123t	/1ā2i3(a)tu/	‘Xing of’	vb.	G	act. ptcpl	fs	cstr	nom.
123t	/1ā2i3(a)ti/	‘Xing of’	vb.	G	act. ptcpl	fs	cstr	gen.
123t	/1ā2i3(a)ta/	‘Xing of’	vb.	G	act. ptcpl	fs	cstr	acc.
123m	/1ā2i3ūma/	‘Xing’	vb.	G	act. ptcpl	mp	abs	nom.
123m	/1ā2i3īma/	‘Xing’	vb.	G	act. ptcpl	mp	abs	gen., acc.
123	/1ā2i3ū/	‘Xing of’	vb.	G	act. ptcpl	mp	cstr	nom.
123	/1ā2i3ī/	‘Xing of’	vb.	G	act. ptcpl	mp	cstr	gen., acc.
123t	/1ā2i3ātu/	‘Xing’	vb.	G	act. ptcpl	fp	abs	nom.
123t	/1ā2i3āti/	‘Xing’	vb.	G	act. ptcpl	fp	abs	gen., acc.
123t	/1ā2i3ātu/	‘Xing of’	vb.	G	act. ptcpl	fp	cstr	nom.
123t	/1ā2i3āti/	‘Xing of’	vb.	G	act. ptcpl	fp	cstr	gen., acc.
123m	/1ā2i3āma/i/	‘Xing’	vb.	G	act. ptcpl	md	abs	nom.
123m	/1ā2i3êma/i/	‘Xing’	vb.	G	act. ptcpl	md	abs	gen., acc.
123	/1ā2i3ā/	‘Xing of’	vb.	G	act. ptcpl	md	cstr	nom.
123	/1ā2i3ê/	‘Xing of’	vb.	G	act. ptcpl	md	cstr	gen., acc.
123t	/1ā2i3atāma/i/	‘Xing’	vb.	G	act. ptcpl	fd	abs	nom.
123t	/1ā2i3atêma/i/	‘Xing’	vb.	G	act. ptcpl	fd	abs	gen., acc.
123t	/1ā2i3atā/	‘Xing of’	vb.	G	act. ptcpl	fd	cstr	nom.
123t	/1ā2i3atê/	‘Xing of’	vb.	G	act. ptcpl	fd	cstr	gen., acc.
"""

# G Infinitive
paradigm_G_inf_strong = """
translit	transcript	gloss	pos	stem	conjugation
lảk	/laˀāku/	‘to send’	vb.	G	inf.
šảl	/šaˀālu/	‘to ask’	vb.	G	inf.
rgm	/ragāmu/	‘to speak’	vb.	G	inf.
ỉkl	/ˀiklu/	‘eating’	vb.	G	inf.
bk	/bikû/	‘weeping, to weep’	vb.	G	inf.
nḫr	/niġru/	‘to guard’	vb.	G	inf.
pṭr	/piṭru/	‘to loosen’	vb.	G	inf.
"""

pattern_G_inf_strong = """
translit	transcript	gloss	pos	stem	conjugation
123	/1a2ā3u/	‘to X’	vb.	G	inf.
"""

# Gp stem

paradigm_Gp_suffc_qatal_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qutala/(?)	‘he was killed’	vb.	Gp	suffc.	3ms
qtlt	/qutalat/(?)	‘she was killed’	vb.	Gp	suffc.	3fs
qtlt	/qutaltā̆/(?)	‘you were killed’	vb.	Gp	suffc.	2ms
qtlt	/qutaltī̆/(?)	‘you were killed’	vb.	Gp	suffc.	2fs
qtlt	/qutaltū̆/(?)	‘I was killed’	vb.	Gp	suffc.	1cs
qtl	/qutalā/(?)	‘they two were killed’	vb.	Gp	suffc.	3md
qtlt	/qutaltā/(?)	‘they two were killed’	vb.	Gp	suffc.	3fd
qtltm	/qutaltumā/(?)	‘you two were killed’	vb.	Gp	suffc.	2cd
qtlny	/qutalnV̄yā/(?)	‘we two were killed’	vb.	Gp	suffc.	1cd
qtl	/qutalū/(?)	‘they were killed’	vb.	Gp	suffc.	3mp
qtl	/qutalā/(?)	‘they were killed’	vb.	Gp	suffc.	3fp
qtltm	/qutaltum(ū)/(?)	‘you were killed’	vb.	Gp	suffc.	2mp
qtltn	/qutaltin(ā/nā̆)/(?)	‘you were killed’	vb.	Gp	suffc.	2fp
qtln	/qutalnV̄̆/(?)	‘we were killed’	vb.	Gp	suffc.	1cp
"""

# paradigm_Gp_suffc_qatil_strong = '''
# translit	transcript	gloss	pos	stem	conjugation	form
# qtl	/qutila/(?)	‘he was killed’	vb.	Gp	suffc.	3ms
# qtlt	/qutilat/(?)	‘she was killed’	vb.	Gp	suffc.	3fs
# qtlt	/qutiltā̆/(?)	‘you were killed’	vb.	Gp	suffc.	2ms
# qtlt	/qutiltī̆/(?)	‘you were killed’	vb.	Gp	suffc.	2fs
# qtlt	/qutiltū̆/(?)	‘I was killed’	vb.	Gp	suffc.	1cs
# qtl	/qutilā/(?)	‘they two were killed’	vb.	Gp	suffc.	3md
# qtlt	/qutiltā/(?)	‘they two were killed’	vb.	Gp	suffc.	3fd
# qtltm	/qutiltumā/(?)	‘you two were killed’	vb.	Gp	suffc.	2cd
# qtlny	/qutilnV̄yā/(?)	‘we two were killed’	vb.	Gp	suffc.	1cd
# qtl	/qutilū/(?)	‘they were killed’	vb.	Gp	suffc.	3mp
# qtl	/qutilā/(?)	‘they were killed’	vb.	Gp	suffc.	3fp
# qtltm	/qutiltum(ū)/(?)	‘you were killed’	vb.	Gp	suffc.	2mp
# qtltn	/qutiltin(ā/nā̆)/(?)	‘you were killed’	vb.	Gp	suffc.	2fp
# qtln	/qutilnV̄̆/(?)	‘we were killed’	vb.	Gp	suffc.	1cp
# '''

paradigm_Gp_suffc_qatil_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
šỉl	/şuˀila/(?)	‘he was asked’	vb.	Gp	suffc.	3ms
šỉlt	/şuˀilat/(?)	‘she was asked’	vb.	Gp	suffc.	3fs
šỉlt	/şuˀiltā̆/(?)	‘you were asked’	vb.	Gp	suffc.	2ms
šỉlt	/şuˀiltī̆/(?)	‘you were asked’	vb.	Gp	suffc.	2fs
šỉlt	/şuˀiltū̆/(?)	‘I was asked’	vb.	Gp	suffc.	1cs
šỉl	/şuˀilā/(?)	‘they two were asked’	vb.	Gp	suffc.	3md
šỉlt	/şuˀiltā/(?)	‘they two were asked’	vb.	Gp	suffc.	3fd
šỉltm	/şuˀiltumā/(?)	‘you two were asked’	vb.	Gp	suffc.	2cd
šlny	/şuˀilnV̄yā/(?)	‘we two were asked’	vb.	Gp	suffc.	1cd
šỉl	/şuˀilū/(?)	‘they were asked’	vb.	Gp	suffc.	3mp
šỉl	/şuˀilā/(?)	‘they were asked’	vb.	Gp	suffc.	3fp
šỉltm	/şuˀiltum(ū)/(?)	‘you were asked’	vb.	Gp	suffc.	2mp
šỉltn	/şuˀiltin(ā/nā̆)/(?)	‘you were asked’	vb.	Gp	suffc.	2fp
šln	/şuˀilnV̄̆/(?)	‘we were asked’	vb.	Gp	suffc.	1cp
"""

paradigm_Gp_suffc_qatul_strong = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qutula/(?)	‘he was killed’	vb.	Gp	suffc.	3ms
qtlt	/qutulat/(?)	‘she was killed’	vb.	Gp	suffc.	3fs
qtlt	/qutultā̆/(?)	‘you were killed’	vb.	Gp	suffc.	2ms
qtlt	/qutultī̆/(?)	‘you were killed’	vb.	Gp	suffc.	2fs
qtlt	/qutultū̆/(?)	‘I was killed’	vb.	Gp	suffc.	1cs
qtl	/qutulā/(?)	‘they two were killed’	vb.	Gp	suffc.	3md
qtlt	/qutultā/(?)	‘they two were killed’	vb.	Gp	suffc.	3fd
qtltm	/qutultumā/(?)	‘you two were killed’	vb.	Gp	suffc.	2cd
qtlny	/qutulnV̄yā/(?)	‘we two were killed’	vb.	Gp	suffc.	1cd
qtl	/qutulū/(?)	‘they were killed’	vb.	Gp	suffc.	3mp
qtl	/qutulā/(?)	‘they were killed’	vb.	Gp	suffc.	3fp
qtltm	/qutultum(ū)/(?)	‘you were killed’	vb.	Gp	suffc.	2mp
qtltn	/qutultin(ā/nā̆)/(?)	‘you were killed’	vb.	Gp	suffc.	2fp
qtln	/qutulnV̄̆/(?)	‘we were killed’	vb.	Gp	suffc.	1cp
"""

paradigm_Gp_pref_qatul_strong_indic = """
translit	transcript	gloss	pos	stem	conjugation	form
yqtl	/yuqtulu/(?)	‘he is killed’	vb.	Gp	pref.	3ms
tqtl	/tuqtulu/(?)	‘she is killed’	vb.	Gp	pref.	3fs
tqtl	/tuqtulu/(?)	‘you are killed’	vb.	Gp	pref.	2ms
tqtln	/tuqtulīna/(?)	‘you are killed’	vb.	Gp	pref.	2fs
ảqtl	/ˀuqtulu/(?)	‘I am killed’	vb.	Gp	pref.	1cs
"""
# It is not too clear what the forms are from Huenergrad's table.


paradigm_derived_stems_short = """
translit	transcript	gloss	pos	stem	conjugation	form
qtl	/qatVla/	‘he killed’	vb.	G	suffc.	3ms
yqtl	/yaqtul-/	‘he kills’	vb.	G	pref.	3ms
yqtl	/yaqtil-/	‘he kills’	vb.	G	pref.	3ms
yqtl	/yaqtal-/	‘he kills’	vb.	G	pref.	3ms
qtl	/qutul/	‘kill!’	vb.	G	impv.	ms
qtl	/qitil/	‘kill!’	vb.	G	impv.	ms
qtl	/qatal/	‘kill!’	vb.	G	impv.	ms
qtl	/qātilu/	‘killing’	vb.	G	ptcpl.	ms
qtl	/qatālu/	‘to kill’	vb.	G	inf.	
qtl	/qitlu/	‘to kill’	vb.	G	inf.	
qtl	/qutila/(?), /qutala/(?)	‘he was killed’	vb.	Gpass.	suffc.	3ms
yqtl	/yuqtal-/	‘he is killed’	vb.	Gpass.	pref.	3ms
?	/?/	‘be killed!’	vb.	Gpass.	impv.	ms
qtl	/qatV̄̆lu/	‘being killed’	vb.	Gpass.	ptcpl.	ms
-	-	‘to be killed’	vb.	Gpass.	inf.	
ỉqttl	/ˀiqtatVla/	‘he killed himself’	vb.	Gt	suffc.	3ms
yqttl	/yiqtatil-/	‘he kills himself’	vb.	Gt	pref.	3ms
ỉqttl	/ˀiqtatil/	‘kill himself!’	vb.	Gt	impv.	ms
mqttl	/mVqtatilu/	‘killing oneself’	vb.	Gt	ptcpl.	ms
tqttl	/tVqtatVlu/	‘to kill oneself’	vb.	Gt	inf.	
nqtl	/naqtala/	‘he was killed’	vb.	N	suffc.	3ms
yqtl	/yiqqatil-/	‘he is killed’	vb.	N	pref.	3ms
nqtl	/naqtil/(?)	‘be killed!’	vb.	N	impv.	ms
nqtl	/naqtalu/(?)	‘being killed’	vb.	N	ptcpl.	ms
nqtl	/naqtālu/(?)	‘to be killed’	vb.	N	inf.	
qtl	/qattila/(?)	‘he was made to kill’	vb.	D	suffc.	3ms
yqtl	/yVqattil-/	‘he makes to kill’	vb.	D	pref.	3ms
qtl	/qattil/	‘make to kill!’	vb.	D	impv.	ms
mqtl	/mVqattilu/	‘making to kill’	vb.	D	ptcpl.	ms
qtl	/quttalu/	‘to make to kill’	vb.	D	inf.	
qtl	/quttila/(?), /quttala/(?)	‘he was made to be killed’	vb.	Dpass.	suffc.	3ms
yqtl	/yVqVttal-/	‘he makes to be killed’	vb.	Dpass.	pref.	3ms
?	/?/	‘make to be killed!’	vb.	Dpass.	impv.	ms
mqtl	/mVqVttalu/	‘making to be killed’	vb.	Dpass.	ptcpl.	ms
-	-	‘to make to be killed’	vb.	Dpass.	inf.	
tqtl	/taqattala/(?)	‘he was made to kill’	vb.	tD	suffc.	3ms
ytqtl	/yVtqattal-/	‘he makes to kill’	vb.	tD	pref.	3ms
tqtl	/taqattal/(?)	‘make to kill!’	vb.	tD	impv.	ms
?	/?/	‘making to kill’	vb.	tD	ptcpl.	ms
tqtl	/tuqattilu/	‘to make to kill’	vb.	tD	inf.	
šqtl	/šaqtila/	‘he was made to kill’	vb.	Š	suffc.	3ms
yšqtl	/yVšaqtil-/	‘he makes to kill’	vb.	Š	pref.	3ms
šqtl	/šaqtil/	‘make to kill!’	vb.	Š	impv.	ms
mšqtl	/mVšaqtilu/	‘making to kill’	vb.	Š	ptcpl.	ms
šqtl	/šuqtalu/(?)	‘to make to kill’	vb.	Š	inf.	
šqtl	/šuqtila/(?), /šuqtala/(?)	‘he was made to be killed’	vb.	Špass.	suffc.	3ms
yšqtl	/yVšVqtal-/	‘he makes to be killed’	vb.	Špass.	pref.	3ms
?	/?/	‘make to be killed!’	vb.	Špass.	impv.	ms
mšqtl	/mVšVqtalu/	‘making to be killed’	vb.	Špass.	ptcpl.	ms
-	-	‘to make to be killed’	vb.	Špass.	inf.	
*ʔštqtl	*/(ˀV)štaqtala/(?)	‘he was made to kill’	vb.	Št	suffc.	3ms
yštqtl	/yištaqtil-/	‘he makes to kill’	vb.	Št	pref.	3ms
?	/?/	‘make to kill!’	vb.	Št	impv.	ms
mštqtl	/mVštaqtilu/	‘making to kill’	vb.	Št	ptcpl.	ms
?	/?/	‘to make to kill’	vb.	Št	inf.	
"""

pattern_derived_stems_short = """
translit	transcript	gloss	pos	stem	conjugation	form
123	/1a2V3a/	‘he Xed’	vb.	G	suffc.	3ms
y123	/ya12u3-/	‘he Xs’	vb.	G	pref.	3ms
y123	/ya12i3-/	‘he Xs’	vb.	G	pref.	3ms
y123	/ya12a3-/	‘he Xs’	vb.	G	pref.	3ms
123	/1u2u3/	‘X!’	vb.	G	impv.	ms
123	/1i2i3/	‘X!’	vb.	G	impv.	ms
123	/1a2a3/	‘X!’	vb.	G	impv.	ms
123	/1ā2i3u/	‘Xing’	vb.	G	ptcpl.	ms
123	/1a2ā3u/	‘to X’	vb.	G	inf.	
123	/1i23u/	‘to X’	vb.	G	inf.	
123	/1u2i3a/(?), /1u2a3a/(?)	‘he was Xed’	vb.	Gpass.	suffc.	3ms
y123	/yu12a3-/	‘he is Xed’	vb.	Gpass.	pref.	3ms
?	/?/	‘be Xed!’	vb.	Gpass.	impv.	ms
123	/1a2V̄̆3u/	‘being Xed’	vb.	Gpass.	ptcpl.	ms
-	-	‘to be Xed’	vb.	Gpass.	inf.	
ỉ1t23	/ˀi1ta2V3a/	‘he Xed himself’	vb.	Gt	suffc.	3ms
y1t23	/yi1ta2i3-/	‘he Xs himself’	vb.	Gt	pref.	3ms
ỉ1t23	/ˀi1ta2i3/	‘X himself!’	vb.	Gt	impv.	ms
m1t23	/mV1ta2i3u/	‘Xing oneself’	vb.	Gt	ptcpl.	ms
t1t23	/tV1ta2V3u/	‘to X oneself’	vb.	Gt	inf.	
n123	/na12a3a/	‘he was Xed’	vb.	N	suffc.	3ms
y123	/yi11a2i3-/	‘he is Xed’	vb.	N	pref.	3ms
n123	/na12i3/(?)	‘be Xed!’	vb.	N	impv.	ms
n123	/na12a3u/(?)	‘being Xed’	vb.	N	ptcpl.	ms
n123	/na12ā3u/(?)	‘to be Xed’	vb.	N	inf.	
123	/1a22i3a/(?)	‘he was made to X’	vb.	D	suffc.	3ms
y123	/yV1a22i3-/	‘he makes to X’	vb.	D	pref.	3ms
123	/1a22i3/	‘make to X!’	vb.	D	impv.	ms
m123	/mV1a22i3u/	‘making to X’	vb.	D	ptcpl.	ms
123	/1u22a3u/	‘to make to X’	vb.	D	inf.	
123	/1u22i3a/(?), /1u22a3a/(?)	‘he was made to be Xed’	vb.	Dpass.	suffc.	3ms
y123	/yV1V22a3-/	‘he makes to be Xed’	vb.	Dpass.	pref.	3ms
?	/?/	‘make to be Xed!’	vb.	Dpass.	impv.	ms
m123	/mV1V22a3u/	‘making to be Xed’	vb.	Dpass.	ptcpl.	ms
-	-	‘to make to be Xed’	vb.	Dpass.	inf.	
t123	/ta1a22a3a/(?)	‘he was made to X’	vb.	tD	suffc.	3ms
yt123	/yVt1a22a3-/	‘he makes to X’	vb.	tD	pref.	3ms
t123	/ta1a22a3/(?)	‘make to X!’	vb.	tD	impv.	ms
?	/?/	‘making to X’	vb.	tD	ptcpl.	ms
t123	/tu1a22i3u/	‘to make to X’	vb.	tD	inf.	
š123	/ša12i3a/	‘he was made to X’	vb.	Š	suffc.	3ms
yš123	/yVša12i3-/	‘he makes to X’	vb.	Š	pref.	3ms
š123	/ša12i3/	‘make to X!’	vb.	Š	impv.	ms
mš123	/mVša12i3u/	‘making to X’	vb.	Š	ptcpl.	ms
š123	/šu12a3u/(?)	‘to make to X’	vb.	Š	inf.	
š123	/šu12i3a/(?), /šu12a3a/(?)	‘he was made to be Xed’	vb.	Špass.	suffc.	3ms
yš123	/yVšV12a3-/	‘he makes to be Xed’	vb.	Špass.	pref.	3ms
?	/?/	‘make to be Xed!’	vb.	Špass.	impv.	ms
mš123	/mVšV12a3u/	‘making to be Xed’	vb.	Špass.	ptcpl.	ms
-	-	‘to make to be Xed’	vb.	Špass.	inf.	
*ʔšt123	*/(ˀV)šta12a3a/(?)	‘he was made to X’	vb.	Št	suffc.	3ms
yšt123	/yišta12i3-/	‘he makes to X’	vb.	Št	pref.	3ms
?	/?/	‘make to X!’	vb.	Št	impv.	ms
mšt123	/mVšta12i3u/	‘making to X’	vb.	Št	ptcpl.	ms
?	/?/	‘to make to X’	vb.	Št	inf.	
"""

# personal pronouns

paradigm_pers_pronouns = """
translit	transcript	gloss	pos	form	case
ảnk	/ˀanākū̆/	‘I‘	pers. pron.	1cs	nom.
ản	/ˀanā̆/	‘I‘	pers. pron.	1cs	nom.
ảt	/ˀattā̆/	‘you‘	pers. pron.	2ms	nom.
ảt	/ˀattī̆/	‘you‘	pers. pron.	2fs	nom.
hw	/huwa/	‘he/it‘	pers. pron.	3ms	nom.
hy	/hiya/	‘she/it‘	pers. pron.	3fs	nom.
ủnk?	-	‘we two‘	pers. pron.	1cd	nom.
ảtm	/ˀattumā/	‘you two‘	pers. pron.	2md	nom.
			pers. pron.	2fd	nom.
hm	/humā/	‘they two‘	pers. pron.	3cd	nom.
			pers. pron.	1cp	nom.
a͗tm	/ˀattum(ū)/	‘we‘	pers. pron.	2mp	nom.
			pers. pron.	2fp	nom.
hm	/hum(ū)/	‘they‘	pers. pron.	3mp	nom.
hn	/hin(ā)/, /hin(na)/	‘they‘	pers. pron.	3fp	nom.
hwt 	/huwā̆tī̆/	‘his; him‘	pers. pron.	3ms	gen.; acc.
hyt	/hiyā̆tī̆/(?)	‘her‘	pers. pron.	3fs	gen.; acc.
hmt	/humātī̆/(?)	‘their; them‘	pers. pron.	3cd	gen.; acc.
hmt	/humūtī̆/(?)	‘their; them‘	pers. pron.	3mp	gen.; acc.
"""

paradigm_rel_pronoun = """
translit	transcript	gloss	pos	form	case
d	/dū/		rel. pron.	ms	nom.
d	/dī/		rel. pron.	ms	gen.
d	/dā/		rel. pron.	ms	acc.
dt	/dūtu/		rel. pron.	mp	nom.
dt	/dūti/(?)		rel. pron.	mp	gen.; acc.
dt	/dātu/		rel. pron.	fs	nom.
dt	/dāti/		rel. pron.	fs	gen.
dt	/dāta/		rel. pron.	fs	acc.
dt	/dātu/(?)		rel. pron.	fp	nom.
dt	/dāti/(?)		rel. pron.	fp	gen.; acc.
"""

paradigm_pers_pronom_suffixes = """
translit	transcript	gloss	pos	form	used with
-ø	/-ī/	‘my‘	pers. pron. suff.	1cs	nom. sg./nom. f. pl. nouns
-y	/-ya/	‘my‘	pers. pron. suff.	1cs	other nouns and prep.
-n	/-nī/	‘my‘	pers. pron. suff.	1cs	finite verbs as objects
-k	/-kā̆/	‘your‘	pers. pron. suff.	2ms	
-k	/-kī̆/	‘your‘	pers. pron. suff.	2fs	
-h	/-hū̆/	‘his‘	pers. pron. suff.	3ms	
-n	/-(V)nnū̆/(?)	‘him‘	pers. pron. suff.	3ms	finite verbs as objects
-nh	/-(V)n(na)hū̆/(?)	‘him‘	pers. pron. suff.	3ms	finite verbs as objects
-nn	/-(V)n(n)annū̆/(?)	‘him‘	pers. pron. suff.	3ms	finite verbs as objects
-h	/-hā̆/	‘her‘	pers. pron. suff.	3fs	
-n	/-(V)nnā̆/(?)	‘her‘	pers. pron. suff.	3fs	finite verbs as objects
-nh	/-(V)n(na)hā̆/(?)	‘her‘	pers. pron. suff.	3fs	finite verbs as objects
-nn	/-(V)n(n)annā̆/(?)	‘her‘	pers. pron. suff.	3fs	finite verbs as objects
-ny	/-nāyā/(?)	‘our two‘	pers. pron. suff.	1cd	
-km	/-kum(ā)/	‘your two‘	pers. pron. suff.	2cd	
-hm	/-humā/	‘their two‘	pers. pron. suff.	3cd	
-n	/-nā/	‘our‘	pers. pron. suff.	1cp	
-km	/-kum(ū)/	‘your‘	pers. pron. suff.	2mp	
-kn	/-kin(ā)/, /-kin(na)/(?)	‘your‘	pers. pron. suff.	2fp	
-hm	/-hum(ū)/	‘their‘	pers. pron. suff.	3mp	
-hn	/-hin(ā)/, /-hin(na)/(?)	‘their‘	pers. pron. suff.	3fp	 
"""

# Noun and adjective paradigms

paradigm_adjective = """
translit	transcript	gloss	pos	state	form	case
ṭb	/ṭābu/	‘good’	adj.	abs., cstr.	ms	nom.
ṭb	/ṭābi/	‘good’	adj.	abs., cstr.	ms	gen.
ṭb	/ṭāba/	‘good’	adj.	abs., cstr.	ms	acc.
ṭbt	/ṭābatu/	‘good’	adj.	abs., cstr.	fs	nom.
ṭbt	/ṭābati/	‘good’	adj.	abs., cstr.	fs	gen.
ṭbt	/ṭābata/	‘good’	adj.	abs., cstr.	fs	acc.
ṭbm	/ṭābūma/	‘good’	adj.	abs.	mp	nom.
ṭb	/ṭābū/	‘good of’	adj.	cstr. 	mp	nom.
ṭbm	/ṭābīma/	‘good’	adj.	abs.	mp	gen., acc.
ṭb	/ṭābī/	‘good of’	adj.	cstr.	mp	gen., acc.
ṭbt	/ṭābātu/	‘good’	adj.	abs., cstr.	fp	nom.
ṭbt	/ṭābāti/	‘good’	adj.	abs., cstr.	fp	gen., acc.
ṭbm	/ṭābāma/i/	‘good’	adj.	abs.	md	nom.
ṭb	/ṭābā/	‘good of’	adj.	cstr.	md	nom.
ṭbm	/ṭābêma/i/	‘good’	adj.	abs.	md	gen., acc.
ṭb	/ṭābê/	‘good of’	adj.	cstr.	md	gen., acc.
ṭbtm	/ṭābatāma/i/	‘good’	adj.	abs.	fd	nom.
ṭbt	/ṭābatā/	‘good of’	adj.	cstr.	fd	nom.
ṭbtm	/ṭābatêma/i/	‘good’	adj.	abs.	fd	gen., acc.
ṭbt	/ṭābatê/	‘good of’	adj.	cstr.	fd	gen., acc.
"""

paradigm_nominal = """
translit	transcript	gloss	pos	state	form	case
mlk	/malku/	‘king‘	n.	abs., cstr.	ms	nom.
mlk	/malki/	‘of king‘	n.	abs., cstr.	ms	gen.
mlk	/malka/	‘king‘	n.	abs., cstr.	ms	acc.
mlkt	/malkatu/	‘queen‘	n.	abs., cstr.	fs	nom.
mlkt	/malkati/	‘of queen‘	n.	abs., cstr.	fs	gen.
mlkt	/malkata/	‘queen‘	n.	abs., cstr.	fs	acc.
mlkm	/malkūma/	‘kings‘	n.	abs.	mp	nom.
mlk	/malkū/	‘kings of’	n.	cstr. 	mp	nom.
mlkm	/malkīma/	‘kings of’	n.	abs.	mp	gen., acc.
mlk	/malkī/	‘kings of’	n.	cstr.	mp	gen., acc.
mlkt	/malkātu/	‘queens‘	n.	abs., cstr.	fp	nom.
mlkt	/malkāti/	‘queens of’	n.	abs., cstr.	fp	gen., acc.
mlkm	/malkāma/i/	‘two kings’	n.	abs.	md	nom.
mlk	/malkā/	‘two kings of’	n.	cstr.	md	nom.
mlkm	/malkêma/i/	‘of two kings’	n.	abs.	md	gen., acc.
mlk	/malkê/	‘of two kings of’	n.	cstr.	md	gen., acc.
mlktm	/malkatāma/i/	‘two queens’	n.	abs.	fd	nom.
mlkt	/malkatā/	‘two queens of’	n.	cstr.	fd	nom.
mlktm	/malkatêma/i/	‘(of) two queens’	n.	abs.	fd	gen., acc.
mlkt	/malkatê/	‘(of) two queens of’	n.	cstr.	fd	gen., acc.
"""

paradigm_noun_suffixes = """
translit	transcript	gloss	pos	form	state	case	suff_form
mlk	/malk-ī/	‘my king’	noun + suff.	ms	cstr.	nom.	1cs
mlky	/malki-ya/	‘of my king’	noun + suff.	ms	cstr.	gen.	1cs
mlky	/malka-ya/	‘my king’	noun + suff.	ms	cstr.	acc.	1cs
mlkk	/malku-kā̆/	‘your king’	noun + suff.	ms	cstr.	nom.	2ms
mlkk	/malki-kā̆/	‘of your king’	noun + suff.	ms	cstr.	gen.	2ms
mlkk	/malka-kā̆/	‘your king’	noun + suff.	ms	cstr.	acc.	2ms
mlkk	/malku-kī̆/	‘your king’	noun + suff.	ms	cstr.	nom.	2fs
mlkk	/malki-kī̆/	‘of your king’	noun + suff.	ms	cstr.	gen.	2fs
mlkk	/malka-kī̆/	‘your king’	noun + suff.	ms	cstr.	acc.	2fs
mlkh	/malku-hū̆/	‘his king’	noun + suff.	ms	cstr.	nom.	3ms
mlkh	/malki-hū̆/	‘of his king’	noun + suff.	ms	cstr.	gen.	3ms
mlkh	/malka-hū̆/	‘his king’	noun + suff.	ms	cstr.	acc.	3ms
mlkh	/malku-hā/	‘her king’	noun + suff.	ms	cstr.	nom.	3fs
mlkh	/malki-hā/	‘of her king’	noun + suff.	ms	cstr.	gen.	3fs
mlkh	/malka-hā/	‘her king’	noun + suff.	ms	cstr.	acc.	3fs
mlkny	/malk-nāyā/(?)	‘our king’	noun + suff.	ms	cstr.	nom.	1cd
mlkny	/malki-nāyā/(?)	‘of our king’	noun + suff.	ms	cstr.	gen.	1cd
mlkny	/malka-nāyā/(?)	‘our king’	noun + suff.	ms	cstr.	acc.	1cd
mlkkm	/malku-kumā/	‘your king’	noun + suff.	ms	cstr.	nom.	2cd
mlkkm	/malki-kumā/	‘of your king’	noun + suff.	ms	cstr.	gen.	2cd
mlkkm	/malka-kumā/	‘your king’	noun + suff.	ms	cstr.	acc.	2cd
mlkhm	/malku-humā/	‘their king’	noun + suff.	ms	cstr.	nom.	3cd
mlkhm	/malki-humā/	‘of their king’	noun + suff.	ms	cstr.	gen.	3cd
mlkhm	/malka-humā/	‘their king’	noun + suff.	ms	cstr.	acc.	3cd
mlkn	/malk-nā/	‘our king’	noun + suff.	ms	cstr.	nom.	1cp
mlkn	/malki-nā/	‘our king’	noun + suff.	ms	cstr.	gen.	1cp
mlkn	/malka-nā/	‘our king’	noun + suff.	ms	cstr.	acc.	1cp
mlkm	/malk-kum(ū)/	‘your king’	noun + suff.	ms	cstr.	nom.	2mp
mlkm	/malki-kum(ū)/	‘your king’	noun + suff.	ms	cstr.	gen.	2mp
mlkm	/malka-kum(ū)/	‘your king’	noun + suff.	ms	cstr.	acc.	2mp
mlkn	/malk-kin(ā)/, /malk-kin(na)/(?)	‘your king’	noun + suff.	ms	cstr.	nom.	2fp
mlkn	/malki-kin(ā)/, /malki-kin(na)/(?)	‘your king’	noun + suff.	ms	cstr.	gen.	2fp
mlkn	/malka-kin(ā)/, /malka-kin(na)/(?)	‘your king’	noun + suff.	ms	cstr.	acc.	2fp
mlkhm	/malk-hum(ū)/	‘their king’	noun + suff.	ms	cstr.	nom.	3mp
mlkhm	/malki-hum(ū)/	‘their king’	noun + suff.	ms	cstr.	gen.	3mp
mlkhm	/malka-hum(ū)/	‘their king’	noun + suff.	ms	cstr.	acc.	3mp
mlkhn	/malk-hin(ā)/, /malk-hin(na)/(?)	‘their king’	noun + suff.	ms	cstr.	nom.	3fp
mlkhn	/malki-hin(ā)/, /malki-hin(na)/(?)	‘their king’	noun + suff.	ms	cstr.	gen.	3fp
mlkhn	/malka-hin(ā)/, /malka-hin(na)/(?)	‘their king’	noun + suff.	ms	cstr.	acc.	3fp
mlkt	/malkat-ī/	‘my queen’	noun + suff.	fs	cstr.	nom.	1cs
mlkty	/malkati-ya/	‘of my queen’	noun + suff.	fs	cstr.	gen.	1cs
mlkty	/malkata-ya/	‘my queen’	noun + suff.	fs	cstr.	acc.	1cs
mlktk	/malkatu-kā̆/	‘your queen’	noun + suff.	fs	cstr.	nom.	2ms
mlktk	/malkati-kā̆/	‘of your queen’	noun + suff.	fs	cstr.	gen.	2ms
mlktk	/malkata-kā̆/	‘your queen’	noun + suff.	fs	cstr.	acc.	2ms
mlktk	/malkatu-kī̆/	‘your queen’	noun + suff.	fs	cstr.	nom.	2fs
mlktk	/malkati-kī̆/	‘of your queen’	noun + suff.	fs	cstr.	gen.	2fs
mlktk	/malkata-kī̆/	‘your queen’	noun + suff.	fs	cstr.	acc.	2fs
mlkth	/malkatu-hū̆/	‘his queen’	noun + suff.	fs	cstr.	nom.	3ms
mlkth	/malkati-hū̆/	‘of his queen’	noun + suff.	fs	cstr.	gen.	3ms
mlkth	/malkata-hū̆/	‘his queen’	noun + suff.	fs	cstr.	acc.	3ms
mlkth	/malkatu-hā/	‘her queen’	noun + suff.	fs	cstr.	nom.	3fs
mlkth	/malkati-hā/	‘of her queen’	noun + suff.	fs	cstr.	gen.	3fs
mlkth	/malkata-hā/	‘her queen’	noun + suff.	fs	cstr.	acc.	3fs
mlktny	/malkat-nāyā/(?)	‘our queen’	noun + suff.	fs	cstr.	nom.	1cd
mlktny	/malkati-nāyā/(?)	‘of our queen’	noun + suff.	fs	cstr.	gen.	1cd
mlktny	/malkata-nāyā/(?)	‘our queen’	noun + suff.	fs	cstr.	acc.	1cd
mlktkm	/malkatu-kumā/	‘your queen’	noun + suff.	fs	cstr.	nom.	2cd
mlktkm	/malkati-kumā/	‘of your queen’	noun + suff.	fs	cstr.	gen.	2cd
mlktkm	/malkata-kumā/	‘your queen’	noun + suff.	fs	cstr.	acc.	2cd
mlkthm	/malkatu-humā/	‘their queen’	noun + suff.	fs	cstr.	nom.	3cd
mlkthm	/malkati-humā/	‘of their queen’	noun + suff.	fs	cstr.	gen.	3cd
mlkthm	/malkata-humā/	‘their queen’	noun + suff.	fs	cstr.	acc.	3cd
mlktn	/malkat-nā/	‘our queen’	noun + suff.	fs	cstr.	nom.	1cp
mlktn	/malkati-nā/	‘our queen’	noun + suff.	fs	cstr.	gen.	1cp
mlktn	/malkata-nā/	‘our queen’	noun + suff.	fs	cstr.	acc.	1cp
mlktm	/malkat-kum(ū)/	‘your queen’	noun + suff.	fs	cstr.	nom.	2mp
mlktm	/malkati-kum(ū)/	‘your queen’	noun + suff.	fs	cstr.	gen.	2mp
mlktm	/malkata-kum(ū)/	‘your queen’	noun + suff.	fs	cstr.	acc.	2mp
mlktn	/malkat-kin(ā)/, /malkat-kin(na)/(?)	‘your queen’	noun + suff.	fs	cstr.	nom.	2fp
mlktn	/malkati-kin(ā)/, /malkati-kin(na)/(?)	‘your queen’	noun + suff.	fs	cstr.	gen.	2fp
mltktn	/malkata-kin(ā)/, /malkata-kin(na)/(?)	‘your queen’	noun + suff.	fs	cstr.	acc.	2fp
mlkhtm	/malkat-hum(ū)/	‘their queen’	noun + suff.	fs	cstr.	nom.	3mp
mlkhtm	/malkati-hum(ū)/	‘their queen’	noun + suff.	fs	cstr.	gen.	3mp
mlkhtm	/malkata-hum(ū)/	‘their queen’	noun + suff.	fs	cstr.	acc.	3mp
mlkhtn	/malkat-hin(ā)/, /malkat-hin(na)/(?)	‘their queen’	noun + suff.	fs	cstr.	nom.	3fp
mlkhtn	/malkati-hin(ā)/, /malkati-hin(na)/(?)	‘their queen’	noun + suff.	fs	cstr.	gen.	3fp
mlkhtn	/malkata-hin(ā)/, /malkata-hin(na)/(?)	‘their queen’	noun + suff.	fs	cstr.	acc.	3fp
mlky	/malakū-ya/	‘my kings’	noun + suff.	mp	cstr.	nom.	1cs
mlky	/malakī-ya/	‘of my kings’	noun + suff.	mp	cstr.	gen., acc.	1cs
mlkk	/malakū-kā̆/	‘your kings’	noun + suff.	mp	cstr.	nom.	2ms
mlkk	/malakī-kā̆/	‘of your kings’	noun + suff.	mp	cstr.	gen., acc.	2ms
mlkk	/malakū-kī̆/	‘your kings’	noun + suff.	mp	cstr.	nom.	2fs
mlkk	/malakī-kī̆/	‘of your kings’	noun + suff.	mp	cstr.	gen., acc.	2fs
mlkh	/malakū-hū̆/	‘his kings’	noun + suff.	mp	cstr.	nom.	3ms
mlkh	/malakī-hū̆/	‘of his kings’	noun + suff.	mp	cstr.	gen., acc.	3ms
mlkh	/malakū-hā/	‘her kings’	noun + suff.	mp	cstr.	nom.	3fs
mlkh	/malakī-hā/	‘of her kings’	noun + suff.	mp	cstr.	gen., acc.	3fs
mlkny	/malakū-nāyā/(?)	‘our kings’	noun + suff.	mp	cstr.	nom.	1cd
mlkny	/malakī-nāyā/(?)	‘of our kings’	noun + suff.	mp	cstr.	gen., acc.	1cd
mlkkm	/malakū-kumā/	‘your kings’	noun + suff.	mp	cstr.	nom.	2cd
mlkkm	/malakī-kumā/	‘of your kings’	noun + suff.	mp	cstr.	gen., acc.	2cd
mlkhm	/malakū-humā/	‘their kings’	noun + suff.	mp	cstr.	nom.	3cd
mlkhm	/malakī-humā/	‘of their kings’	noun + suff.	mp	cstr.	gen., acc.	3cd
mlkn	/malakū-nā/	‘our kings’	noun + suff.	mp	cstr.	nom.	1cp
mlkn	/malakī-nā/	‘our kings’	noun + suff.	mp	cstr.	gen., acc.	1cp
mlkm	/malakū-kum(ū)/	‘your kings’	noun + suff.	mp	cstr.	nom.	2mp
mlkm	/malakī-kum(ū)/	‘your kings’	noun + suff.	mp	cstr.	gen., acc.	2mp
mlkn	/malakū-kin(ā)/, /malakū-kin(na)/(?)	‘your kings’	noun + suff.	mp	cstr.	nom.	2fp
mlkn	/malakī-kin(ā)/, /malakī-kin(na)/(?)	‘your kings’	noun + suff.	mp	cstr.	gen., acc.	2fp
mlkhm	/malakū-hum(ū)/	‘their kings’	noun + suff.	mp	cstr.	nom.	3mp
mlkhm	/malakī-hum(ū)/	‘their kings’	noun + suff.	mp	cstr.	gen., acc.	3mp
mlkhn	/malakū-hin(ā)/, /malakū-hin(na)/(?)	‘their kings’	noun + suff.	mp	cstr.	nom.	3fp
mlkhn	/malakī-hin(ā)/, /malakī-hin(na)/(?)	‘their kings’	noun + suff.	mp	cstr.	gen., acc.	3fp
mlkty	/malakāt-ī/	‘my queens’	noun + suff.	fp	cstr.	nom.	1cs
mlkty	/malakāti-ya/	‘of my queens’	noun + suff.	fp	cstr.	gen., acc.	1cs
mlktk	/malakātu-kā̆/	‘your queens’	noun + suff.	fp	cstr.	nom.	2ms
mlktk	/malakāti-kā̆/	‘of your queens’	noun + suff.	fp	cstr.	gen., acc.	2ms
mlktk	/malakātu-kī̆/	‘your queens’	noun + suff.	fp	cstr.	nom.	2fs
mlktk	/malakāti-kī̆/	‘of your queens’	noun + suff.	fp	cstr.	gen., acc.	2fs
mlkth	/malakātu-hū̆/	‘his queens’	noun + suff.	fp	cstr.	nom.	3ms
mlkth	/malakāti-hū̆/	‘of his queens’	noun + suff.	fp	cstr.	gen., acc.	3ms
mlkth	/malakātu-hā/	‘her queens’	noun + suff.	fp	cstr.	nom.	3fs
mlkth	/malakāti-hā/	‘of her queens’	noun + suff.	fp	cstr.	gen., acc.	3fs
mlktny	/malakāt-nāyā/(?)	‘our queens’	noun + suff.	fp	cstr.	nom.	1cd
mlktny	/malakāti-nāyā/(?)	‘of our queens’	noun + suff.	fp	cstr.	gen., acc.	1cd
mlktkm	/malakātu-kumā/	‘your queens’	noun + suff.	fp	cstr.	nom.	2cd
mlktkm	/malakāti-kumā/	‘of your queens’	noun + suff.	fp	cstr.	gen., acc.	2cd
mlkthm	/malakātu-humā/	‘their queens’	noun + suff.	fp	cstr.	nom.	3cd
mlkthm	/malakāti-humā/	‘their queens’	noun + suff.	fp	cstr.	gen., acc.	3cd
mlktn	/malakāt-nā/	‘our queens’	noun + suff.	fp	cstr.	nom.	1cp
mlktn	/malakāti-nā/	‘our queens’	noun + suff.	fp	cstr.	gen., acc.	1cp
mlktm	/malakātu-kum(ū)/	‘your queens’	noun + suff.	fp	cstr.	nom.	2mp
mlktm	/malakāti-kum(ū)/	‘your queens’	noun + suff.	fp	cstr.	gen., acc.	2mp
mlktn	/malakātu-kin(ā)/, /malakātu-kin(na)/(?)	‘your queens’	noun + suff.	fp	cstr.	nom.	2fp
mlktn	/malakāti-kin(ā)/, /malakāti-kin(na)/(?)	‘your queens’	noun + suff.	fp	cstr.	gen., acc.	2fp
mlkthm	/malakātu-hum(ū)/	‘their queens’	noun + suff.	fp	cstr.	nom.	3mp
mlkthm	/malakāti-hum(ū)/	‘their queens’	noun + suff.	fp	cstr.	gen., acc.	3mp
mlkthn	/malakātu-hin(ā)/, /malakātu-hin(na)/(?)	‘their queens’	noun + suff.	fp	cstr.	nom.	3fp
mlkthn	/malakāti-hin(ā)/, /malakāti-hin(na)/(?)	‘their queens’	noun + suff.	fp	cstr.	gen., acc.	3fp
ydy	/yadā-ya/	‘my hands’	noun + suff.	md	cstr.	nom.	1cs
ydy	/yadê-ya/	‘of my hands’	noun + suff.	md	cstr.	gen., acc.	1cs
ydk	/yadā-kā̆/	‘your hands’	noun + suff.	md	cstr.	nom.	2ms
ydk	/yadê-kā̆/	‘of your hands’	noun + suff.	md	cstr.	gen., acc.	2ms
ydk	/yadā-kī̆/	‘your hands’	noun + suff.	md	cstr.	nom.	2fs
ydk	/yadê-kī̆/	‘of your hands’	noun + suff.	md	cstr.	gen., acc.	2fs
ydh	/yadā-hū̆/	‘his hands’	noun + suff.	md	cstr.	nom.	3ms
ydh	/yadê-hū̆/	‘of his hands’	noun + suff.	md	cstr.	gen., acc.	3ms
ydh	/yadā-hā/	‘her hands’	noun + suff.	md	cstr.	nom.	3fs
ydh	/yadê-hā/	‘of her hands’	noun + suff.	md	cstr.	gen., acc.	3fs
ydny	/yadā-nāyā/(?)	‘our hands’	noun + suff.	md	cstr.	nom.	1cd
ydny	/yadê-nāyā/(?)	‘of our hands’	noun + suff.	md	cstr.	gen., acc.	1cd
ydkm	/yadā-kumā/	‘your hands’	noun + suff.	md	cstr.	nom.	2cd
ydkm	/yadê-kumā/	‘of your hands’	noun + suff.	md	cstr.	gen., acc.	2cd
ydhm	/yadā-humā/	‘their hands’	noun + suff.	md	cstr.	nom.	3cd
ydhm	/yadê-humā/	‘of their hands’	noun + suff.	md	cstr.	gen., acc.	3cd
ydn	/yadā-nā/	‘our hands’	noun + suff.	md	cstr.	nom.	1cp
ydn	/yadê-nā/	‘of our hands’	noun + suff.	md	cstr.	gen., acc.	1cp
ydkm	/yadā-kum(ū)/	‘your hands’	noun + suff.	md	cstr.	nom.	2mp
ydkm	/yadê-kum(ū)/	‘of your hands’	noun + suff.	md	cstr.	gen., acc.	2mp
ydkn	/yadā-kin(ā)/, /yadā-kin(na)/(?)	‘your hands’	noun + suff.	md	cstr.	nom.	2fp
ydkn	/yadê-kin(ā)/, /yadê-kin(na)/(?)	‘of your hands’	noun + suff.	md	cstr.	gen., acc.	2fp
ydhm	/yadā-hum(ū)/	‘their hands’	noun + suff.	md	cstr.	nom.	3mp
ydhm	/yadê-hum(ū)/	‘of their hands’	noun + suff.	md	cstr.	gen., acc.	3mp
ydhn	/yadā-hin(ā)/, /yadā-hin(na)/(?)	‘their hands’	noun + suff.	md	cstr.	nom.	3fp
ydhn	/yadê-hin(ā)/, /yadê-hin(na)/(?)	‘of their hands’	noun + suff.	md	cstr.	gen., acc.	3fp
špty	/šapatā-ya/	‘my lips’ 	noun + suff.	fd	cstr.	nom.	1cs
špty	/šapatê-ya/	‘of my lips’	noun + suff.	fd	cstr.	gen., acc.	1cs
šptk	/šapatā-kā̆/	‘your lips’	noun + suff.	fd	cstr.	nom.	2ms
šptk	/šapatê-kā̆/	‘of your lips’	noun + suff.	fd	cstr.	gen., acc.	2ms
šptk	/šapatā-kī̆/	‘your lips’	noun + suff.	fd	cstr.	nom.	2fs
šptk	/šapatê-kī̆/	‘of your lips’	noun + suff.	fd	cstr.	gen., acc.	2fs
špth	/šapatā-hū̆/	‘his lips’	noun + suff.	fd	cstr.	nom.	3ms
špth	/šapatê-hū̆/	‘of his lips’	noun + suff.	fd	cstr.	gen., acc.	3ms
špth	/šapatā-hā/	‘her lips’	noun + suff.	fd	cstr.	nom.	3fs
špth	/šapatê-hā/	‘of her lips’	noun + suff.	fd	cstr.	gen., acc.	3fs
šptny	/šapatā-nāyā/(?)	‘our lips’	noun + suff.	fd	cstr.	nom.	1cd
šptny	/šapatê-nāyā/(?)	‘of our lips’	noun + suff.	fd	cstr.	gen., acc.	1cd
šptkm	/šapatā-kumā/	‘your lips’	noun + suff.	fd	cstr.	nom.	2cd
šptkm	/šapatê-kumā/	‘of your lips’	noun + suff.	fd	cstr.	gen., acc.	2cd
špthm	/šapatā-humā/	‘their lips’	noun + suff.	fd	cstr.	nom.	3cd
špthm	/šapatê-humā/	‘of their lips’	noun + suff.	fd	cstr.	gen., acc.	3cd
šptn	/šapatā-nā/	‘our lips’	noun + suff.	fd	cstr.	nom.	1cp
šptn	/šapatê-nā/	‘of our lips’	noun + suff.	fd	cstr.	gen., acc.	1cp
šptkm	/šapatā-kum(ū)/	‘your lips’	noun + suff.	fd	cstr.	nom.	2mp
šptkm	/šapatê-kum(ū)/	‘of your lips’	noun + suff.	fd	cstr.	gen., acc.	2mp
šptkn	/šapatā-kin(ā)/, /šapatā-kin(na)/(?)	‘your lips’	noun + suff.	fd	cstr.	nom.	2fp
šptkn	/šapatê-kin(ā)/, /šapatê-kin(na)/(?)	‘of your lips’	noun + suff.	fd	cstr.	gen., acc.	2fp
špthm	/šapatā-hum(ū)/	‘their lips’	noun + suff.	fd	cstr.	nom.	3mp
špthm	/šapatê-hum(ū)/	‘of their lips’	noun + suff.	fd	cstr.	gen., acc.	3mp
špthn	/šapatā-hin(ā)/, /šapatā-hin(na)/(?)	‘their lips’	noun + suff.	fd	cstr.	nom.	3fp
špthn	/šapatê-hin(ā)/, /šapatê-hin(na)/(?)	‘of their lips’	noun + suff.	fd	cstr.	gen., acc.	3fp
"""

paradigm_cardinal_numbers = """
translit	transcript	gloss	pos	gender	case
ảḥd	/ˀaḥ(ḥ)adu/	1, ‘one’	card. num.	m.	nom., gen., acc.
ṯn	/ṯinā/	2, ‘two’	card. num.	m., f.	nom.
ṯn	/ṯinê/	2, ‘two’	card. num.	m., f.	gen., acc.
ṯlṯ	/ṯalāṯu/	3, ‘three’	card. num.	m., f.	nom., gen., acc.
ảrbˁ	/ˀarbaˁu/	4, ‘four’	card. num.	m., f.	nom., gen., acc.
ḫmš	/ḫam(i)šu/	5, ‘five’	card. num.	m., f.	nom., gen., acc.
ṯṯ	/ṯiṯṯu/	6, ‘six’	card. num.	m., f.	nom., gen., acc.
šbˁ	/šabˁu/	7, ‘seven’	card. num.	m., f.	nom., gen., acc.
ṯmn	/ṯamānû/	8, ‘eight’	card. num.	m., f.	nom., gen., acc.
tšˁ	/tišˁu/	9, ‘nine’	card. num.	m., f.	nom., gen., acc.
ˁšr	/ˁaš(a)ru/	10, ‘ten’	card. num.	m., f.	nom., gen., acc.
ảḥt	/ˀaḥ(ḥ)attu/	1, ‘one’	card. num.	f.	nom., gen., acc.
ṯt	/ṯittā/	2, ‘two’	card. num.	f.	nom.
ṯt	/ṯittê/	2, ‘two’	card. num.	f.	gen., acc.
ṯlṯt	/ṯalāṯatu/	3, ‘three’	card. num.	m.	nom., gen., acc.
ảrbˁt	/ˀarbaˁ(a)tu/	4, ‘four’	card. num.	m.	nom., gen., acc.
ḫmšt	/ḫam(i)š(a)tu/	5, ‘five’	card. num.	m.	nom., gen., acc.
ṯṯt	/ṯiṯṯatu/	6, ‘six’	card. num.	m.	nom., gen., acc.
šbˁt	/šabˁatu/	7, ‘seven’	card. num.	m.	nom., gen., acc.
ṯmnt	/ṯamānītû/	8, ‘eight’	card. num.	m.	nom., gen., acc.
*tšˁt	/tišˁatu/	9, ‘nine’	card. num.	m.	nom., gen., acc.
ˁšrt	/ˁašartu/	10, ‘ten’	card. num.	m.	nom., gen., acc.
ˁšrm	/ˁišrāmi/, /ˁišrūma/	20, ‘twenty’	card. num.	m., f.	nom., gen., acc.
ṯlṯm	/ṯalāṯuma/	30, ‘thirty’	card. num.	m., f.	nom., gen., acc.
ảrbˁm	/ˀarbaˁūma/	40, ‘forty’	card. num.	m., f.	nom., gen., acc.
ḫmšm	/ḫam(i)šūma/	50, ‘fifty’	card. num.	m., f.	nom., gen., acc.
ṯṯm	/ṯiṯṯūma/	60, ‘sixty’	card. num.	m., f.	nom., gen., acc.
šbˁm	/šabˁūma/	70, ‘seventy’	card. num.	m., f.	nom., gen., acc.
ṯmnym	/ṯamānīyūma/	80, ‘eighty’	card. num.	m., f.	nom., gen., acc.
tšˁm	/tišˁūma/	90, ‘ninety’	card. num.	m., f.	nom., gen., acc.
"""

strong_consonants = "bgdzṭkšlmḏnẓspṣqrṯġtөś"
weak_consonants = "ảỉủʔʕḥḫʾʿˀˁwy"


# To check for strong root use the following regexp: ``r"/[^ʔʕyhwḥḫ]-[^ʔʕyhwḥḫ]-[^ʔʕyhwḥḫ]/"``.
def is_strong_verb_root(root: str) -> bool:
    import re

    pattern = rf"^[{strong_consonants}][{strong_consonants}][{strong_consonants}]$"
    return re.match(pattern, root) is not None


def get_verb_paradigm(
    lemma: str, stem: Stem = Stem.QATUL, verbal_stem: VerbalStem = VerbalStem.G
) -> dict:
    """
    Generate a paradigm table for a given verb. Lemma is expected in the form 'ktb' (three consonants) or 'nš' (two consonants).
    """
    from ug_nlp.verb_paradigm import VerbParadigmGenerator

    return VerbParadigmGenerator(lemma, stem=stem, verbal_stem=verbal_stem).generate()
