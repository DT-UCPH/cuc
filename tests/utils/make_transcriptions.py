"""
Running the script creates line-by-line transcriptions of the original word files.
Make sure the word files are in the folder utils/files.
"""
import os
import re
import docx

class TextTranscriber:
    """
    Makes a transcription of original word files line by line
    """

    def __init__(self, word_file_names, word_files_folder):
        self.word_file_names = word_file_names
        self.word_files_folder = word_files_folder
        self.line_texts = {}
        
        for word_file_name in self.word_file_names:
            path = os.path.join(self.word_files_folder, word_file_name)
            self.word_doc = docx.Document(path)
            self.read()
        
    def read(self):
        for para in self.word_doc.paragraphs:
            if re.match('KTU', para.text):
                self.corpus = para.text
            elif re.match(r'(rev. )?[LXVI+]', para.text):
                self.column = para.text.lstrip('rev.').lstrip()
            elif re.match('\.\.\.', para.text):
                    continue
            elif re.match('^\d+', para.text):
                self.line = int(re.match('^\d+', para.text).group())
                self.text = re.sub('^\d+', '', para.text).lstrip()
                
                self.line_texts[(self.corpus, self.column, self.line)] = self.text