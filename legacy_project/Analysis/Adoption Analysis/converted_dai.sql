/* Forked from 0xjesse */
WITH list AS (
  SELECT
    0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7 AS wallet,
    'Dex' AS wallet_type,
    'Curve' AS protocol
  UNION ALL
  SELECT
    0xa929022c9107643515f5c777ce9a910f0d1e490c AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x23ddd3e3692d1861ed57ede224608875809e127f AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x3ed3b47dd13ec9a98b44e6204a523e766b225811 AS wallet,
    'Lending' AS wallet_type,
    'Aave' AS protocol
  UNION ALL
  SELECT
    0xe78388b4ce79068e89bf8aa7f218ef6b9ab0e9d0 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xcee284f754e854890e311e3280b767f80797180d AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9 AS wallet,
    'Lending' AS wallet_type,
    'Compound' AS protocol
  UNION ALL
  SELECT
    0x78605df79524164911c144801f41e9811b7db73d AS wallet,
    'Other' AS wallet_type,
    'Treasury' AS protocol
  UNION ALL
  SELECT
    0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a AS wallet,
    'Other' AS wallet_type,
    'Other' AS protocol
  UNION ALL
  SELECT
    0x3416cf6c708da44db2624d63ea0aaef7113527c6 AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852 AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x075e72a5edf65f0a5f44699c7654c1a76941ddc8 AS wallet,
    'Other' AS wallet_type,
    'Other' AS protocol
  UNION ALL
  SELECT
    0xc564ee9f21ed8a2d8e7e76c085740d5e4c5fafbe AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xba12222222228d8ba445958a75a0704d566bf2c8 AS wallet,
    'Lending' AS wallet_type,
    'Balancer' AS protocol
  UNION ALL
  SELECT
    0x1bf68a9d1eaee7826b3593c20a0ca93293cb489a AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x4e68ccd3e89f51c3074ca5072bbac773960dfa36 AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0xa5407eae9ba41422680e2e00537571bcc53efbfd AS wallet,
    'Dex' AS wallet_type,
    'Curve' AS protocol
  UNION ALL
  SELECT
    0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xa21ed0af81d7cdaebd06d1150c166821cfcd64ff AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x06da0fd433c1a5d7a4faa01111c044910a184553 AS wallet,
    'Dex' AS wallet_type,
    'Sushiswap' AS protocol
  UNION ALL
  SELECT
    0x99c9fc46f92e8a1c0dec1b1747d010903e884be1 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x3ee18b2214aff97000d974cf647e7c347e8fa585 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x61b62c5d56ccd158a38367ef2f539668a06356ab AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x10c6b61dbf44a083aec3780acf769c77be747e23 AS wallet,
    'Other' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x2dccdb493827e15a5dc8f8b72147e6c4a5620857 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x12ed69359919fc775bc2674860e8fe2d2b6a7b5d AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xec4486a90371c9b66f499ff3936f29f0d5af8b7e AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x3041cbd36888becc7bbcbc0045e3b1f144466f5f AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x306121f1344ac5f84760998484c0176d7bfb7134 AS wallet,
    'Other' AS wallet_type,
    'Other' AS protocol
  UNION ALL
  SELECT
    0x8aff5ca996f77487a4f04f1ce905bf3d27455580 AS wallet,
    'Other' AS wallet_type,
    'Other' AS protocol
  UNION ALL
  SELECT
    0x79d89b87468a59b9895b31e3a373dc5973d60065 AS wallet,
    'Lending' AS wallet_type,
    'Bancor' AS protocol
  UNION ALL
  SELECT
    0x5d22045daceab03b158031ecb7d9d06fad24609b AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x5427fefa711eff984124bfbb1ab6fbf5e3da1820 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xabea9132b05a70803a4e85094fd0e1800777fbef AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xc2a856c3aff2110c1171b8f942256d40e980c726 AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x7858e59e0c01ea06df3af3d20ac7b0003275d4bf AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x83f798e925bcd4017eb265844fddabb448f1707d AS wallet,
    'Other' AS wallet_type,
    'Yearn' AS protocol
  UNION ALL
  SELECT
    0xc5af84701f98fa483ece78af83f11b6c38aca71d AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x2eb8f5708f238b0a2588f044ade8dea7221639ab AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x3dfd23a6c5e8bbcfc9581d2e864a68feb6a076d3 AS wallet,
    'Lending' AS wallet_type,
    'Aave' AS protocol
  UNION ALL
  SELECT
    0xf8f12fe1b51d1398019c4facd4d00adab5fef746 AS wallet,
    'Other' AS wallet_type,
    'Other' AS protocol
  UNION ALL
  SELECT
    0xf4b00c937b4ec4bb5ac051c3c719036c668a31ec AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x3e4a3a4796d16c0cd582c382691998f7c06420b6 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x55d31f68975e446a40a2d02ffa4b0e1bfb233c2f AS wallet,
    'Dex' AS wallet_type,
    'Sushiswap' AS protocol
  UNION ALL
  SELECT
    0xdc1664458d2f0b6090bea60a8793a4e66c2f1c00 AS wallet,
    'Bridge' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xb20bd5d04be54f870d5c0d3ca85d82b34b836405 AS wallet,
    'Dex' AS wallet_type,
    'Uniswap' AS protocol
  UNION ALL
  SELECT
    0x22648c12acd87912ea1710357b1302c6a4154ebc AS wallet,
    'Other' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0x355d72fb52ad4591b2066e43e89a7a38cf5cb341 AS wallet,
    'Other' AS wallet_type,
    'Treasury' AS protocol
  UNION ALL
  SELECT
    0x88a69b4e698a4b090df6cf5bd7b2d47325ad30a3 AS wallet,
    'Other' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xec4486a90371c9b66f499ff3936f29f0d5af8b7e AS wallet,
    'Other' AS wallet_type,
    'Bridge' AS protocol
  UNION ALL
  SELECT
    0xD51a44d3FaE010294C616388b506AcdA1bfAAE46 AS wallet,
    'Other' AS wallet_type,
    'Curve' AS protocol
  UNION ALL
  SELECT
    0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C AS wallet,
    'Other' AS wallet_type,
    'Curve' AS protocol
  UNION ALL SELECT 0x5d3a536e4d6dbd6114cc1ead35777bab948e3643 AS wallet, 'Other' AS wallet_type, 'Compound' AS protocol
  UNION ALL SELECT 0x5777d92f208679db4b9778590fa3cab3ac9e2168 AS wallet, 'Other' AS wallet_type, 'Uniswap' AS protocol
  UNION ALL SELECT 0x028171bca77440897b824ca71d1c56cac55b68a3 AS wallet, 'Other' AS wallet_type, 'Aave' AS protocol
  UNION ALL SELECT 0x6c6bc977e13df9b0de53b251522280bb72383700 AS wallet, 'Other' AS wallet_type, 'Uniswap' AS protocol
  UNION ALL SELECT 0xae461ca67b15dc8dc81ce7615e0320da1a9ab8d5 AS wallet, 'Other' AS wallet_type, 'Uniswap' AS protocol
  UNION ALL SELECT 0xa10c7ce4b876998858b1a9e12b10092229539400 AS wallet, 'Other' AS wallet_type, 'Bridge' AS protocol
  UNION ALL SELECT 0x649765821d9f64198c905ec0b2b037a4a52bc373 AS wallet, 'Other' AS wallet_type, 'Bancor' AS protocol
  UNION ALL SELECT 0x055475920a8c93cffb64d039a8205f7acc7722d3 AS wallet, 'Other' AS wallet_type, 'Sushiswap' AS protocol
  UNION ALL SELECT 0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f AS wallet, 'Other' AS wallet_type, 'Sushiswap' AS protocol
  UNION ALL SELECT 0x1e0447b19bb6ecfdae1e4ae1694b0c3659614e4e AS wallet, 'Other' AS wallet_type, 'dydx' AS protocol
  UNION ALL SELECT 0xacd43e627e64355f1861cec6d3a6688b31a6f952 AS wallet, 'Other' AS wallet_type, 'Yearn' AS protocol
  UNION ALL SELECT 0xfb76e9be55758d0042e003c1e46e186360f0627e AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
  UNION ALL SELECT 0xce4a1e86a5c47cd677338f53da22a91d85cab2c9 AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
  UNION ALL SELECT 0xffe6280ae4e864d9af836b562359fd828ece8020 AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
  UNION ALL SELECT 0x31f8cc382c9898b273eff4e0b7626a6987c846e8 AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
  UNION ALL SELECT 0xf92cd566ea4864356c5491c177a430c222d7e678 AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
  UNION ALL SELECT 0x1cf0df2a5a20cd61d68d4489eebbf85b8d39e18a AS wallet, 'Other' AS wallet_type, 'Treasury' AS protocol
), transfers AS (
  SELECT
    evt_block_time,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Curve'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Curve'
      )
      THEN -value
    END AS Curve,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Bridge'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Bridge'
      )
      THEN -value
    END AS Bridge,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Aave'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Aave'
      )
      THEN -value
    END AS Aave,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Compound'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Compound'
      )
      THEN -value
    END AS Compound,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Treasury'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Treasury'
      )
      THEN -value
    END AS Treasury,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Other'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Other'
      )
      THEN -value
    END AS Other,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Uniswap'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Uniswap'
      )
      THEN -value
    END AS Uniswap,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Balancer'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Balancer'
      )
      THEN -value
    END AS Balancer,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Sushiswap'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Sushiswap'
      )
      THEN -value
    END AS Sushiswap,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Bancor'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Bancor'
      )
      THEN -value
    END AS Bancor,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Yearn'
      )
      THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT
          wallet
        FROM list
        WHERE
          protocol = 'Yearn'
      )
      THEN -value
    END AS Yearn,
    CASE
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr.to IN (
        SELECT 
          wallet
        FROM list 
        WHERE 
          protocol = 'dydx'
        ) 
       THEN value
      WHEN tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
      AND tr."from" IN (
        SELECT 
        wallet 
        FROM list
        WHERE 
          protocol = 'dydx'
        ) 
        THEN -value
    END AS dydx
  FROM erc20_ethereum.evt_Transfer AS tr
  WHERE
    (
      tr.to IN (
        SELECT
          wallet
        FROM list
      )
      OR tr."from" IN (
        SELECT
          wallet
        FROM list
      )
      AND tr.contract_address = 0x6b175474e89094c44da98b954eedeac495271d0f
    ) 
    
), grouped_transfers AS (
  SELECT
    DATE_TRUNC('day', evt_block_time) AS evt_date,
    SUM(Curve) AS Curve,
    SUM(Bridge) AS Bridge,
    SUM(Aave) AS Aave,
    SUM(Compound) AS Compound,
    SUM(Treasury) AS Treasury,
    SUM(Other) AS Other,
    SUM(Uniswap) AS Uniswap,
    SUM(Balancer) AS Balancer,
    SUM(Sushiswap) AS Sushiswap,
    SUM(Bancor) AS Bancor,
    SUM(Yearn) AS Yearn,
    SUM(dydx) AS dydx
  FROM transfers
  GROUP BY
    1
), data AS (
  SELECT
    evt_date,
    SUM(Curve) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Curve",
    SUM(Bridge) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Bridge",
    SUM(Aave) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Aave",
    SUM(Compound) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Compound",
    SUM(Treasury) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Treasury",
    SUM(Other) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Other",
    SUM(Uniswap) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Uniswap",
    SUM(Balancer) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Balancer",
    SUM(Sushiswap) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Sushiswap",
    SUM(Bancor) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Bancor",
    SUM(Yearn) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "Yearn",
    SUM(dydx) OVER (ORDER BY evt_date) / CAST(1e18 AS DOUBLE) AS "dydx"
  FROM grouped_transfers
)
SELECT
  *
FROM data
WHERE
  evt_date > CAST('2020-09-15' AS TIMESTAMP)