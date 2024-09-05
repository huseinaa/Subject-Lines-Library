import gspread
import streamlit as st
from ast import literal_eval
from SimplerLLM.language.llm import LLM, LLMProvider
from google.oauth2.service_account import Credentials
import tempfile

def insert_into_sheet(json_file, sheet_id, subject_line, data, row):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write(str(json_file))  
        temp_file.flush() 

        creds = Credentials.from_service_account_file(temp_file.name, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0) 

        worksheet.update_cell(row, 1, subject_line)
        if len(data) >= 3:  
            worksheet.update_cell(row, 2, data[0])  # Score
            worksheet.update_cell(row, 3, data[1])  # Template
            worksheet.update_cell(row, 4, data[2])  # Topic classification

def generate_response(subject_line: str):
    llm_instance = LLM.create(provider=LLMProvider.OPENAI, model_name="gpt-4o-mini", api_key=st.secrets["OPENAI_API_KEY"])
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
    Classify the provided subject line into one of the following types: Informational, Announcement, Promotion, Generic, Cold, or Survey.

    ##Output Examples:

    Input: "2 Questions YouTubers Need To Stop Asking"
    ["90", "[X] Questions [Audience] Need To Stop Asking", "Informational"]

    Input: "I need to give you more money"
    ["76", "I need to give you more [X]", "Announcement"]

    Input: "👔 3 years in 3 hours"
    ["91", "[Emoji] [X] years in [X] hours", "Generic"]

    Input: "3 ways to trick AI content detectors 🤖"
    ["87", "3 ways to [Achieve Goal] [Emoji]", "Informational"]

    Input: "Simple Way to Boost Conversions with Your Email Marketing"
    ["88", "Simple Way to [Goal] with Your [Type of Marketing]", "Promotion"]

    ##INPUT

    Subject Line: ```[{subject_line}]```

    ##OUTPUT FORMAT
    The output should be in a list format as show below and nothing else.
    [Score, Template, Topic]
    """

    response = llm_instance.generate_response(prompt=u_prompt)

    return response

st.title('Subject Lines Automation')

subject_line = st.text_input('Enter your email subject line:', '')
row = st.text_input('Enter the row you want to edit:', '')

if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

if st.button('Analyze Subject Line'):
    st.session_state.analyzed = True

if st.session_state.analyzed:
    sheet_id = st.secrets["sheet_id"]
    json_file = st.secrets["client_secret_key"]

    if subject_line and json_file and sheet_id:
        result1 = generate_response(subject_line)
        result2 = generate_response(subject_line)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('Result 1')
            result1_list = literal_eval(result1) 
            st.text_area('Output:', value=result1, height=None, disabled=True, key="Text_Area_1")
            if st.button('Add to Google Sheets.', key='save_to_sheet1'):
                try:
                    if isinstance(result1_list, list) and len(result1_list) == 3:
                        insert_into_sheet(json_file, sheet_id, subject_line, result1_list, int(row))
                        st.success('Result 1 saved!')
                    else:
                        st.error('Result 1 format is incorrect or missing data.')
                except Exception as e:
                    st.error(f'Error processing result 1: {e}')

        with col2:
            st.subheader('Result 2')
            result2_list = literal_eval(result2) 
            st.text_area('Output:', value=result2, height=None, disabled=True, key="Text_Area_2")
            if st.button('Add to Google Sheets.', key='save_to_sheet2'):
                try:
                    if isinstance(result2_list, list) and len(result2_list) == 3:
                        insert_into_sheet(json_file, sheet_id, subject_line, result2_list, int(row))
                        st.success('Result 2 saved!')
                    else:
                        st.error('Result 2 format is incorrect or missing data.')
                except Exception as e:
                    st.error(f'Error processing result 2: {e}')
    else:
        st.error('Please enter a subject line and Google Sheets configuration.')
