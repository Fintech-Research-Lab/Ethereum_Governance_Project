import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import numpy as np

###############################################################################
# SETUP
os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project')


###############################################################################
# DEFINE FUNCTIONS

# Strip last name from full name
def get_last_name(full_name):
    """Extract the last name from a full name."""
    parts = full_name.split()
    return parts[-1] if parts else full_name



# Create network graph
def plot_bc_graph(df, G, centrality, typ):
    
        
    # Create a list of author id and name
    
    aut_id_names = {}
    
    m95 = np.percentile(list(centrality.values()),95)
    
    for i in range(1,15):
        for _, row in df.iterrows():
            if np.isnan(row['author' + str(i) + '_id']) == False and \
                centrality[str(int(row['author' + str(i) + '_id']))] > m95 :
                aut_id_names['{:.0f}'.format(row['author' + str(i) + '_id'])] \
                = get_last_name(row['author' + str(i) ])
      
            
    # Create Node Size standardized to max of 1000 and min of 10
    
    node_size_min = np.min(list(centrality.values()))
    node_size_max = np.max(list(centrality.values()))
    node_size = ( (list(centrality.values()) - node_size_min)* 990 / (node_size_max-node_size_min)) +10
        
    
    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(G, k=0.5, iterations=100)
    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color='skyblue', edgecolors='black')
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    nx.draw_networkx_labels(G,  pos , aut_id_names, font_size=10, font_weight='bold')
#    plt.title('Betweenness Centrality of Ethereum EIP Co-authorship Graph', fontsize=25, fontweight='bold')
    plt.axis('off')
    
    #We remove the surrounding box.
    plt.box(False)
    plt.savefig('Analysis/Centrality Analysis/eip_' + typ + '.png', bbox_inches="tight")
    plt.show()



###############################################################################
# LODN AND CLEAN DATA


# Load the CSV file
data = pd.read_csv('Data/Raw Data/Ethereum_Cross-sectional_Data_output.csv')

data = data.loc[(data['Category']!='Meta') & (data['Category']!='Informational' )]
data.loc[data['author3'] == 'et al.', 'author3'] = np.NaN

# Combine all author names into a single column separated by commas
data['allid'] = data[['author1_id', 'author2_id', 'author3_id', 'author4_id', 'author5_id', 
                       'author6_id', 'author7_id', 'author8_id', 'author9_id', 'author10_id',
                       'author11_id', 'author12_id', 'author13_id', 'author14_id', 'author15_id'
                       ]].apply(lambda x: ','.join(x.dropna().astype(int).astype(str)), axis=1)

data['author'] = data[['author1', 'author2', 'author3', 'author4', 'author5', 
                       'author6', 'author7', 'author8', 'author9', 'author10',
                       'author11', 'author12', 'author13', 'author14', 
                       'author15']].apply(lambda x: ', '.join(x.dropna()), axis=1)



###############################################################################
# NETWORK OF ALL EIPS

# Create an empty graph for last names

G_all = nx.Graph()

# Iterate through each row in the dataset to construct the co-authorship graph using authorid
for _, row in data.iterrows():
    authors = [author for author in row['author'].split(', ')]
    authorids = [author for author in row['allid'].split(',')]

    for author in authorids:
        if author not in G_all:
            G_all.add_node(author)
    for i in range(len(authorids)):
        for j in range(i+1, len(authorids)):
            if G_all.has_edge(authorids[i], authorids[j]):
                G_all[authorids[i]][authorids[j]]['weight'] += 1
            else:
                G_all.add_edge(authorids[i], authorids[j], weight=1)

# Remove self-loops from the graph
G_all.remove_edges_from(nx.selfloop_edges(G_all))


# Compute betweenness centrality for each author
betweenness = nx.betweenness_centrality(G_all, weight='weight')

# Compute eigenvector centrality for each author
eigen = nx.eigenvector_centrality(G_all, weight='weight') 

# Compute eigenvector centrality for each author
close = nx.closeness_centrality(G_all) 



# Plot the graph
plot_bc_graph(data, G_all, betweenness, 'between_all')


# Plot the graph
plot_bc_graph(data, G_all, close, 'close_all')


# Plot the graph
plot_bc_graph(data, G_all, eigen, 'eigen_all')

# Count the number of EIPs each author has co-authored

  
# Create a list of author id and name

aut_id_names = {}

for i in range(1,15):
    for _, row in data.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            aut_id_names['{:.0f}'.format(row['author' + str(i) + '_id'])] \
            = row['author' + str(i) ]
 

aut_id_eip = {}

