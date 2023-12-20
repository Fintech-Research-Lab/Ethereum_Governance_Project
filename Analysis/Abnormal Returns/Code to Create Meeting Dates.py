# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 11:18:19 2023

@author: moazz
"""

import pandas as pd
import openai

openai.api_key = 'ENTER KEY HERE'


def standardize_date(date_str):
    if pd.isna(date_str):
        return 'Missing'

    try:
        # Adjust the engine name to a known GPT-3 engine
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Standardize the date {date_str} to MM/DD/YYYY format:",
            max_tokens=50
        )
        standardized_date = response['choices'][0]['text'].strip()
        return standardized_date
    except Exception as e:
        print(f"An error occurred: {e}")
        return date_str  # Return the original date string if there is an error


def main():
    df = pd.read_csv('calls_updated.csv')
    df['Date'] = df['Date'].apply(standardize_date)
    df.to_csv('calls_updated_standardized.csv', index=False)


if __name__ == "__main__":
    main()