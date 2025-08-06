import pandas as pd
from urllib.parse import quote

# Read CSV
df = pd.read_csv('utilities/pdf_meta.csv')

# URL encode the pdf_url column
df['pdf_url'] = df['pdf_url'].apply(lambda x: quote(x, safe=':/.'))

# Write back to CSV
df.to_csv('utilities/pdf_meta.csv', index=False)
