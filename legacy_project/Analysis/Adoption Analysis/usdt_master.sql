-- Forked from 0xjesse
WITH list AS
(
SELECT '\xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7'::bytea AS wallet, 'Dex' AS wallet_type,  'Curve' AS protocol UNION ALL
SELECT '\xa929022c9107643515f5c777ce9a910f0d1e490c'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x23ddd3e3692d1861ed57ede224608875809e127f'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x3ed3b47dd13ec9a98b44e6204a523e766b225811'::bytea AS wallet, 'Lending' AS wallet_type,  'Aave' AS protocol UNION ALL
SELECT '\xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xcee284f754e854890e311e3280b767f80797180d'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9'::bytea AS wallet, 'Lending' AS wallet_type,  'Compound' AS protocol UNION ALL
SELECT '\x78605df79524164911c144801f41e9811b7db73d'::bytea AS wallet, 'Other' AS wallet_type,  'Treasury' AS protocol UNION ALL
SELECT '\x48759f220ed983db51fa7a8c0d2aab8f3ce4166a'::bytea AS wallet, 'Other' AS wallet_type,  'Other' AS protocol UNION ALL
SELECT '\x3416cf6c708da44db2624d63ea0aaef7113527c6'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x0d4a11d5eeaac28ec3f61d100daf4d40471f1852'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x075e72a5edf65f0a5f44699c7654c1a76941ddc8'::bytea AS wallet, 'Other' AS wallet_type,  'Other' AS protocol UNION ALL
SELECT '\xc564ee9f21ed8a2d8e7e76c085740d5e4c5fafbe'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xba12222222228d8ba445958a75a0704d566bf2c8'::bytea AS wallet, 'Lending' AS wallet_type,  'Balancer' AS protocol UNION ALL
SELECT '\x1bf68a9d1eaee7826b3593c20a0ca93293cb489a'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x4e68ccd3e89f51c3074ca5072bbac773960dfa36'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\xa5407eae9ba41422680e2e00537571bcc53efbfd'::bytea AS wallet, 'Dex' AS wallet_type,  'Curve' AS protocol UNION ALL
SELECT '\x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xa21ed0af81d7cdaebd06d1150c166821cfcd64ff'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x06da0fd433c1a5d7a4faa01111c044910a184553'::bytea AS wallet, 'Dex' AS wallet_type,  'Sushiswap' AS protocol UNION ALL
SELECT '\x99c9fc46f92e8a1c0dec1b1747d010903e884be1'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x3ee18b2214aff97000d974cf647e7c347e8fa585'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x61b62c5d56ccd158a38367ef2f539668a06356ab'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x10c6b61dbf44a083aec3780acf769c77be747e23'::bytea AS wallet, 'Other' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x2dccdb493827e15a5dc8f8b72147e6c4a5620857'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x12ed69359919fc775bc2674860e8fe2d2b6a7b5d'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xec4486a90371c9b66f499ff3936f29f0d5af8b7e'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x3041cbd36888becc7bbcbc0045e3b1f144466f5f'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x306121f1344ac5f84760998484c0176d7bfb7134'::bytea AS wallet, 'Other' AS wallet_type,  'Other' AS protocol UNION ALL
SELECT '\x8aff5ca996f77487a4f04f1ce905bf3d27455580'::bytea AS wallet, 'Other' AS wallet_type,  'Other' AS protocol UNION ALL
SELECT '\x79d89b87468a59b9895b31e3a373dc5973d60065'::bytea AS wallet, 'Lending' AS wallet_type,  'Bancor' AS protocol UNION ALL
SELECT '\x5d22045daceab03b158031ecb7d9d06fad24609b'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x5427fefa711eff984124bfbb1ab6fbf5e3da1820'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xabea9132b05a70803a4e85094fd0e1800777fbef'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xc2a856c3aff2110c1171b8f942256d40e980c726'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x7858e59e0c01ea06df3af3d20ac7b0003275d4bf'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x83f798e925bcd4017eb265844fddabb448f1707d'::bytea AS wallet, 'Other' AS wallet_type,  'Yearn' AS protocol UNION ALL
SELECT '\xc5af84701f98fa483ece78af83f11b6c38aca71d'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x2eb8f5708f238b0a2588f044ade8dea7221639ab'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x3dfd23a6c5e8bbcfc9581d2e864a68feb6a076d3'::bytea AS wallet, 'Lending' AS wallet_type,  'Aave' AS protocol UNION ALL
SELECT '\xf8f12fe1b51d1398019c4facd4d00adab5fef746'::bytea AS wallet, 'Other' AS wallet_type,  'Other' AS protocol UNION ALL
SELECT '\xf4b00c937b4ec4bb5ac051c3c719036c668a31ec'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x3e4a3a4796d16c0cd582c382691998f7c06420b6'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x55d31f68975e446a40a2d02ffa4b0e1bfb233c2f'::bytea AS wallet, 'Dex' AS wallet_type,  'Sushiswap' AS protocol UNION ALL
SELECT '\xdc1664458d2f0b6090bea60a8793a4e66c2f1c00'::bytea AS wallet, 'Bridge' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xb20bd5d04be54f870d5c0d3ca85d82b34b836405'::bytea AS wallet, 'Dex' AS wallet_type,  'Uniswap' AS protocol UNION ALL
SELECT '\x22648c12acd87912ea1710357b1302c6a4154ebc'::bytea AS wallet, 'Other' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\x355d72fb52ad4591b2066e43e89a7a38cf5cb341'::bytea AS wallet, 'Other' AS wallet_type,  'Treasury' AS protocol UNION ALL
SELECT '\x88a69b4e698a4b090df6cf5bd7b2d47325ad30a3'::bytea AS wallet, 'Other' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xec4486a90371c9b66f499ff3936f29f0d5af8b7e'::bytea AS wallet, 'Other' AS wallet_type,  'Bridge' AS protocol UNION ALL
SELECT '\xD51a44d3FaE010294C616388b506AcdA1bfAAE46'::bytea AS wallet, 'Other' AS wallet_type,  'Curve' AS protocol UNION ALL
SELECT '\x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C'::bytea AS wallet, 'Other' AS wallet_type,  'Curve' AS protocol 
),

