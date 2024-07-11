from sqlite3 import complete_statement
from docx import Document
import os
import os.path
import string
import glob 
import sys

# Definování vstupního a výstupního adresáře
input_dir = "input"
output_dir = "./output"

# Funkce pro zpracování souboru
def translate(filename, without_short=False):
    print(filename)
    document =  Document(filename)
    
    # Inicializace seznamů pro různé části textu
    cloze_text = []        # Text s vynechanými částmi
    first_task = []        # První úloha
    second_task = []       # Druhá úloha
    completed_text = []    # Kompletní text
    questions = []         # Otázky
    state = 0              # Stavový ukazatel
    second_task_text = ""  
    second_task_words = [] 
    
    add_source = 0         # Příznak pro přidání zdroje

    for par in document.paragraphs:
        if len(par.text) == 0 or par.text == "\n":
                continue

        if (state == 0):
            # Zpracování textu před první úlohou
            if  (par.text[0:7].lower() == "source:") :
                continue
            if (len(par.text) == 1):
                continue
            if (state == 0) and ("Five clauses/sentences have been removed from the text." in par.text):
                state = state + 1
                first_task.append(par.text)
                continue     
            cloze_text.append(par.text)
        elif (state == 1) : 
            # Zpracování první úlohy            
            first_task.append(par.text)
            if ("answers" in par.text.lower()):
                state = state + 1 
                if without_short:
                    state = state + 1
        elif (state == 2) :
            # Zpracování druhé úlohy             
            second_task.append(par.text)
            if ("answers" in par.text.lower()):
                state = state + 1         
        elif (state == 3) : 
            # Zpracování kompletního textu            
            if (len(par.text) == 1):
                continue
            completed_text.append(par.text)
            if (par.text[0:7].lower() == "source:"):
                add_source = 1 
            if par.text.strip() == "Here is the text without gaps.":
                add_source = add_source+1
            if (len(completed_text) == len(cloze_text)+add_source):
                state = state + 1 
        elif(state == 4):
            # Zpracování otázek
            questions.append(par.text)
            
    print(80*"#")

    for i, row in enumerate(cloze_text):
        print(i, len(row), row, row == " ")


    print("LEN ", len(cloze_text))
    print(80*"*")    
    print("Completed len", len(completed_text))

    for i, row in enumerate(completed_text):
        print(i, len(row), row, row == " ")
    print(80*"-") 

    # Zpracování první úlohy
    first_task_text = first_task[0]
    first_task_options = first_task[1:-1]
    # Ochrana proti slovu "ANSWERS" v odpovědích
    for i in range(len(first_task_options)-1, 0, -1):
        print(i)
        if first_task_options[i] == "" or first_task_options[i].find("ANSWERS") != -1:
            first_task_options.pop(i)


    first_task_answers = []  
    for t in first_task[1:]:
        if t.find("ANSWERS:") != -1:
            first_task_answers = t.split(":")[1].split()
            break
    # Ochrana pred pismeny v listu
    for i, item in enumerate(first_task_options):
        if item[0:2] in ["a)", "b)", "c)", "d)", "e)", "f)", "1)", "2)", "3)", "4)", "5)", "6)", "1.", "2.", "3.", "4.", "5.", "6." ]:
            if item[2] == " ":
                first_task_options[i] = item[3:] 
            else:
                first_task_options[i] = item[2:]

    # Získání čísel odpovědí (indexů v poli)
    alphabet = "ABCDEFGH"
    for i in range(len(first_task_answers)):
        print(first_task_answers[i])
        first_task_answers[i] = alphabet.index(first_task_answers[i][1])

    # Zpracování druhé úlohy, pokud není vynechána
    if without_short == False:
        second_task_text = second_task[0]
        second_task_words = []
        for t in second_task[1:]:
            if t.find("ANSWERS:") != -1:
                second_task_words = t.split(":")[1].replace(",", "").split()
        second_task_answers = []
        for word in second_task_words:
            second_task_answers.append(word[1])
            second_task_answers.append(word.split(")")[1])
            second_task_answers.append(word.replace("(","").replace(")",""))

    # MULTICHOICE
    for q in range(5):
        for i in range(len(cloze_text)):
            qn = q + 1
            index = cloze_text[i].find(str(qn) + ")_") 
            if index == -1:
                index = cloze_text[i].find(str(qn) + ") _") 
                if index != -1:
                    cloze_text[i] = cloze_text[i][0:index+2] + "_" +  cloze_text[i][index+3:]
            if  (index != -1):
                index2 = index +2
                for j in range(100):
                    if len(cloze_text[i]) <= index2:
                        break
                    if  cloze_text[i][index2] == "_":
                        index2 = index2+1
                    else:
                        break  
                cloze_text[i] = cloze_text[i].replace(str(qn) + ")" + (index2 - (index +2))*"_", "") 

                answer_str = "{1:MULTICHOICE:"
                print(q, first_task_answers)
                right_answer = first_task_answers[q]
                for op_i in range(len(first_task_options)):
                    if op_i > 0:
                        answer_str  = answer_str + "~"
                    if  op_i == right_answer:
                        answer_str  = answer_str + "%100%"
                    else:
                        answer_str  = answer_str + "%0%"
                    answer_str = answer_str + first_task_options[op_i] + "#"
                answer_str = answer_str + "}"
                cloze_text[i] = cloze_text[i][0:index] + answer_str + cloze_text[i][index:]
                if cloze_text[i][index-1] == "(":              
                    cloze_text[i] = cloze_text[i][0:index-1] +  cloze_text[i][index:]         
    #WORDS (SHORT ANSWER)
    if without_short == False:
        for w_i in range(0, len(second_task_answers), 3):
            for i in range(len(cloze_text)):
                index = cloze_text[i].find(second_task_answers[w_i] + "_") 
                if  (index != -1):
                    index2 = index +2
                    for j in range(12):
                        if  cloze_text[i][index2] == "_":
                            index2 = index2+1
                        else:
                            break
                    cloze_text[i] = cloze_text[i].replace(second_task_answers[w_i] + "_" + (index2 - (index +2))*"_", second_task_answers[w_i]) 
                    index = index + 1 
                    answer_str = "{3:SHORTANSWER:%100%"+second_task_answers[w_i + 1]+"#~%100%"+second_task_answers[w_i + 2]+"#}"
                    cloze_text[i] = cloze_text[i][0:index] + answer_str + cloze_text[i][index:]

    return cloze_text, first_task_text, first_task_options, first_task_answers, second_task_text, second_task_words, completed_text, questions

