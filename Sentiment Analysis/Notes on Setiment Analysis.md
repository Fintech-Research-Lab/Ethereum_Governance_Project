We created sentiment analysis using python library transformer specifically the model of bert-base-multilingual-uncased-sentiment. This library is the most well-trained model but it only work on maximum 
as this model was trained on twitter data. We apply this sentiment analysis on comments made on magician. The full code is in the file sent_broken_comments_final.ipynb. As a first step each comment was 
broken into multiple comments of 512 words. We organize all comments by EIPs so all comments made by each EIP is aggregated.

The first part of the code runs a function called "preprocess" This function removes "stop words", lower cases, and removes punctuations. 

First we apply a function called tokenize_comment which tokenizes comments that are greater than 512 words using nltk_sent_tokenizer. This is a specialized function that is designed to tokenize comment that
have greater than 512 word length. Tokenizing comments creates list that contains multiple comments as separate items. If comments are greater than 512 words, the list breaks it into separate items in the list

Finally we apply the BERT sentiment analysis using the sentiment_analysis function from BERT. This function produces two outputs. First it gives a sentiment score which is discrete score of either 1,2,3,4, or 5.
The interpretation of these scores is that a score of 1 is considered most negative sentiment whereas the core of 5 is considered most positive.

We save the magician sentiment score in the file magician_comments_separated_withresults.csv 


We use the R code "Generating Mode and Mean Sentiment" in extracting data from magician_comments_separated_withresults.csv. The above Python code creates sentiment analysis which is stored in a dictionary that contains two elements for each item. The first element of a dictionary item is a label which is the sentiment score one of these digits (1,2,3,4, or 5). The second element in the is score which is a number from 0-1. The score is a confidence measure which tells a user how confident the model is in coming up with the sentiment label. A core of 0.99 would imply a very high confidence in the score while a number of 0.05 would have a very low confidence. You can think of this as a signal to noise measure where a high number conveys a strong signal

The R code first extract scores and labels from the disctionary, it then applies a filter that only records labels (sentiment score 1,2,3,4, or 5) of the score is greater than 0.5. The idea is that unless the model has a confidence level of at least 50% or greater for a score, then record the label otherwise "discard" the label.

Once the 'filtered scores' are recorded, we calculate mode and mean sentiments. In mode sentiments we take mode of the sentiment labels and in mean we take mean of the sentiment. The idea behind using mode sentiment is that if most of the comments are positive or negative and fewer commets are nuetral then we assign the mode_sentiment score to the EIP that represented "majority" of the opinions expressed. We calculate mean sentiment also but use mode_sentiment in our further analysis, because nuetral sentiments are highly noisy and real signal only come when someone expresses a clear opinion about an EIP. 

Both the results of mode_sentiments and textual data on magician comments is stored in file called "data_with_mode_sentiment.csv"
