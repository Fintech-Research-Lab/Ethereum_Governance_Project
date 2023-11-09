import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

def get_last_name(full_name):
    """Extract the last name from a full name."""
    parts = full_name.split()
    return parts[-1] if parts else full_name

os.chdir('C:/Users/cf8745/Box/Research/Ethereum Governance/Ethereum_Governance_Project')

# Load the CSV file
data = pd.read_csv('Data/Raw Data/Ethereum_Cross-sectional_Data.csv')

# Combine all author names into a single column separated by commas
data['allid'] = data[['author1_id', 'author2_id', 'author3_id', 'author4_id', 'author5_id', 
                       'author6_id', 'author7_id', 'author8_id', 'author9_id', 'author10_id',
                       'author11_id', 'author12_id', 'author13_id', 'author14_id', 'author15_id'
                       ]].apply(lambda x: ','.join(x.dropna().astype(int).astype(str)), axis=1)

data['Author'] = data[['Author1', 'Author2', 'Author3', 'Author4', 'Author5', 
                       'Author6', 'Author7', 'Author8', 'Author9', 'Author10',
                       'Author11', 'Author12', 'Author13', 'Author14', 
                       'Author15']].apply(lambda x: ', '.join(x.dropna()), axis=1)

# Create an empty graph for last names

G_last_name = nx.Graph()

# Iterate through each row in the dataset to construct the co-authorship graph using authorid
for _, row in data.iterrows():
    authors = [author for author in row['Author'].split(',')]
    authorids = [author for author in row['allid'].split(',')]

    for author in row['allid'].split(','):
        if author not in G_last_name:
            G_last_name.add_node(author)
    for i in range(len(authorids)):
        for j in range(i+1, len(authorids)):
            if G_last_name.has_edge(authorids[i], authorids[j]):
                G_last_name[authorids[i]][authorids[j]]['weight'] += 1
            else:
                G_last_name.add_edge(authorids[i], authorids[j], weight=1)

# Remove self-loops from the graph
G_last_name.remove_edges_from(nx.selfloop_edges(G_last_name))

# Remove nodes with no edges (i.e., no co-authors)
isolates = list(nx.isolates(G_last_name))
G_last_name.remove_nodes_from(isolates)


# Compute betweenness centrality for each author
betweenness_centrality_last_name = nx.betweenness_centrality(G_last_name, weight='weight')

# Compute betweenness centrality for each author
eigen_centrality_last_name = nx.eigenvector_centrality(G_last_name, weight='weight') 

# Create network graph
def plot_bc_graph(G, betweenness_centrality):
    plt.figure(figsize=(20, 20))
    node_size = [v * 20000 for v in betweenness_centrality.values()]
    pos = nx.spring_layout(G, k=0.5, iterations=100)
    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color='skyblue', edgecolors='black')
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    plt.title('Betweenness Centrality of Ethereum EIP Co-authorship Graph', fontsize=25, fontweight='bold')
    plt.axis('off')
    plt.savefig('Analysis/Centrality Analysis/eip_bc.png')
    plt.show()

# Plot the graph
plot_bc_graph(G_last_name, betweenness_centrality_last_name)

# Count the number of EIPs each author has co-authored
author_eip_count = {}
for _, row in data.iterrows():
    authors = [get_last_name(author.strip()) for author in row['Author'].split(',')]
    for author in authors:
        author_eip_count[author] = author_eip_count.get(author, 0) + 1

# Create a mapping of last names to full names using the original data
last_name_to_full_name = {}
for _, row in data.iterrows():
    authors = [author.strip() for author in row['Author'].split(',')]
    for author in authors:
        last_name_to_full_name[get_last_name(author)] = author

# Create and save a DataFrame for betweenness centrality scores
eip_bc_df = pd.DataFrame({
    'Full_Name': [last_name_to_full_name[name] for name in betweenness_centrality_last_name.keys()],
    'Number_of_EIPs_Co-authored': [author_eip_count.get(name, 0) for name in betweenness_centrality_last_name.keys()],
    'Betweenness_Centrality_Score': list(betweenness_centrality_last_name.values())
})
eip_bc_df.to_csv("Analysis/Centrality Analysis/EIP_BC.csv", index=False)
