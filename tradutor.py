from deep_translator import MyMemoryTranslator

# Texto que você quer traduzir
texto_original = (
    "Hello! I am learning Python to automate tasks and manage my company."
)

# Usando os códigos regionais corretos exigidos pelo MyMemoryTranslator
texto_traduzido = MyMemoryTranslator(
    source='en-US', target='pt-BR'
).translate(texto_original)

print('--- Texto Original ---')
print(texto_original)
print('\n--- Texto Traduzido ---')
print(texto_traduzido)


