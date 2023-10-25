// Regression Code

cd "C:\Users\moazz\Box\Fintech Research Lab\Ethereum Governance Project\Ethereum Project Data\"
use "Ethereum_Cross-sectional_Data.dta", clear




// create labels

// Create labels
label var log_tw "log(1+Twitter Followers)"
label var log_gh "log(1+GitHub Followers)"
label var tf_scale "No. Twitter Followers(1000s)"
label var n_author "Number of EIP Authors"
label var betweenness "Betweenness-Centrality"
label var author_commit "Author Commits"
label var total_commit "Total Commits"
label var eip_contributors "EIP Contributors"
label var besu_commits "Besu Commits"
label var erigon_commits "Erigon Commits"
label var geth_commits "Geth Commits"
label var nethermind_commits "Nethermind Commits"
label var dummy_spearbit_labs "Spearbit"
label var dummy_ethereum_name_service "Ethereum Name Service"
label var dummy_consensys "ConsenSys"
label var dummy_stoneshot "Stoneshot"
label var dummy_cube_code "Cube Code"
label var dummy_google "Google"
label var dummy_serv_eth_support "Eth Support"
label var dummy_dyno_security_ab "Dyno Security Lab"
label var dummy_chainsafe_systems "Chain Safe Systems"


// summary stats

tabstat n_author tw_follower gh_follower total_commit author_commit eip_contributors besu_commits erigon_commits geth_commits nethermind_commits betweenness, ///
  statistics(N mean median sd p1 p5 p25 p75 p95 p99 min max) format(%12.2gc) save

  
  asdoc tabstat orginal_twitterfollower original_gfollower discussion_length n_author betweenness mode_sentiment mean_sentiment DN, ///
  statistics(N mean median sd p1 p5 p25 p75 p95 p99 min max) format(%12.4gc) varwidth(25) replace

list
  
// Individual Factors
// following are ols results probit specifications are in the end

eststo clear
eststo : quietly reg success log_gh
eststo : quietly reg success log_tw
eststo : quietly reg success n_author
eststo : quietly reg success betweenness
eststo : quietly reg success total_commit
eststo : quietly reg success author_commit
eststo : quietly reg success eip_contributors
eststo : quietly reg success log_gh log_tw betweenness n_author total_commit author_commit eip_contributors
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title(" Individual Factors Associated with Success of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace

eststo clear
eststo : quietly reg success log_gh log_tw
eststo : quietly reg success n_author  total_commit author_commit eip_contributors
eststo : quietly reg success betweenness
eststo : quietly reg success pc1_social pc1_authors betweenness
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title(" Individual Factors Associated with Success of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace

// create pc1

pca log_gh log_tw n_author total_commit author_commit eip_contributors
predic pc1_authors, score


eststo clear
eststo : quietly reg implementation log_gh log_tw
eststo : quietly reg implementation n_author  total_commit author_commit eip_contributors
eststo : quietly reg implementation betweenness
eststo : quietly reg implementation pc1_social pc1_authors betweenness
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title(" Individual Factors Associated with implementation of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace



eststo clear
eststo : quietly reg implementation log_gh 
eststo : quietly reg implementation log_tw
eststo : quietly reg implementation n_author
eststo : quietly reg implementation betweenness
eststo : quietly reg implementation total_commit
eststo : quietly reg implementation author_commit
eststo : quietly reg implementation eip_contributors
eststo : quietly reg implementation log_gh log_tw betweenness n_author total_commit author_commit eip_contributors
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title(" Individual Factors Associated with implementation of EIP") star (* .1 ** .05 *** .01) replace
 
 
 // client involvement
 
eststo clear
eststo : quietly reg success besu_commits
eststo : quietly reg success geth_commits
eststo : quietly reg success erigon_commits
eststo : quietly reg success nethermind_commits
eststo : quietly reg success  besu_commits geth_commits erigon_commits nethermind_commits
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title("Author Engagement on Client Commits Associated with Success of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace

eststo clear
eststo : quietly reg implementation besu_commits
eststo : quietly reg implementation geth_commits
eststo : quietly reg implementation erigon_commits
eststo : quietly reg implementation nethermind_commits
eststo : quietly reg implementation  besu_commits geth_commits erigon_commits nethermind_commits
esttab ,  varwidth(35) modelwidth(10) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2(2) r2(2) title("Author Engagement on Client Commits Associated with implementation of EIP") star (* .1 ** .05 *** .01) replace
 

// company 



label var dummy_spearbit_labs "Spearbit"
label var dummy_ethereum_name_service "Ethereum Name Service"
label var dummy_consensys "ConsenSys"
label var dummy_stoneshot "Stoneshot"
label var dummy_cube_code "Cube Code"
label var dummy_google "Google"
label var dummy_serv_eth_support "Eth Support"
label var dummy_dyno_security_ab "Dyno Security Lab"
label var dummy_chainsafe_systems "Chain Safe Systems"

eststo clear
eststo : quietly reg success dummy_spearbit_labs
eststo : quietly reg success dummy_ethereum_name_service
eststo : quietly reg success dummy_consensys
eststo : quietly reg success dummy_stoneshot
eststo : quietly reg success dummy_cube_code
eststo : quietly reg success dummy_google
eststo : quietly reg success dummy_serv_eth_support
eststo : quietly reg success dummy_dyno_security_ab
eststo : quietly reg success dummy_chainsafe_systems
eststo : quietly reg success dummy_spearbit_labs dummy_ethereum_name_service dummy_consensys dummy_stoneshot dummy_cube_code dummy_serv_eth_support dummy_google dummy_dyno_security_ab dummy_chainsafe_systems
esttab ,  varwidth(20) modelwidth(8) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2 r2(2) title("Author's Employer Associated with success of EIP to Reach Final Stage") star (* .1 ** .05 *** .01) replace

eststo clear
eststo : quietly reg implementation dummy_spearbit_labs
eststo : quietly reg implementation dummy_ethereum_name_service
eststo : quietly reg implementation dummy_consensys
eststo : quietly reg implementation dummy_stoneshot
eststo : quietly reg implementation dummy_cube_code
eststo : quietly reg implementation dummy_google
eststo : quietly reg implementation dummy_serv_eth_support
eststo : quietly reg implementation dummy_dyno_security_ab
eststo : quietly reg implementation dummy_chainsafe_systems
eststo : quietly reg implementation dummy_spearbit_labs dummy_ethereum_name_service dummy_consensys dummy_stoneshot dummy_cube_code dummy_serv_eth_support dummy_google dummy_dyno_security_ab dummy_chainsafe_systems
esttab ,  varwidth(20) modelwidth(8) b(4) nobaselevels noomitted interaction(" X ") depvars label ar2 r2(2) title("Author's Employer Associated with implementation of EIP") star (* .1 ** .05 *** .01) replace


