"""
This test will not run on github, because it needs data that are not in the github repo.
Tests whether the text in TF is the same as a transcription of the original word files.
"""
import logging
import os
import pytest
import re

from utils import make_transcriptions

from tf.fabric import Fabric

#ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = 'C:/Users/Christian/github/DT-UCPH/cuc'
TF_FOLDER = 'tf'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype g_cons trailer alt
''')
api.loadLog()
api.makeAvailableIn(globals())

F, L, T = api.F, api.L, api.T

WORD_FILES_FOLDER = './utils/files'

CORPORA = [F.corpus.v(n) for n in F.otype.s('corpus')]
WORD_FILES = [f for f in os.listdir(WORD_FILES_FOLDER) if f.lower().endswith('.docx') or f.lower().endswith('.doc')]

logging.basicConfig(
    filename='./logs/test_cuc_texts.log',
    level = logging.INFO,
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s')

def get_line_transcriptions():
    """Make dict with transcription of each verse"""
    transcriber = make_transcriptions.TextTranscriber(WORD_FILES, WORD_FILES_FOLDER)
    text_dict = transcriber.line_texts
    logging.info(f'The word files contain {len(text_dict)} lines.')
    return text_dict

@pytest.fixture(scope='module')
def verse_transcriptions(module):
    yield get_line_transcriptions()
    
def test_cuc_text(line_transcriptions):
    try:
        idx = 0
        corpus_set = set()
        for l in F.otype.s('line'):
            line_text = ''
            for w in L.d(l, 'word'):
                word = ''
                for s in L.d(w, 'sign'):
                    if F.alt.v(s): word += f'{F.sign.v(s)}{F.alt.v(s)}'
                    else: word += F.sign.v(s)
                line_text += word+F.trailer.v(w)
            line_text = re.sub('[ \xa0]', '',line_text)
            corpus, column, line = T.sectionFromNode(l)
            if corpus not in corpus_set:
                logging.info(f'Testing {corpus}')
                corpus_set.add(corpus)
            line_transcription = re.sub('[\[\]\{\}\/\<\>\(\)\\\ \xa0]','',line_transcriptions[(corpus, column, line)])
            assert line_transcription == line_text
            idx += 1
        logging.info('Testing test_cuc_texts: SUCCES')
        logging.info(f'Tested {idx} lines')
    except AssertionError as err:
        logging.error(f'Testing texts of CUC corpora, transcription not equal to TF data in {corpus} {column} line {line}')
        logging.error(f'Word transcription: {line_transcription}')
        logging.error(f'TF transcription: {line_text}')
        
if __name__ == '__main__':

    line_transcriptions = get_line_transcriptions()
    test_cuc_text(line_transcriptions)