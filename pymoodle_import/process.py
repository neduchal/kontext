from sqlite3 import complete_statement
from docx import Document
import os
import os.path
import string
import glob 
import sys

input_dir = "input"
output_dir = "./output"


def translate(filename, without_short=False):
    print(filename)
    document =  Document(filename)

    cloze_text = []
    first_task = []
    second_task = []
    completed_text = []
    questions = []
    state = -1
    second_task_text = ""
    second_task_words = [] 

    for par in document.paragraphs:
        for run_idx, r in enumerate(par.runs):
            if (r.bold == True):
                state = state + 1
                if without_short and state == 2:
                    state = state + 1
            if (state == 0):
                if  (par.text[0:6] != "source"):
                    cloze_text.append(par.text)
            elif (state == 1) : 
                first_task.append(par.text)
            elif (state == 2) : 
                second_task.append(par.text)
            elif (state == 3) : 
                completed_text.append(par.text) 
                if (len(completed_text) == len(cloze_text)+1):
                    state = state + 1 
            elif(state == 4):
                questions.append(par.text)
            break

    first_task_text = first_task[0]
    first_task_options = first_task[1:-1]
    for i in range(len(first_task_options)-1, 0, -1):
        print(i)
        if first_task_options[i] == "" or first_task_options[i].find("ANSWERS") != -1:
            first_task_options.pop(i)


    first_task_answers = []    
    for t in first_task[1:]:
        if t.find("ANSWERS:") != -1:
            first_task_answers = t.split(":")[1].split()
            break

    for i, item in enumerate(first_task_options):
        if item[0:2] in ["a)", "b)", "c)", "d)", "e)", "f)", "1)", "2)", "3)", "4)", "5)", "6)", "1.", "2.", "3.", "4.", "5.", "6." ]:
            if item[2] == " ":
                first_task_options[i] = item[3:] 
            else:
                first_task_options[i] = item[2:]
    #first_task_answers = first_task[-1].split(":")[1].split()

    alphabet = "ABCDEF"
    for i in range(len(first_task_answers)):
        first_task_answers[i] = alphabet.index(first_task_answers[i][1])

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
                for j in range(25):
                    if  cloze_text[i][index2] == "_":
                        index2 = index2+1
                    else:
                        break  
                cloze_text[i] = cloze_text[i].replace(str(qn) + ")" + (index2 - (index +2))*"_", "") 

                answer_str = "{1:MULTICHOICE:"
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
    #WORDS
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
    alphabet = "ABCDEF"
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
        print(first_task_options)  
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
        




