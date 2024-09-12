import json
import pymysql
import streamlit as st
from SimplerLLM.language.llm import LLM, LLMProvider

def insert_subject_line(db_host, username, pwd, db_name, subject_line, score, template, type):
    try:
        connection = pymysql.connect(
            host=db_host,
            user=username,
            password=pwd,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")

    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `subject_lines` (`SUBJECT`, `SCORE`, `FORMULA`, `TYPE`) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (subject_line, score, template, type))
        connection.commit()
    finally:
        connection.close()

def generate_response(subject_line: str):
    llm_instance = LLM.create(provider=LLMProvider.OPENAI, model_name="gpt-4o-mini")
    u_prompt = f"""
    ##Task

    Act as a professional Email Marketer. I am gonna give you a subject line in the inputs section delimited between triple backticks which I created and I want you to generate for me a score, template, and a topic classification based on the 3 criteria I'll give you below. 
    Plus,  make sure you just give the final result immediately based on the output format I'm gonna give you and the end. 

    ##Criteria

    1. Template Creation:
    Provided a subject line, you will generate a generic template based on that input. 
    Replace unique elements within the original subject line with placeholders [X] or something more detailed, while preserving the overall structure to enable easy customization for various niches. 
    
    2. Professional Subject Line Analysis:
    Using the provided subject line, you will analyze it based on predefined criteria to generate scores for effectiveness, scannability, sentiment, spam triggers, usage of all-caps words, and emojis, and offer alternative subject lines. 
    The analysis will also classify the subject line type.
        
        Criteria:
        
        - Effectiveness: Score out of 100 representing the overall impact and engagement potential. The effectiveness score will be calculated based on a weighted combination of the following criteria:
        - Scannability: Score out of 10 indicating how easily the main message is understood.
        - Sentiment: Score out of 10 assessing the emotional tone conveyed.
        - Spam Triggers: Score out of 10 evaluating the likelihood of triggering spam filters. This criteria has a higher weight due to its negative impact on effectiveness.
        - All Caps Words: Score out of 10 noting the presence of words in all capital letters. This criteria has a higher weight due to its negative impact on effectiveness.
        - Emojis: Score out of 10 assessing the impact of emojis on the total efficiency of the subject line.
            
        The weighted scoring system will be used to calculate the overall effectiveness score, considering the relative importance of each criterion. 
        Higher scores in Scannability, Sentiment, and Emojis will positively contribute to effectiveness, while higher scores in Spam Triggers and All Caps Words will negatively impact effectiveness.
            
    3. Subject Line Type Classification:
    Classify the provided subject line into only one of the following types: Informational, Announcement, Promotion, Generic, Cold, or Survey.

    ##Output Examples:

    Input: "2 Questions YouTubers Need To Stop Asking"
    {{
        "subject": "2 Questions YouTubers Need To Stop Asking",
        "score": "90",
        "template": "[X] Questions [Audience] Need To Stop Asking",
        "category": "Informational"
    }}

    Input: "I need to give you more money"
    {{
        "subject": "I need to give you more money",
        "score": "76",
        "template": "I need to give you more [X]",
        "category": "Announcement"
    }}

    Input: "👔 3 years in 3 hours"
    {{
        "subject": "👔 3 years in 3 hours",
        "score": "91",
        "template": "[Emoji] [X] years in [X] hours",
        "category": "Generic"
    }}

    Input: "3 ways to trick AI content detectors 🤖"
    {{
        "subject": "3 ways to trick AI content detectors 🤖",
        "score": "87",
        "template": "3 ways to [Achieve Goal] [Emoji]",
        "category": "Informational"
    }}

    Input: "Simple Way to Boost Conversions with Your Email Marketing"
    {{
        "subject": "Simple Way to Boost Conversions with Your Email Marketing",
        "score": "88",
        "template": "Simple Way to [Goal] with Your [Type of Marketing]",
        "category": "Promotion"
    }}

    ##INPUT

    Subject Line: ```[{subject_line}]```

    ##OUTPUT FORMAT
    The output should be in a json format as show in the output examples above and nothing else.
    """

    response = llm_instance.generate_response(prompt=u_prompt)

    return response

st.title('Subject Lines Automation')

subject_line = st.text_input('Enter your email subject line:', '')

if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

if st.button('Analyze Subject Line'):
    st.session_state.analyzed = True

if st.session_state.analyzed:
    host=st.secrets["host"]
    user=st.secrets["user"]
    password=st.secrets["password"]
    db=st.secrets["db"]

    if subject_line:
        result1 = generate_response(subject_line)
        result2 = generate_response(subject_line)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('Result 1')
            result1_json = json.loads(result1)
            st.text_area('Output:', value=result1, height=None, disabled=True, key="Text_Area_1")
            if st.button('Add to Database.', key='save_to_db1'):
                try:
                    if isinstance(result1_json, dict):
                        insert_subject_line(host, user, password, db, subject_line, result1_json['score'], result1_json['template'], result1_json['category'])
                        st.success('Result 1 saved!')
                    else:
                        st.error('Result 1 format is incorrect or missing data.')
                except Exception as e:
                    st.error(f'Error processing result 1: {e}')

        with col2:
            st.subheader('Result 2')
            result2_json = json.loads(result2)
            st.text_area('Output:', value=result2, height=None, disabled=True, key="Text_Area_2")
            if st.button('Add to Database.', key='save_to_db2'):
                try:
                    if isinstance(result2_json, dict):
                        insert_subject_line(host, user, password, db, subject_line, result1_json['score'], result1_json['template'], result1_json['category'])
                        st.success('Result 2 saved!')
                    else:
                        st.error('Result 2 format is incorrect or missing data.')
                except Exception as e:
                    st.error(f'Error processing result 2: {e}')
    else:
        st.error('Please enter a subject line.')
