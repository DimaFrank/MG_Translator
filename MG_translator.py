import streamlit as st
from PIL import Image
import pandas as pd
from io import BytesIO
import requests
import deep_translator
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import langdetect
from langdetect import detect
import time
import openpyxl


def get_transcription(phrase):
    words = phrase.split()
    result = ''

    for word in words:
      
        url = f'https://www.pealim.com/ru/search/?from-nav=1&q={word}'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            transcription_elements = soup.find_all(class_="transcription")
            
            # Create a new list to store the filtered transcription elements
            filtered_transcriptions = []

            for element in transcription_elements:
                if element.get_text() not in ['шинита', 'шинисо']:
                    # Find the <b> tag and update its contents to uppercase
                    b_tag = element.find('b')
                    if b_tag:
                        b_tag.string = b_tag.string.upper()
                    
                    filtered_transcriptions.append(element)

            if len(filtered_transcriptions) > 0:
                result += filtered_transcriptions[0].get_text() + ' '
            else:
                return "ERROR: No transcription found for word"

        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")

    return result.strip()


def get_full_transcription(word):
    if '/' in word:
        male = word.split('/')[0]
        female = male + word.split('/')[1]
        result = f"{get_transcription(male)} / {get_transcription(female)}"
    else:
        result = get_transcription(word)
    return result.strip()


def get_examples(word):
    s = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0'
    }
    url = f'https://context.reverso.net/translation/hebrew-russian/{word}'
    response = s.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml")
        tag = soup.select("span.text[lang=he]")  # Select Hebrew text
        translation_tag = soup.select("span.text[lang=ru]")  # Select Russian text

        result = []
        for i, (hebrew_sentence, russian_sentence) in enumerate(zip(tag, translation_tag), 1):
            hebrew_text = hebrew_sentence.get_text().strip()
            russian_text = russian_sentence.get_text().strip()
            
            # Check if the text is long enough for language detection
            if len(hebrew_text) >= 10 and len(russian_text) >= 10:
                try:
                    detected_language_hebrew = detect(hebrew_text)
                    detected_language_russian = detect(russian_text)
                    
                    if detected_language_hebrew == 'he' and detected_language_russian == 'ru':
                        result.append(f"{hebrew_text}\n{russian_text}")
                except langdetect.lang_detect_exception.LangDetectException:
                    pass  # Language detection failed, skip this example

        # Join the sentences into a single string with each pair on a new line
        return "\n\n".join(result)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")


def get_translation(word):
    s = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0'
    }
    url = f'https://context.reverso.net/translation/hebrew-russian/{word}'
    response = s.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml")
        possible_classes = ["translation ltr dict n", "translation ltr dict adv", "translation ltr dict adj adj", "translation ltr dict no-pos"]        
        found = False  
        for pos_class in possible_classes:
            target_tags = soup.find_all('a', {'class': pos_class, 'lang': 'ru'})
            if target_tags:
                found = True  
                results = []  
                for i, tag in enumerate(target_tags):
                    if i < 2:
                        display_term = tag.find('span', class_='display-term').text
                        results.append(display_term)
                return f"{', '.join(results)}"
        if not found:
            return f"No results found for the word '{word}'."
    else:
        return "Failed to retrieve the page. Status code: {response.status_code}"

def get_full_translation(word):
    if '/' in word:
        return get_translation(word.split('/')[0])
    return get_translation(word)

def alternative_translation(word):
    if "No results found for the word" in get_full_translation(word):
        return GoogleTranslator(source='iw', target='ru').translate(word)
    else:
        return get_full_translation(word)


def main():
    st.title("Welcome to MG Translator")

    image = Image.open("main_pic.jpeg")
    st.image(image, caption="By Meital Goldberg")
  
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

    if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, header=None, names=['Иврит'])

            df[['Пeревод']] = df['Иврит'].apply(lambda x: pd.Series(alternative_translation(x)))
            df[['Транскрипция']] = df['Иврит'].apply(lambda x: pd.Series(get_full_transcription(x)))
            df[['Примеры']] = df['Иврит'].apply(lambda x: pd.Series(get_examples(x)))    

            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)

            with st.spinner('Wait for it...'):
                time.sleep(5)
            st.success('Done!')        
            st.balloons()

            st.download_button(
                label="Download Updated Excel File",
                data=excel_buffer.getvalue(),
                file_name="updated_file.xlsx",
                key="download_button",
            )

if __name__ == "__main__":
    main()



   