for i in range(1,15):
    for _, row in data.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            if str('{:.0f}'.format(row['author' + str(i) + '_id'])) in aut_id_eip:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] \
                = aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] +1
            else:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] = 1


eip_bc_df = pd.DataFrame.from_dict(aut_id_names, orient = 'index').rename(columns = {0 : 'name'})
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(aut_id_eip, orient = 'index').rename(columns = {0 : 'n_eip'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(betweenness, orient = 'index').rename(columns = {0 : 'between'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(close, orient = 'index').rename(columns = {0 : 'close'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(eigen, orient = 'index').rename(columns = {0 : 'eigen'}), left_index = True, right_index = True)


# Create and save a DataFrame for betweenness centrality scores
eip_bc_df.reset_index(names = 'id').to_csv("Analysis/Centrality Analysis/centrality_all.csv", index = False)



###############################################################################
# NETWORK OF FINALIZED ERC-Interfacee EIPS

# Create an empty graph for last names

G_final = nx.Graph()

data_final = data.loc[(data['status']=='Final') & ((data['Category'] == 'ERC') | (data['Category'] == 'Interface')) ]

# Iterate through each row in the dataset to construct the co-authorship graph using authorid
for _, row in data_final.iterrows():
    authors = [author for author in row['author'].split(', ')]
    authorids = [author for author in row['allid'].split(',')]

    for author in authorids:
        if author not in G_final:
            G_final.add_node(author)
    for i in range(len(authorids)):
        for j in range(i+1, len(authorids)):
            if G_final.has_edge(authorids[i], authorids[j]):
                G_final[authorids[i]][authorids[j]]['weight'] += 1
            else:
                G_final.add_edge(authorids[i], authorids[j], weight=1)

# Remove self-loops from the graph
G_final.remove_edges_from(nx.selfloop_edges(G_final))


# Compute betweenness centrality for each author
betweenness = nx.betweenness_centrality(G_final, weight='weight')

# Compute eigenvector centrality for each author
eigen = nx.eigenvector_centrality(G_final, weight='weight') 

# Compute eigenvector centrality for each author
close = nx.closeness_centrality(G_final) 



# Plot the graph
plot_bc_graph(data_final, G_final, betweenness, 'between_final')


# Plot the graph
plot_bc_graph(data_final, G_final, close, 'close_final')


# Plot the graph
plot_bc_graph(data_final, G_final, eigen, 'eigen_final')

# Count the number of EIPs each author has co-authored

  
# Create a list of author id and name

aut_id_names = {}

for i in range(1,15):
    for _, row in data_final.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            aut_id_names['{:.0f}'.format(row['author' + str(i) + '_id'])] \
            = row['author' + str(i) ]
 

aut_id_eip = {}

for i in range(1,15):
    for _, row in data_final.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            if str('{:.0f}'.format(row['author' + str(i) + '_id'])) in aut_id_eip:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] \
                = aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] +1
            else:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] = 1


eip_bc_df = pd.DataFrame.from_dict(aut_id_names, orient = 'index').rename(columns = {0 : 'name'})
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(aut_id_eip, orient = 'index').rename(columns = {0 : 'n_eip'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(betweenness, orient = 'index').rename(columns = {0 : 'between'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(close, orient = 'index').rename(columns = {0 : 'close'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(eigen, orient = 'index').rename(columns = {0 : 'eigen'}), left_index = True, right_index = True)


# Create and save a DataFrame for betweenness centrality scores
eip_bc_df.reset_index(names = 'id').to_csv("Analysis/Centrality Analysis/centrality_final.csv", index = False)



###############################################################################
# NETWORK OF IMPLEMENTED EIPS

# Create an empty graph for last names

G_imp = nx.Graph()

data_imp = data.loc[data['implementation']==1]

# Iterate through each row in the dataset to construct the co-authorship graph using authorid
for _, row in data_imp.iterrows():
    authors = [author for author in row['author'].split(', ')]
    authorids = [author for author in row['allid'].split(',')]

    for author in authorids:
        if author not in G_imp:
            G_imp.add_node(author)
    for i in range(len(authorids)):
        for j in range(i+1, len(authorids)):
            if G_imp.has_edge(authorids[i], authorids[j]):
                G_imp[authorids[i]][authorids[j]]['weight'] += 1
            else:
                G_imp.add_edge(authorids[i], authorids[j], weight=1)

# Remove self-loops from the graph
G_imp.remove_edges_from(nx.selfloop_edges(G_imp))


# Compute betweenness centrality for each author
betweenness = nx.betweenness_centrality(G_imp, weight='weight')

# Compute eigenvector centrality for each author
eigen = nx.eigenvector_centrality(G_imp, weight='weight') 

# Compute eigenvector centrality for each author
close = nx.closeness_centrality(G_imp) 



# Plot the graph
plot_bc_graph(data_imp, G_imp, betweenness, 'between_imp')


# Plot the graph
plot_bc_graph(data_imp, G_imp, close, 'close_imp')


# Plot the graph
plot_bc_graph(data_imp, G_imp, eigen, 'eigen_imp')

# Count the number of EIPs each author has co-authored

  
# Create a list of author id and name

aut_id_names = {}

for i in range(1,15):
    for _, row in data_imp.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            aut_id_names['{:.0f}'.format(row['author' + str(i) + '_id'])] \
            = row['author' + str(i) ]
 

aut_id_eip = {}

for i in range(1,15):
    for _, row in data_imp.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            if str('{:.0f}'.format(row['author' + str(i) + '_id'])) in aut_id_eip:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] \
                = aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] +1
            else:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] = 1


eip_bc_df = pd.DataFrame.from_dict(aut_id_names, orient = 'index').rename(columns = {0 : 'name'})
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(aut_id_eip, orient = 'index').rename(columns = {0 : 'n_eip'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(betweenness, orient = 'index').rename(columns = {0 : 'between'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(close, orient = 'index').rename(columns = {0 : 'close'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(eigen, orient = 'index').rename(columns = {0 : 'eigen'}), left_index = True, right_index = True)


# Create and save a DataFrame for betweenness centrality scores
eip_bc_df.reset_index(names = 'id').to_csv("Analysis/Centrality Analysis/centrality_imp.csv", index = False)




###############################################################################
# DYNAMICS OF ALL EIP NETWORK


# Create an empty graph for last names

G_all = nx.Graph()

data['sdate_d'] = pd.to_datetime(data['sdate'], format = '%d%b%Y %H:%M:%S' ) 

data.sort_values(by = 'sdate_d', inplace = True)

for i in range(len(data))
# Iterate through each row in the dataset to construct the co-authorship graph using authorid
for _, row in data.iterrows():
    authors = [author for author in row['author'].split(', ')]
    authorids = [author for author in row['allid'].split(',')]

    for author in authorids:
        if author not in G_all:
            G_all.add_node(author)
    for i in range(len(authorids)):
        for j in range(i+1, len(authorids)):
            if G_all.has_edge(authorids[i], authorids[j]):
                G_all[authorids[i]][authorids[j]]['weight'] += 1
            else:
                G_all.add_edge(authorids[i], authorids[j], weight=1)

# Remove self-loops from the graph
G_all.remove_edges_from(nx.selfloop_edges(G_all))


# Compute betweenness centrality for each author
betweenness = nx.betweenness_centrality(G_all, weight='weight')

# Compute eigenvector centrality for each author
eigen = nx.eigenvector_centrality(G_all, weight='weight') 

# Compute eigenvector centrality for each author
close = nx.closeness_centrality(G_all) 



# Plot the graph
plot_bc_graph(data, G_all, betweenness, 'between_all')


# Plot the graph
plot_bc_graph(data, G_all, close, 'close_all')


# Plot the graph
plot_bc_graph(data, G_all, eigen, 'eigen_all')

# Count the number of EIPs each author has co-authored

  
# Create a list of author id and name

aut_id_names = {}

for i in range(1,15):
    for _, row in data.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            aut_id_names['{:.0f}'.format(row['author' + str(i) + '_id'])] \
            = row['author' + str(i) ]
 

aut_id_eip = {}

for i in range(1,15):
    for _, row in data.iterrows():
        if np.isnan(row['author' + str(i) + '_id']) == False :
            if str('{:.0f}'.format(row['author' + str(i) + '_id'])) in aut_id_eip:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] \
                = aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] +1
            else:
                aut_id_eip['{:.0f}'.format(row['author' + str(i) + '_id'])] = 1


eip_bc_df = pd.DataFrame.from_dict(aut_id_names, orient = 'index').rename(columns = {0 : 'name'})
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(aut_id_eip, orient = 'index').rename(columns = {0 : 'n_eip'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(betweenness, orient = 'index').rename(columns = {0 : 'between'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(close, orient = 'index').rename(columns = {0 : 'close'}), left_index = True, right_index = True)
eip_bc_df = eip_bc_df.merge(pd.DataFrame.from_dict(eigen, orient = 'index').rename(columns = {0 : 'eigen'}), left_index = True, right_index = True)


# Create and save a DataFrame for betweenness centrality scores
eip_bc_df.reset_index(names = 'id').to_csv("Analysis/Centrality Analysis/centrality_all.csv", index = False)









