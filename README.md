<img src="images/caccht-logo.png" alt="CACCHT logo" height="200">

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10695308.svg)](https://doi.org/10.5281/zenodo.10695308)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

# Copenhagen Ugaritic Corpus

This repo contains a text fabric dataset of the Ugaritic text corpus. It is work in progress.

### The CACCHT project: Creating Annotated Corpora of Classical Hebrew Texts
This dataset is developed as part of the [CACCHT project](https://github.com/CACCHT), which is a collaboration of Christian Canu Højgaard, Martijn Naaijer, Martin Ehrensvärd, Robert Rezetko, Oliver Glanz, and Willem van Peursen. The goal of CACCHT is to prepare and publish ancient Semitic texts digitally, that can be used for research.

For this dataset, we cooperate with Tania Notarius (University of the Free State), Alex Sosnovshchenko and Kseniia Yerofeieva.
Other contributors are Maria Simion, Lynn Strietzel, Ben Shields and Elijah Labowe-Stoll, volunteer assistants (Polis - the Jerusalem Institute of Language and Humanities).

### Data
The dataset contains 453 texts.

363 tablets of *Die keilalphabetischen Texte aus Ugarit, Ras Ibn Hani und anderen Orten* (KTU, 3rd edition, 2013):

- KTU 1.1-1.7
- KTU 1.9-1.33
- KTU 1.38-1.43
- KTU 1.45-1.51
- KTU 1.54-1.58
- KTU 1.61-1.63
- KTU 1.65-1.69
- KTU 1.71-1.98
- KTU 1.100-1.109
- KTU 1.111-1.119
- KTU 1.121-1.122
- KTU 1.124-1.127
- KTU 1.129-1.130
- KTU 1.132-1.144
- KTU 1.146-1.156
- KTU 1.158-1.177
- KTU 1.179-1.180
- KTU 2.1-2.18
- KTU 2.20-2.27
- KTU 2.30-2.44
- KTU 2.46-2.75
- KTU 2.77-2.80
- KTU 2.82-2.113
- KTU 3.1-3.35
- KTU 4.1-4.13
- KTU 4.15-4.17
- KTU 4.19-4.25
- KTU 4.27-4.51
- KTU 4.53-4.58
- KTU 4.60-4.62
- KTU 4.140
- KTU 4.185
- KTU 5.24
- KTU 5.27
- KTU 7.191

KTU 1.8, 1.99 and 2.19 are not separate tablets in KTU³: their text is now part of KTU 1.3 VI 1-17, KTU 1.98 and KTU 3.12. The corpus keeps the old numbers as references to those texts.

90 texts of *Ras Ibn Hani II. Les textes en écritures cunéiformes de l'âge du Bronze récent* (P. Bordreuil, D. Pardee and C. Roche-Hawley, BAH 214, 2019), by their number in that edition:

- RIH II 3, 5, 8, 12-18, 20-24, 26, 28, 30, 32-34, 36, 38-40, 44, 46-47, 50, 52, 56, 59, 64-68, 70-71, 73-81, 103-105, 107, 109-113, 116-121, 123-126, 128-132, 135-138, 140-153

Most Ras Ibn Hani texts also have a KTU number (KTU 8.31, 8.32 and 9.439-9.528). They can be found by either number.

The texts are annotated with the following features:

- tablet: tablet title (KTU number, or RIH number for a Ras Ibn Hani text without one)
- rih, ktu: the Ras Ibn Hani and KTU numbers of a Ras Ibn Hani text
- tablet@rih: the same tablet titles, with Ras Ibn Hani texts named by their RIH number, for looking them up by it
- column: column number or fragment
- line_label: line number as printed
- line: line number as an integer
- surface: tablet surface of the inscription (obverse, reverse, edges)
- surface_cert: the editor's certainty about the surface attribution
- g_cons: a consonantal representation of each word in Latin script
- trailer: a representation of word spacing or word dividers
- language: language of the word (Ugaritic, Hurrian or Akkadian)
- tablet_language: language of the tablet as a whole
- sign: letter in Latin script
- sign_source: the original spelling where a letter is normalised (the short alphabet of KTU 4.31)
- usign: letter in Ugaritic script
- emen: emendations of various sorts in relation to a sign (including reconstructed, missing, excised, or redundant signs/letters)
- cert: the editor's confidence in the reading, including restored or supplied readings
- cont: marking of line continuation in between lines
- alt: alternative reading
- boundary: breaks and scribal rulings between lines

Notes on each release are in the [docs](docs/) folder.
