# The purpose of this code is to create a name matching algorithm using Fuzzy Logic
# We have four datasets that are organized by authors but there is no unique alphanumeric
# id that combines these data. This code is designed to do the following

# 1. First create a list of Authors of EIPs from a master file
# 2. Assign an numeric id to each author
# 3. Match author names using text matching techniques with data sets that contains twitter, github, 
#    and company data

# Then create a list of authors by different data sets for manual checking

# We have four datasets that are organized by authors but there is no unique alphanumeric
# id that combines these data. This code is designed to do the following

# 1. First create a list of Authors of EIPs from a master file
# 2. Assign an numeric id to each author
# 3. Match author names using text matching techniques with data sets that contains twitter, github, 
#    and company data

# Then create a list of authors by different data sets for manual checking

# Let's use the following packages

library(data.table)
library(readxl)
library(dplyr)
library(stringr)
library(stringi)
library(rlist)
library(stringdist)

# Get the master file 

## Create a master file that contains unique author ids #########
master <- fread("c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/ALLEIPS2.csv")
# order it by EIP number
master <- arrange(master, Number)
# Break the EIPs by number of Authors
author <- str_split_fixed(master$Author, ',', 11)
author <- data.table(author)

# apply name modification to authors

author <- apply(author,2,function(x){ifelse(x != "",stri_trans_general(x,"Latin-ASCII"),"")})
author <- apply(author,2,function(x){ifelse(x != "",gsub(" ","",x),"")})
author <- apply(author,2,function(x){ifelse(x != "",tolower(x),"")})

author <- data.table(author)

# create a list of unique author names
author_name <- data.table(author_name = unique(na.omit(unlist(author))))
author_name <- author_name %>% filter(author_name != "")

# check for dupliactes
which(duplicated(author_name$author_name) == TRUE) # no duplicates 

# create unique names and then add unique ids to author name and then combine them to the master file

author_name$author_id <- seq(1,nrow(author_name),1)

# to create a columns of author_number in master file, first combine modified author names to the master file
colnames(author) <- c("author1","author2","author3","author4","author5","author6","author7","author8","author9","author10","author11")
master <- cbind(master,author)

# now create a author_number column for each author

master <- merge(master,author_name, by.x = "author1",by.y="author_name", all.x = TRUE)
master <- rename(master,author1_id = author_id)

master <- merge(master,author_name, by.x = "author2",by.y="author_name", all.x = TRUE)
master <- rename(master,author2_id = author_id)

master <- merge(master,author_name, by.x = "author3",by.y="author_name", all.x = TRUE)
master <- rename(master,author3_id = author_id)

master <- merge(master,author_name, by.x = "author4",by.y="author_name", all.x = TRUE)
master <- rename(master,author4_id = author_id)

master <- merge(master,author_name, by.x = "author5",by.y="author_name", all.x = TRUE)
master <- rename(master,author5_id = author_id)

master <- merge(master,author_name, by.x = "author6",by.y="author_name", all.x = TRUE)
master <- rename(master,author6_id = author_id)

master <- merge(master,author_name, by.x = "author7",by.y="author_name", all.x = TRUE)
master <- rename(master,author7_id = author_id)

master <- merge(master,author_name, by.x = "author8",by.y="author_name", all.x = TRUE)
master <- rename(master,author8_id = author_id)

master <- merge(master,author_name, by.x = "author9",by.y="author_name", all.x = TRUE)
master <- rename(master,author9_id = author_id)

master <- merge(master,author_name, by.x = "author10",by.y="author_name", all.x = TRUE)
master <- rename(master,author10_id = author_id)

master <- merge(master,author_name, by.x = "author11",by.y="author_name", all.x = TRUE)
master <- rename(master,author11_id = author_id)

# save it

fwrite(master,"c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/ALLEIPS_with_author_id.csv")

