from deep_translator import GoogleTranslator


translator = GoogleTranslator(source='iw', target='ru')

print(translator.translate("אני רוצה לחגוג"))
