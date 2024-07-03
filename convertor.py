import pandas as pd
import psycopg2
import boto3
import math
import numpy
import requests
from io import BytesIO

# 2 files -> class 
s3_bucket='thinking-bucket' 
s3_client = boto3.client('s3')
s3_objects = s3_client.list_objects_v2(Bucket=s3_bucket)
files = [obj['Key'] for obj in s3_objects['Contents'] if obj['Key'].endswith('.xlsx')]

for file_name in files:
    obj = s3_client.get_object(Bucket=s3_bucket, Key=file_name)
    excel_data = BytesIO(obj['Body'].read())
    df = pd.read_excel(excel_data)
    with open(f'./c.sql', 'a+') as insert_data_file:
        insert_data_file.write('-- new file here --\n')
        inserted_topics = set()
        for index, row in df.iterrows():
            if not pd.notna(row.iloc[1]):
                continue
            try:
                topic_id = int(str(row.iloc[1])[0]) 
                if topic_id not in inserted_topics:
                    topic_name = 'math' if topic_id == 1 else 'common knowlage' if  topic_id == 3 else 'english'
                    insert_data_file.write(
                        f"INSERT INTO topics (topic_id, topic_name) VALUES ({topic_id}, '{topic_name}') ON CONFLICT (topic_id) DO NOTHING;\n")
                    inserted_topics.add(topic_id)
            except Exception as e:
                print(e)

        for index, row in df.iterrows():
            if not pd.notna(row.iloc[1]):
                continue
            question_id = str(int(row.iloc[1]))  
            language_id = 1
            sub_subject_id = int(str(row.iloc[1])[3:6])  
            sub_subject_name = str(row.iloc[0])
            topic_id = int(str(row.iloc[1])[0])
            c_grade_id = int(question_id[2])  
            level = int(question_id[-1])

            q_top = 2 if topic_id == 3 or topic_id == 4 else 3
            question_text = str(row.iloc[q_top]).replace("'", "`")
            if topic_id == 3 or topic_id == 4:
                explanation = ''
                interesting_fact = str(row.iloc[7]).replace("'", "`")
            else:
                interesting_fact = ""
                explanation = row.iloc[8].replace("'", "`") if isinstance(row.iloc[8], str) else row.iloc[
                8]

            insert_data_file.write(f"""
INSERT INTO questions (question_id, language_id, topic_id, c_grade_id, level, question_text, explanation, interesting_fact)
VALUES ('{question_id}', {language_id}, {topic_id}, {c_grade_id}, {sub_subject_id}, '{question_text}', '{explanation}', '{interesting_fact}') ON CONFLICT (question_id) DO UPDATE SET language_id = {language_id} ,topic_id= {topic_id},c_grade_id ={c_grade_id},level={level},question_text='{question_text}',explanation='{explanation}',interesting_fact='{interesting_fact}';
""")
            try:

                sub_subject_id = int(str(row.iloc[1])[2:6])  
                sub_subject_name = str(row.iloc[0])
                question_id = str(int(row.iloc[1]))
                insert_data_file.write(
                        f"INSERT INTO sub_subjects (sub_subject_id, sub_subject_name , question_id) VALUES ({sub_subject_id}, '{sub_subject_name}', '{question_id}') ON CONFLICT (question_id) DO NOTHING;\n")
            except Exception as e:
                print(e)
            q_id = 3 if topic_id == 3 or topic_id ==4  else 4
            correct_answer = str(row.iloc[q_id]).replace("'",
                                                         "`").strip()  
            insert_data_file.write(f"""
INSERT INTO answer_options (question_id, correct_answer, answer_text)
VALUES ('{question_id}', TRUE, '{correct_answer}') ON CONFLICT (question_id, correct_answer, answer_text) DO NOTHING;
""")

            q_id = 4 if topic_id == 3 or topic_id ==4 else 5
            wrong_answers = [str(row.iloc[q_id]).replace("'", "`").strip(),str(row.iloc[q_id + 1]).replace("'", "`").strip(), str(row.iloc[q_id + 2]).replace("'","`").strip()]
            if 'nan' in wrong_answers:
                wrong_answers.remove('nan')
            for i,ans in enumerate(wrong_answers):
                if wrong_answers.count(ans) > 1:
                    wrong_answers.remove(ans)
            for i, answer in enumerate(wrong_answers):
                insert_data_file.write(f"""
INSERT INTO answer_options (question_id, correct_answer, answer_text)
VALUES ('{question_id}', FALSE, '{answer}') ON CONFLICT (question_id, correct_answer, answer_text) DO NOTHING;
""")


    print("INSERT commands SQL file generated successfully.")
db_params = {
        "host": "prod-database.ctaqgooomz1t.eu-central-1.rds.amazonaws.com",
        "port": "5432",
        "database": "postgres",
        "user": "postgres",
        "password": "Pa$$w0rdTk",
        }
connection = psycopg2.connect(**db_params)
cursor = connection.cursor()
sql_file = "c.sql"

# sql execution

try:
    with open(sql_file, "r") as f:
        sql_commands = f.read()

    cursor.execute('DELETE FROM answer_options;')
    cursor.execute('DELETE FROM sub_subjects;')
    cursor.execute(sql_commands)
    connection.commit()
    data = {
    'subject': 'question convertor job in jenkins',
    'success': 'was successful',
    'details': 'All tasks completed successfully'
    }
    print('data injected to the database ')
except Exception as e:
    print(e)
    data = {
    'subject': 'question convertor job in jenkins',
    'success': 'was failed',
    'details': f'error message : -> {e}'
    }
    
finally:
    url = 'http://ecs-lb-1105484532.eu-central-1.elb.amazonaws.com/api/sendemail'
    response = requests.post(url, json=data)
    print(response.status_code)
    cursor.close()
    connection.close()

