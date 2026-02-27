## How to correct the preparsed data.

### Where
The folder "auto_parsing" contains preprocessed files with predictions for the morphology made with the help of an LLM. Within the folder auto_parsing you find a folder of which the name is the tf data version. In the data version folder you find the preprocessed data files. Each file contains the text of one tablet.
After you have finished the corrections, move the data to the folder "reviewed".

### What
In a file, you will find the words with parsing. Some lines contain the line number on a tablet
You find information about one word on a line. The file contains the following columns:

id: identifier of the word in the Text-Fabric dataset.	
surface form: consonantal transcription of the word.
morphological parsing: proposed morphological parsing, there can be multiple options. 
DULAT: proposed DULAT lemma. 
POS: part of speech based on DULAT. 
gloss: gloss based on DULAT
comments: Comments indicating that a word was not found in DULAT.

If there are multiple proposed morphologies, each alternative is on a separate line. There is no guarantee that at least one is correct.

### Making corrections
If there is one proposed morphology for a word and you agree, leave it as it is.
If there is one proposed morphology for a word and you disagree, correct it. Use the information from DULAT as much as possible. It is our present standard, which does not mean that we cannot deviate from it.
If there are multiple proposed morphologies and you agree with none of them, make a line with the correct morphology and remove the wrong morphologies.
If there are multiple proposed morphologies and you agree with one, remove the others.
If there are multiple proposed morphologies and you agree with more than, Leave the correct morphologies in the file, remove the others.

### How to save the work

1. Get the latest version of the main branch (git pull).
2. Make a new branch with a recognizable name, e.g. your name and the tablet number. Make one new branch for one file that you work on.
3. Make corrections in the file you want to correct.
4. If you do not finish the whole file at once, make sure you push the changes in the new branch to Github after the session.
5. When you are done with the file, move it to the folder "reviewed".
6. Merge it with the main branch and make a pull request.
7. The reviewer will review the work and approve or make comments.