transfers AS 
(SELECT

evt_block_time,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Curve') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Curve') THEN -value END AS Curve,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Bridge') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Bridge') THEN -value END AS Bridge,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Aave') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Aave') THEN -value END AS Aave,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Compound') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Compound') THEN -value END AS Compound,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Treasury') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Treasury') THEN -value END AS Treasury,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Other') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Other') THEN -value END AS Other,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Uniswap') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Uniswap') THEN -value END AS Uniswap,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Balancer') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Balancer') THEN -value END AS Balancer,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Sushiswap') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Sushiswap') THEN -value END AS Sushiswap,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Bancor') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Bancor') THEN -value END AS Bancor,
CASE WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.to IN (SELECT wallet FROM list WHERE protocol = 'Yearn') THEN value WHEN tr.contract_address = '\xdAC17F958D2ee523a2206206994597C13D831ec7' AND tr.from IN (SELECT wallet FROM list WHERE protocol = 'Yearn') THEN -value END AS Yearn

FROM erc20."ERC20_evt_Transfer" tr

WHERE   (tr.to IN (SELECT wallet FROM list) 
    OR tr.from IN (SELECT wallet FROM list )
AND tr.contract_address = --'\x6b175474e89094c44da98b954eedeac495271d0f', -- DAI
                            '\xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48' -- USDC
                            --'\xdac17f958d2ee523a2206206994597c13d831ec7'--USDT
                            )),                   
grouped_transfers AS

(SELECT
    date_trunc('day', evt_block_time) AS evt_date
    ,SUM(Curve) AS Curve
    ,SUM(Bridge) AS Bridge
    ,SUM(Aave) AS Aave
    ,SUM(Compound) AS Compound
    ,SUM(Treasury) AS Treasury
    ,SUM(Other) AS Other
    ,SUM(Uniswap) AS Uniswap 
    ,SUM(Balancer) AS Balancer
    ,SUM(Sushiswap) AS Sushiswap
    ,SUM(Bancor) AS Bancor
    ,SUM(Yearn) AS Yearn
FROM transfers
GROUP BY 1)

, data AS (
SELECT
    evt_date
    ,SUM(Curve) over (order by evt_date) / 1e6 as "Curve"
    ,SUM(Bridge) over (order by evt_date) / 1e6 as "Bridge"
    ,SUM(Aave) over (order by evt_date) / 1e6 as "Aave"
    ,SUM(Compound) over (order by evt_date) / 1e6 as "Compound"
    ,SUM(Treasury) over (order by evt_date) / 1e6 as "Treasury"
    ,SUM(Other) over (order by evt_date) / 1e6 as "Other"
    ,SUM(Uniswap) over (order by evt_date) / 1e6 as "Uniswap"
    ,SUM(Balancer) over (order by evt_date) / 1e6 as "Balancer"
    ,SUM(Sushiswap) over (order by evt_date) / 1e6 as "Sushiswap"
    ,SUM(Bancor) over (order by evt_date) / 1e6 as "Bancor"
    ,SUM(Yearn) over (order by evt_date) / 1e6 as "Yearn"
FROM grouped_transfers
)

SELECT * FROM data
WHERE evt_date > '2020-09-15'