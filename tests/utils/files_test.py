"""
Running the script creates line-by-line transcriptions of the original word files.
Make sure the word files are in a folder named "/files/".
"""
import os
import re
import docx

CHARACTERS = {'a','b','d','ḏ','g','ġ','h','ḥ','ḫ','i','k','l','m','n','p','q','r','s','ṣ','š','ṯ','ṭ','t','u','w','y',
              'z','ẓ','ʿ','x','.',' ','\xa0','-','…','[',']','{','}','<','>','(',')','/','\\'}

class TextTranscriber:
    """
    Makes a transcription of original word files line by line
    """

    def __init__(self, WORD_FILES_FOLDER):
        self.word_files = [f for f in os.listdir(WORD_FILES_FOLDER) if f.lower().endswith('.docx') or f.lower().endswith('.doc')]
        
        for file in self.word_files:
            path = os.path.join(WORD_FILES_FOLDER, file)
            self.word_doc = docx.Document(path)
            run_test = self.test()
            if run_test:
                print(run_test)
                break
            else:
                print(f"{self.corpus}: SUCCESS")
                
        
    def test(self):
        '''
        Testing each sign of each line against accepted characters.
        '''
        for para in self.word_doc.paragraphs:
            if re.match('KTU', para.text):
                self.corpus = para.text
                continue
                
            if re.match(r'(rev. )?[LXVI+]', para.text):
                column = para.text.lstrip('rev.').lstrip()
                continue

            if re.match('^\d+', para.text):
                line = int(re.match('^\d+', para.text).group())
                text = re.sub('^\d+', '', para.text).lstrip()
                
                for sign in text:
                    if sign not in CHARACTERS:
                        return f'Illegal character in {self.corpus} {column} {line}: {sign}'
                
WORD_FILES_FOLDER = './files'
        
if __name__ == '__main__':

    line_transcriptions = TextTranscriber(WORD_FILES_FOLDER)