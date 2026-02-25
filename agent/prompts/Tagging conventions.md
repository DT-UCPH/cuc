# Tagging conventions

At this stage we decided not to reconstruct consonants, doubling, vowels and other grammatical markings that do not appear on the surface and concentrate on the visible elements. Altogether, if a sign is part of a lexeme, but it does not appear in a word, it is added to the word by "(". If a sign occurs in a word but it does not occur in the lexeme in DULAT, it is preceded by "&". E.g., in case of a scribal error corrected by editors, the ‘(’ precedes the ‘&’, as in wsp - (k&wsp “silver”. Otherwise, at this stage we don't reconstruct missing signs.

Important: when several consecutive letters are reconstructed, each letter must be marked separately with "(".

The signs ( and & are also can also be used for aleph letters (u, i, a).
Comments about variants can be added after  #

## Lexical tagging

Always check a word in DULAT for the lexeme. Are there homographs? DULAT adds roman numerals in parentheses to a lexeme for disambiguation. For now, we use this convention as well. This rule applies also to the homographic particles, e.g. -h(I) pron "his/her" -h(II) adverb.
If aleph letters are part of the nominal root and do not show different variants of vocalization, they are not further parsed. In verbal roots aleph ʔ should be visible, because we follow the lexicon DULAT. E.g. the verb š-ʔ-b has the surface form šibt, we encode as š(ʔ&ib[/t= "those (fpl) who draw water".

## Check also the part of speech

* lexemes of nouns and adjectives end on "/".
* lexemes of verbs end on "[".
* If a form is deverbal noun (as infinitive or participle), the order is [/.
* Prepositions, particles, pronouns are without a special sign at the end.

E.g.: Suppose in a text you find the word "il", meaning "God". DULAT adds "(I)" to it. This means that we encode the word as: il(I)/.

## Suffixes and enclitics

Pronominal suffixes are prefixed with "+": mlk/+h "his king"
~ appears before the postclitic consonants: !y!rgm[~n "he says"
If feminine ending -t  of nouns (both sing or plur) is part of the lexeme, we leave it unmarked  at this stage. A noun that appears without the feminine -t in singular, but with -t in plural, e.g. gg, is tagged: gg/t= “roofs”. 

For pluralia tantum, keep plural ending explicit in analysis and mark POS with `pl. tant.`/`pl. tant.?` (e.g. hml(t/t=; nš(m/m). 

But adjectives and participles tag feminine ending -t, e.g. mru "fattened: 
```
f.s. mr(u&a/t
f. pl. mr(u&a/t=
```

In III-ˀ nouns aleph letters show case endings, e.g. ksu "seat: 
```
nominative ks(u/&u
genitive ks(u/&i
accusative ks(u/&a
```
or plural of rpu "Rafa": 
```
rp(u&/m, 
rp(u&i/m
```

## Prefixes and infixes

Verbal preformatives of the prefix conjugation are between !!, e.g. tqtl -> !t!qtl[.
Augment that indicates the verbal stem are between ]]. E.g. a verb with a prefixed š (š-stem), looks like this: šqtl -> ]š]qtl[.
An infinitive is encoded as !!qtl[/.
An active participle is encoded as qtl[/.

# The CUC encoding paradigm

## General


Always check a word in DULAT for the lexeme. Are there homographs? DULAT adds roman numerals in parentheses to a lexeme for disambiguation. For now, we use this convention as well. Check also the part of speech. This rule applies also to the homographic particles, e.g. -h(I) pron "his/her" -h(II) adverb

lexemes of nouns, adjectives, and numerals end on "/".
lexemes of verbs end on "[".
If a form is deverbal noun (as infinitive or participle), the order is [/.

## Disambiguation

Suppose in a text you find the word "il", meaning "God". DULAT adds "(I)" to it. This means that we encode the word as: il(I)/.

An opening parenthesis ‘(’ marks a letter not present in the realized form
and an ampersand ‘&’ marks a letter not present in the paradigmatic (lexical) form.
In case of a scribal error corrected by editors, the ‘(’ precedes the ‘&’, as in wsp - (k&wsp “silver”.

Pronominal suffixes are prefixed with "+".
The post-clitic particles are prefixed with "~".

## NOUNS

Feminine nouns ending on -t.
In feminine nouns of which the lexeme ends on -t, the t is a nominal ending, and therefore needs to appear after the /. However, it is also part of the lexeme, so before the / it appears as (t, like this:
am(t/t (I) for the lexeme amt (I) "female slave". This is similar to >WL(T/T אִוֶּלֶת "foolishness" in Proverbs 12:23 in the ETCBC dataset of the MT. 
The plural of feminine words ending on -t is am(t/t=. -t= is the feminine plural marker.
A noun that appears without the feminine -t in singular, but has it in plural gg, gg/t= "roof". 

In pluralia tantum, keep this split ending explicit and mark POS as `pl. tant.`/`pl. tant.?`.

Adjectives and participles, e.g. dl "poor". The feminine singular form is dl/t and the feminine plural is dl/t=.

Ugaritic corpus is different from the Biblical Hebrew or Syriac corpora, as it has no traditional vocalization, the alphabetic script is basically consonantal. Needless to say, the lack of vowels creates an additional difficulty for the grammatical tagging and disambiguation. However, Ugaritic has three aleph letters that partly report about the vocalization of the forms.  If aleph letters do not show different variants of vocalization of nominal forms, they are not further parsed. Some cases, involving three aleph letters, require special attention:


### III-ˀ nouns

Case endings of nouns with aleph as final consonant, without feminine ending -t:
ksu "seat" and other final-aleph nouns ṣbu "army", iqnu "lapiz lazuli", llu "baby" etc.


have 3 forms in singualar, processed as follows:

```
ks(u/&u nominative
ks(u/&i genitive
ks(u/&a accusative
```

u, i and a are inflectional ending, and are placed after the "/". However, we put an ampersand in front of it, because a word only has this ending if it ends with aleph.

Plural forms without feminine ending will have two vocalizations: pl. rpủm, rpỉm
Final aleph nouns with feminine ending t do not have these variations, as the case ending was added after the t ending.

### (2) II-ˀ nominal forms

Some nouns, with or without feminine ending, can have different vocalic patterns in singular and plural and the aleph-sign will show it. E.g. pit "boundary"

```
pit singular /piˀtu/
pat plural /piˀātu/
```

`pit` is our paradigmatic lexical form in singular, but if it occurs in the plural, its vocalization changes, and we encode it with:
```
p(i&a(t/t=
```

### (3) Prosthetic aleph

A very special case of aleph that is added in the plural of a noun, namely a prostetic aleph: dmʿ "tear". In the plural, it has a prefixed “u”. The same aleph occurs as well in imperative forms (see below), and its function is to break the initial cluster of consonants. In the encoding, we treat it as a prefix, e.g.:


udmʿth !(ʔ&u!dmʿ(t/t+h ”his tears” (TODO: maybe think about other marker than !! for the prefix, because this is used for verbal prefixes.:


## Pronominal suffixes

We use the following conventions to parse and disambiguate pronominal suffixes:

```
Singular
1cs	+y
	+n=
	+ny
2ms	+k
	+nk
2fs	+k=
3ms	+h
	+nh
	+nn
3fs	+h=
	+nh=

Dual
1cd	+ny=
2cd	+km=
3cd	+hm=

Plural
1cp	+n
2mp	+km
	+nkm
2fp	+kn
3mp	+hm
3fp	+hn
```

## VERBS

Verbs with a double middle radical have ":d" at the end of the word. Stems with reduplications are notified :l (pālil) and :r (pilpil).
Verbs of internal passive stems are not fully vocalized but have :pass at the end of the word.

Consonants that indicate the verbal stem are between ]]. E.g. a verb with a prefixed š (š-stem), looks like this: šqtl -> ]š]qtl[.
Verbal preformatives of the prefixkonjugation are between !!, e.g. tqtl -> !t!qtl[.

The assimilated letter n, either of the root or the N-stem, is added by means of ( .

Some difficult cases, especially those that involve aleph letters:

In verbs with aleph in the root, the ʔ should be visible, because we follow the lexicon DULAT, which uses "ʔ" in verbs. E.g., the G participle feminine plural of š-ʔ-b has the surface text šibt. We encode it as š(ʔ&ib[/t= "those (f,) who draw water". It consists of the following parts:

* š the first radical
* (ʔ the second radical, not realized in the realized text.
* &i the vowel after the ʔ, which is realized in the give text but is not found in the lexeme.  
* b the third radical
* [ the end of the verbal root. After "[" follows the verbal ending, which is empty here.
* / the marker of the nominal ending
* t= the nominal ending t= marks the feminine plural form.

If the verb is of I or II-aleph root, firstly aleph is added by (, and then the vocalization is added by &:
```
!yrš[ "he desires"; !t!(]n](ʔ&adm[ "she blushed" (in the N-stem)
š(ʔ&ib[/t= "(they, fem) water-drawers" (active participle).
```

But if the verb is III-aleph root, the aleph is added by (, [ marks the end of the root, and then the vocalization is added by &, because the verb has a verbal inflectional ending:
```
!!(nš(ʔ[&a "raise!" (lengthened imperative)
!y!(nš(ʔ[&u
```

For aleph as a prefix, the vocalization is marked as follows:
```
!(ʔ&a!šlw[ "I will be in peace"
```
Forms with * need further disambiguation

## SUFFIX CONJUGATION

Various plural verb forms ended on a vowel “u”. In Biblical Hebrew, this happens as well, and there the vowel is indicated with the final vowel letter ו. In Ugaritic, this final vowel letter is never written. To indicate that a verb is in the plural we add “:w” in these cases where there is no other visible indication that a verb is in the plural.

```
Singular			Plural				Dual
3m qtl[			3m qtl[:w	*		3m qtl[*
3f qtl[t===		3f qtl[*			3f qtl[t*
2m qtl[t=			2m qtl[tm			2m qtl[tm=
2f qtl[t==			2f qtl[tn			2f qtl[tm==
1c qtl[t			1c qtl[n or qtl[*	1c qtl[n= or qtl[y
```

## PREFIX CONJUGATION

```
Singular			Plural			Dual
3m !y!qtl[			3m !t!qtl[:w	3m !y=!qtl[ or !t!qtl[
3f !t!qtl[			3f !t!qtl[n	3f !t!qtl[*
2m !t=!qtl[		2m !t===!qtl[	2m !t!qtl[*
2f !t==!qtl[		2f !t!qtl[n=	2f !t!qtl[*
1c !(ʔ$a!qtl[		1c !n!qtl[

Infinitive
!!qtl[/

Active participle 
qtl[/
```



## ENCLITIC PARTICLES

The enclitic particles are prefixed with “~” in the encoding.

### Energic nun

Energic nun is a mysterious enclitic particle in the Ugaritic language. It can occur as single or double nun:
```
~n
~nn
```

A special case of energic nun is when it incorporates a pronominal suffix with a fusion. In this case, we use a combination of ~ and +. E.g.:

```
85856 tluan !t!l(ʔ&u(y(I)[~+(n&an #an is a variant of nn
```

### Directive h

Directive h ("adverbial -h (II)") is encoded as ~h.

## VARIANTS

Sometimes we could not disambiguate the consonantal spelling even on the level of lexemes or to give preference to one of the interpretations. In such cases both readings are preserved, 9878-9880:

```
ḥšk	!!ḥš(I)[/+k # with Smith Pitard, or !!ḥšk[ with DULAT
ˤṣk	!!ˤṣ[/+k # with Smith Pitard, or ˤṣ/+k with DULAT
ˤbṣk	!!ˤbṣ[/+k # with Smith Pitard, or ˤbṣ/+k with DULAT
```
