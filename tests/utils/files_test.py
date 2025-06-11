"""
Running the script creates line-by-line transcriptions of the original word files.
Make sure the word files are in a folder named "/files/".
"""
import os
from natsort import os_sorted
import re
import docx

CHARACTERS = {'a','b','d','ḏ','g','ġ','h','ḥ','ḫ','i','k','l','m','n','p','q','r','s','ṣ','š','ś','ṯ','ṭ','t','u','w','y',
              'z','ẓ','ʿ','x','.',' ','\xa0','-','[',']','{','}','<','>','(',')','/','\\','?','\n','…'}

side = r'le\.e\.|low\.e\.|obv\.|r\.e\.|rev\.|up\.e\.'

LATIN_NUMBERS = {
'I':1,
'II':2,
'III':3,
'IV':4,
'V':5,
'VI':6,
'VII':7,
'VIII':8,
'IX':9,
'X':10,
}

class TextTranscriber:
    """
    Makes a transcription of original word files line by line
    """

    def __init__(self, WORD_FILES_FOLDER):
        self.word_files = [f for f in os_sorted(os.listdir(WORD_FILES_FOLDER)) if f.lower().endswith('.docx') or f.lower().endswith('.doc') and not f.startswith('~$')]
        
        for file in self.word_files:
            path = os.path.join(WORD_FILES_FOLDER, file)
            self.word_doc = docx.Document(path)
            run_test = self.test(file)
            if run_test:
                print(run_test)
                break
            else:
                print(f"{self.corpus}: SUCCESS")
        
    def test(self, filename):
        '''
        Testing each sign of each line against accepted characters.
        '''
        col_nu = 0
        line_nu = 0
        for para in self.word_doc.paragraphs:

            if re.match('KTU', para.text):
                self.corpus = para.text.rstrip()
                if self.corpus != filename[:filename.index('_')]:
                    return f'{filename}: Corpus name does not match file name'

            elif re.fullmatch('[LXVI]+', para.text.strip()):
                column = para.text.strip()
                col_nu+=1
                line_nu = 1
                if col_nu != LATIN_NUMBERS[column]: #Check if all columns are included in the right order
                    return f'Unexpected column number in {self.corpus}: {para.text}. Expected column number: {col_nu}'

            elif re.match(rf'({side})', para.text):
                continue

            elif para.text == '...' or para.text == '. . .':
                return f'Unexpected ... in {self.corpus} {column}: {para.text}     Probable solution: Replace ... with …'

            elif re.match('^…', para.text):
                continue

            elif re.match('^-', para.text):
                continue

            elif not para.text:
                continue

            elif re.match(r'^\d+', para.text):
                line = int(re.match(r'^\d+', para.text).group())
                text = re.sub(r'^\d+', '', para.text).lstrip()

                if not col_nu:
                    return f'Missing column number in {self.corpus}'

                if line != line_nu:
                    return f'Unexpected line number in {self.corpus} {column} {line}'
                
                for sign in text:
                    if sign not in CHARACTERS:
                        if ord(sign) == 9:
                                probable_error = 'Probable solution: replace tab with white spaces'
                        elif ord(sign) in {49,73}:
                                probable_error = 'Probable solution: replace 1 (number) with l (letter)'
                        elif ord(sign) == 705:
                                probable_error = 'Probable solution: replace ˁ with ʿ'
                        elif ord(sign) == 740:
                                probable_error = 'Probable solution: replace ˤ with ʿ'
                        elif ord(sign) == 769:
                                probable_error = 'Probable solution: replace some letter with a diagonal line above it, probably ś'
                        elif ord(sign) == 775:
                                probable_error = 'Probable solution: replace some letter with a dot above it'
                        elif ord(sign) == 780:
                                probable_error = 'Probable solution: replace some letter with a ̌ above it, probably š'
                        elif ord(sign) == 800:
                                probable_error = 'Probable solution: replace some letter with a macron (line) below it'
                        elif ord(sign) == 803:
                                probable_error = 'Probable solution: replace some letter with a dot below it'
                        else:
                                probable_error = ord(sign)
                        return f'Illegal character in {self.corpus} {column} {line}: {sign} {probable_error}'

                if text.count('[') != text.count(']'):
                    return f'[ does not match ] in {self.corpus} {column} {line}'

                if text.count('{') != text.count('}'):
                    return r'\{ does not match \} in {self.corpus} {column} {line}'

                if text.count('<') != text.count('>'):
                    return f'< does not match > in {self.corpus} {column} {line}'

                if text.count('(') != text.count(')'):
                    return f'( does not match ) in {self.corpus} {column} {line}'
                line_nu += 1

            else:
                ERROR_RESPONSE = f'Unexpected (initial?) sign in {self.corpus}'
                if col_nu != 0:
                     ERROR_RESPONSE += f' {column}'
                if line_nu:
                     ERROR_RESPONSE += f' {str(line_nu)}'
                if para.text[0] == '\\':
                     ERROR_RESPONSE += '     Solution: Move to the end of preceding line'
                return f'{ERROR_RESPONSE}: {para.text}'
     
WORD_FILES_FOLDER = './files'
        
if __name__ == '__main__':

    line_transcriptions = TextTranscriber(WORD_FILES_FOLDER)