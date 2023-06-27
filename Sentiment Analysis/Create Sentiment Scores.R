# The following code is created to compile the results of sentiment analysis
# We ran sentiment analysis using BERT on broken sentences This created a list of sentence their sentiment expressed in {1.2.3.4.5} and
# a certainty score from 0-1 which gives confidence on the validity of sentiment score
# The following code takes this input and create a mode and mean values of sentiment using a filtering criteria that removes all
# sentiments that do not have at least 0.5 certainty score

# This code was modified on 5-17-2023. The results are not imported in stata file correctly. I will modify columns to reduce columns that are not needed
# for regressions and merge them into a stata data. In addition, I also want to add company names in the database

library(data.table)
library(tidyr)
library(dplyr)
library(stringr)
library(DescTools)
library(writexl)
library(jsonlite)
library(haven)

d <- fread("C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/Old Data WIP/magician_comments_separated_withresults.csv")
# convert a list of list into labels and scores list
d$labels <- str_extract_all(d$score, "(?<=label': ')[[:digit:]]") 
d$scores <-  str_extract_all(d$score, "(?<=score': )[0-9]\\.[0-9]+")

# create filtered scores
for(i in 1:nrow(d)){
d$filtered_score[i] <- lapply(d$scores[i],function(x){ifelse(as.numeric(x)>0.5,d$labels[i],character(0))})
}
# remove NAs from filtered score
for(i in 1:nrow(d)){
d$filtered_score_notna[i] <- sapply(d$filtered_score[i], function(x){Filter(Negate(is.na), x)})
}
# calculate mode sentiment score
for(i in 1:nrow(d)){
d$mode_sentiment[i] <- Mode(as.numeric(unlist(d$filtered_score_notna[i])))
}

for(i in 1:nrow(d)){
  d$mean_sentiment[i] <- mean(as.numeric(unlist(d$filtered_score_notna[i])))
}

length(which(is.na(d$mode_sentiment)== FALSE)) # 260 EIPs have sentiments have a mode value

summary(d$mean_sentiment)

# create a file that can be used to run regressions

d1 <- d %>% select(EIP_Number,Title,Author,mode_sentiment,mean_sentiment)

fwrite(d1,"C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/data_with_mode_sentiment_reduced.csv")

# to write the code in csv I will need to convert list into characters

d$score <- lapply(d$score, toJSON, auto_unbox = TRUE)
d$labels <- sapply(d$labels, paste, collapse = ",")
d$scores <- sapply(d$scores, paste, collapse = ",")
d$filtered_score <- sapply(d$filtered_score, paste, collapse = ",")
d$filtered_score_notna <- sapply(d$filtered_score_notna, paste, collapse = ",")

fwrite(d,"C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/sentiment_data.csv")

# create a depracated version of the file

d <- rename(d,Index = V1)

d_dep <- d %>% dplyr::select(EIP_Number, Title, Website, Author,mod_comment,mode_sentiment,mean_sentiment)

fwrite(d_dep, "C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/data_with_mode_sentiment.csv" )











