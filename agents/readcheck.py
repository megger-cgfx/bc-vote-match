import json, os
os.chdir('.')
print("ok", os.getcwd())
q = json.load(open('data/questions/questions.json'))
print(len(q), "questions")
