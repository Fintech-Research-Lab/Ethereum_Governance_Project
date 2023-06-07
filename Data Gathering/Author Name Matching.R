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

## Name Match with Twitter Data #############

# name match twitter data uses fuzzy logic matching names after they have been treated with removing spaces 
# lowering cases, and removing latic characters

# The above section creates a author_name data table that contains unique id and modified names
# we begin with that table. The modified name already has been treated

author_name <- rename(author_name, mod_name = author_name)

# save author name file

fwrite(author_name, "c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/unique_author_names_with_id.csv")

# Bring twitter data 

tw1 <-  read_excel("c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/twitter following data 5312023.xlsx")


# apply same treatment to tw data
tw <- tw1 %>% dplyr::select(author_name,EIP)
tw <- data.table(tw)

# apply name treatment similar to what we did in the "master" name list in the code above

tw <- tw %>% mutate(mod_name = stri_trans_general(author_name,"Latin-ASCII")) # remove Latin Characters
tw <- tw %>% mutate(mod_name =gsub(" ","",mod_name)) # remove spaces
tw <- tw %>% mutate(mod_name = tolower(mod_name)) # lower caps
tw <- tw %>% mutate(mod_name = iconv(mod_name, from = "UTF-8", to = "ASCII//TRANSLIT"))

# apply fuzzy logic to treated list of author names
best_matches <- amatch(author_name$mod_name, tw$mod_name, method = "jw")
tw_matched_names <- tw$author_name[best_matches]
length(which(is.na(tw_matched_names) == TRUE)) # 15 names could not be matched using fuzzy logic jw method after treatment

# attach twitter following list to unique names
author_name$tw_matched_names <- tw_matched_names

# to find names that are in twitter but not in the master list 

tw <- as.data.frame(tw)
author_name <- as.data.frame(author_name)
tw_extra <- tw[which(tw$mod_name %in% author_name$mod_name == FALSE),]

# create an author list that also contains unmatched twitter accounts

author_name$extra_in_twitter <- rep(NA,nrow(author_name))
author_name$extra_in_twitter[1:26] <- tw_extra$author_name

# create a new twitter data that contains author_number 

tw1$mod_name <- tw$mod_name
a <- author_name %>% dplyr::select(mod_name,author_id,)
tw2 <- merge(tw1,author_name, by.x = "mod_name", by.y = "mod_name", all.x = TRUE)

# save modified twitter data
fwrite(tw2,"c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/modified_twitter_data.csv")

## Name Match GitHub Data #############

# get github data

g <- fread("C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/author_github_followers_v3.csv")

# check duplicate names

which(duplicated(g$Full_Name) == TRUE)

# remove duplicate names

g1 <- g[!duplicated(g$Full_Name, fromLast = TRUE)]

fwrite(g1,"C:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/author_github_followers_v3_dup_removed.csv")

# treat full name with lowering cap, removing spaces and remove latin_characters

g1 <- g1 %>% mutate(mod_name = stri_trans_general(Full_Name,"Latin-ASCII")) # remove Latin Characters
g1 <- g1 %>% mutate(mod_name =gsub(" ","",mod_name)) # remove spaces
g1 <- g1 %>% mutate(mod_name = tolower(mod_name)) # lower caps
g1 <- g1 %>% mutate(mod_name = iconv(mod_name, from = "UTF-8", to = "ASCII//TRANSLIT"))

# match names using JW distance method

# apply fuzzy logic to treated list of author names
best_matches <- amatch(author_name$mod_name, g1$mod_name, method = "jw")
gh_matched_names <- g1$Full_Name[best_matches]
length(which(is.na(g1_matched_names) == TRUE)) # 139 names could not be matched using fuzzy logic jw method after treatment

# attach twitter following list to unique names
author_name$gh_matched_names <- gh_matched_names

# save the new author_name file

fwrite(author_name, "c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/unique_author_names_with_id.csv")


# to find names that are in twitter but not in the master list 

g1_extra <- subset(g1,! g1$mod_name %in% author_name$mod_name)

# create an author list that also contains unmatched github accounts

author_name$extra_in_gh <- rep(NA,nrow(author_name))
author_name$extra_in_gh[1:91] <- g1_extra$Full_Name
author_name <- relocate(author_name,gh_matched_names,.after = tw_matched_names)

# create a new gh data that contains author_number 

g2 <- merge(g1,author_name[,c("mod_name","author_id","gh_matched_names","extra_in_gh")], by.x = "mod_name", by.y = "mod_name", all.x = TRUE)

# save modified gh data
fwrite(g2,"c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/modified_github_data.csv")


## This part of the code added on 6-7-2023 is to add author id to the company data
# Note that we begin by opening a modified twitter file that has been manually reconciled 
# we will use the author id and twitter names of this file to apply the matching algorith with the 
# company file

# bring author names with id file

author_name <- fread("c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/unique_author_names_with_id.csv")

# bring the file with company data

co1 <- fread("c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/Old Data WIP/company.csv")

# check duplicate names

which(duplicated(co1$Name) == TRUE) # found 4 duplicates 

# remove duplicate names

co1 <- co1[!duplicated(co1$Name, fromLast = TRUE)]

# save after removing duplicates

fwrite(co1, "c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/Old Data WIP/company_duplicatesremoved.csv")

co <- co1 %>% dplyr::select(Name)

# treat Name with lowering cap, removing spaces and remove latin_characters

co <- co %>% mutate(mod_name = stri_trans_general(Name,"Latin-ASCII")) # remove Latin Characters
co <- co %>% mutate(mod_name =gsub(" ","",mod_name)) # remove spaces
co <- co %>% mutate(mod_name = tolower(mod_name)) # lower caps
co <- co %>% mutate(mod_name = iconv(mod_name, from = "UTF-8", to = "ASCII//TRANSLIT"))

# match names using JW distance method

# apply fuzzy logic to treated list of author names
best_matches <- amatch(author_name$mod_name, co$mod_name, method = "jw")
co_matched_names <- co$Name[best_matches]
length(which(is.na(co_matched_names) == TRUE)) # 319 names could not be matched using fuzzy logic jw method after treatment

# attach company list to unique names
author_name$co_matched_names <- co_matched_names

# to find names that are in company but not in the master list 

co_extra <- subset(co,! co$mod_name %in% author_name$mod_name)

# create extra_in_co record in the author_name file

author_name$extra_in_co <- rep(NA,nrow(author_name))
author_name$extra_in_co[1] <- co_extra$Name
author_name <- relocate(author_name,gh_matched_names,.after = tw_matched_names)

# save new author_name

fwrite(author_name, "c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/unique_author_names_with_id.csv")

# create a new co data that contains author_number

# add mod name to co1 the full data

co1$mod_name <- co$mod_name

co2 <- merge(co1,author_name[,c("mod_name","author_id","co_matched_names","extra_in_co")], by.x = "mod_name", by.y = "mod_name", all.x = TRUE)

# save modified co data
fwrite(co2,"c:/Users/moazz/Box/Fintech Research Lab/Ethereum Governance Project/modified_company_data.csv")



# scratch work
dist_matrix <- stringdistmatrix(author_unique$mod_name, tw$mod_name, method = "jw")