if __name__ == "__main__":
    without_short = False
    if len(sys.argv) > 1 and sys.argv[1] == "true":
        without_short = True
    files = glob.glob(os.path.join(input_dir, "*.docx"))
    alphabet = "ABCDEFGH"
    
    # Zpracování každého souboru
    for f in files:
        cloze_text, first_task_text, first_task_options, first_task_answers, second_task_text, second_task_words, completed_text, questions = translate(f, without_short)

        output_filename = os.path.basename(f).split(".")[0] + ".txt"
        of = open(os.path.join(output_dir, output_filename), "w")
        for row in cloze_text:
            of.write(row + "\n\n")
        of.write("\n" + 80*"#" + "\n")
        of.write(first_task_text  + "\n")
        for option in first_task_options:
            of.write(option  + "\n")
        of.write("ANSWERS: ")          
        #print(first_task_options)  
        for i, answer in enumerate(first_task_answers):
            of.write(str(i+1)  +  alphabet[answer])
            if i < len(first_task_answers):
                of.write(", ")
        of.write("\n\n" + 80*"#" + "\n")
        if without_short == False:
            of.write(second_task_text  + "\n") 
            of.write("ANSWERS: ")          
            for i, answer in enumerate(second_task_words):
                of.write(answer)
                if i < len(second_task_words):
                    of.write(", ")
            of.write("\n\n" + 80*"#" + "\n")      
        for i, row in enumerate(completed_text):
            if (i > 0):
                of.write(row + "\n\n")      
            else:
                of.write(row + "\n")         
        of.write("\n\n" + 80*"#" + "\n")                           
        index = -1
        a = ["A. ", "B. ", "C. ", "D. ", "E. "]
        for row in questions:
            if len(row) == 0:
                continue
            if row.find("ANSWER:") != -1:
                index = -1
                of.write(row + "\n") 
                of.write("\n")
                continue
            if index >=0:
                of.write(a[index] + row + "\n")
            else:
                of.write(row + "\n") 
            index += 1
        of.close()
        




