-- ===========================================
-- Etherscan账户数据导入SQL脚本
-- 直接运行此脚本即可导入所有数据
-- ===========================================

-- 1. 创建数据库（如果不存在）
-- CREATE DATABASE polymarket;
-- CREATE USER predictlab_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE polymarket TO predictlab_user;

-- 2. 连接到数据库
-- \c polymarket

-- 3. 创建表结构
CREATE TABLE IF NOT EXISTS etherscan_accounts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL UNIQUE,
    username VARCHAR(100),
    email VARCHAR(200) UNIQUE,
    password VARCHAR(100),
    api_key VARCHAR(100) UNIQUE NOT NULL,
    proxy_ip VARCHAR(50),
    proxy_port VARCHAR(10),
    proxy_user VARCHAR(50),
    proxy_pass VARCHAR(50),
    daily_used INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 100000,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_etherscan_api_key ON etherscan_accounts(api_key);
CREATE INDEX IF NOT EXISTS idx_etherscan_email ON etherscan_accounts(email);
CREATE INDEX IF NOT EXISTS idx_etherscan_account_id ON etherscan_accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_etherscan_last_used ON etherscan_accounts(last_used);

-- 4. 插入数据
INSERT INTO etherscan_accounts (account_id, username, email, password, api_key, proxy_ip, proxy_port, proxy_user, proxy_pass) VALUES
(1, 'sfesf', 'sdf@gaoxing01.ggff.net', 'yueyan1214', 'QTZZ2KHYZTUHF9QE5FE1HTBDXCYFHPR3YG', '167.100.107.205', '6774', 'xtsgqbla', 'a337l88lug4v'),
(2, 'adsda', 'adsda@gaoxing01.ggff.net', 'yueyan1214', 'R54VRAG5WWBM7RBW3B7X55P8MIHAUGMZTB', '195.40.70.84', '6767', 'xtsgqbla', 'a337l88lug4v'),
(3, 'dgrdwe', 'dgrdwe@gaoxing01.ggff.net', 'yueyan1214', 'JREEQVQP634FE55RAUJX4XHK3QM2FB2RJY', '108.165.87.29', '6492', 'xtsgqbla', 'a337l88lug4v'),
(4, 'efsfw3', 'efsfw3@gaoxing01.ggff.net', 'yueyan1214', '7QREA6S8ZE8YTAG346FMRQ14CKV9SFIXF8', '142.111.67.217', '5682', 'xtsgqbla', 'a337l88lug4v'),
(5, 'sfseg', 'sfseg@gaoxing01.ggff.net', 'yueyan1214', 'FM3WP9N5FXHISVXVBVU3HHV1JNB1D5MCAA', '108.165.181.37', '5500', 'xtsgqbla', 'a337l88lug4v'),
(6, 'zaadw', 'zaadw@gaoxing01.ggff.net', 'yueyan1214', 'AYX25AJCD8ZCF9RRU7DETQJFBV88R3788M', '23.26.47.145', '6611', 'xtsgqbla', 'a337l88lug4v'),
(7, 'sefsf', 'sefsf@gaoxing01.ggff.net', 'yueyan1214', 'MRJ59U6SFXY92Z21BH2PV8F6NIMCD87SKA', '195.40.123.107', '6291', 'xtsgqbla', 'a337l88lug4v'),
(8, 'sfsds', 'sfsds@gaoxing01.ggff.net', 'yueyan1214', 'TQIXKR1VYBPA7KUJ3D846NTIJ8IUX77J5T', '168.199.145.2', '6260', 'xtsgqbla', 'a337l88lug4v'),
(9, 'esfes', 'lceekhjf76931@outlook.com', 'yueyan1214', 'TQ1YUTCXJR3Z5X63147DHAX1MDHVQJC57J', '142.111.67.122', '5587', 'xtsgqbla', 'a337l88lug4v'),
(10, 'wefsf', 'uxxirj4867577@outlook.com', 'yueyan1214', 'R3Q3KJEWXH2I7CWIRBFSTIBRHRJ4IB6A22', '195.40.120.66', '5749', 'xtsgqbla', 'a337l88lug4v'),
(11, 'sfeesef', 'ldwxx185983@outlook.com', 'yueyan1214', 'QKYAZSVC8GY4TRGMA4ZCBHH761Q1THHIZ6', '195.40.120.109', '5792', 'xtsgqbla', 'a337l88lug4v'),
(12, 'afsawe', 'dcoxze7631@outlook.com', 'yueyan1214', 'S5WRIGE4IFS4IV9C4IST27AUGUFTCTEP65', '92.112.94.229', '7703', 'xtsgqbla', 'a337l88lug4v'),
(13, 'rgerfe', 'pqof42549@outlook.com', 'yueyan1214', 'SHYBVG1JYJ43X2GK4X4U1YP2Y367XEZKFW', '195.40.123.85', '6269', 'xtsgqbla', 'a337l88lug4v'),
(14, 'fdsgsqw', 'jbjlzq68588@outlook.com', 'yueyan1214', 'QYDVDWBSK2YE46I2HBNN8KYCY9I9EJ36KV', '108.165.181.53', '5516', 'xtsgqbla', 'a337l88lug4v'),
(15, 'fefsfsg', 'njuwqjf9809276@outlook.com', 'yueyan1214', '8H5F5JSWQB53SF9HWBBIQNQ1Y7PU79SUHP', '108.165.87.241', '6704', 'xtsgqbla', 'a337l88lug4v'),
(16, 'dgdfb32', 'yjwmpzrn1340@outlook.com', 'yueyan1214', 'EFXYGYTFTBCU3RB6CRTDUA8UT84YJGJX59', '195.40.70.52', '6735', 'xtsgqbla', 'a337l88lug4v'),
(17, 'ewsfwfe', 'tohhksgx953307@outlook.com', 'yueyan1214', 'TXSQPXVBHC51MEYB8429NYHAV8JQY9XFDR', '31.57.90.182', '5751', 'xtsgqbla', 'a337l88lug4v'),
(18, 'efrw23', 'tnul50063@outlook.com', 'yueyan1214', 'WJRASUMJEZBMQZ9PZZ8AAKVAH5PEPEIDBZ', '195.172.150.189', '5873', 'xtsgqbla', 'a337l88lug4v'),
(19, 'fghrdr5', 'nezmg59245@outlook.com', 'yueyan1214', 'XXAX3ZWZHP4RYRIS9ZAGJ6T7PAG7FYK7X6', '168.199.145.254', '6512', 'xtsgqbla', 'a337l88lug4v'),
(20, 'ewafger', 'ozivpsjh2324@outlook.com', 'yueyan1214', 'N4VJ62M137A52Q7IYFKZDCGY4B6NN2JGGN', '46.203.52.243', '5766', 'xtsgqbla', 'a337l88lug4v'),
(21, 'regfs3r', 'nmea6988081@outlook.com', 'yueyan1214', 'R7EDYPS7AEK2SVXCJN4GN585ZM2CW71VUZ', '195.172.150.160', '5844', 'xtsgqbla', 'a337l88lug4v'),
(22, 'erhgrht5', 'bzqemh4483760@outlook.com', 'yueyan1214', 'ICZ1A37TNJA653I7WEQJBR29NQ5VDZ3NZB', '92.112.94.110', '7584', 'xtsgqbla', 'a337l88lug4v'),
(23, 'trur6u6', 'fjjhl64834@outlook.com', 'yueyan1214', 'R6B5CAFNKMX3UVRZ8HBE91XBWIWT2GJ87M', '166.88.149.85', '6549', 'xtsgqbla', 'a337l88lug4v'),
(24, 'e45y4y', 'xpmrgq3126972@outlook.com', 'yueyan1214', 'FZXNTDB85TW14A26XMXFIEGI862EQIF6DX', '50.114.92.249', '5713', 'xtsgqbla', 'a337l88lug4v'),
(25, 'wertge4', 'fcste295558@outlook.com', 'yueyan1214', 'JKZMI6BCZ6HFF6A3SKG9NIM1XMTHZUGDC1', '108.165.181.153', '5616', 'xtsgqbla', 'a337l88lug4v'),
(26, 'regesge4', 'ztkxru7131297@outlook.com', 'yueyan1214', '66AFY49MR5C9XXHNJ1CM9TR8VC37S4FV1F', '168.199.145.143', '6401', 'xtsgqbla', 'a337l88lug4v'),
(27, '43543rd', 'bijr1773@outlook.com', 'yueyan1214', 'DB3H8ATAGBKSZD5CWQW3MX6FPYSM6IHTYM', '195.40.123.241', '6425', 'xtsgqbla', 'a337l88lug4v'),
(28, 'trdyu65', 'ajckspq2242470@outlook.com', 'yueyan1214', '2ER9QCDWKXXMWPBUGHTFXH8GZSMSH7WEJG', '195.40.70.253', '6936', 'xtsgqbla', 'a337l88lug4v'),
(29, 'rthyr67', 'wugb572121@outlook.com', 'yueyan1214', '6CE2YJMF63336NZW17FPMUUEJFAM39FH7D', '206.232.74.71', '7141', 'xtsgqbla', 'a337l88lug4v'),
(30, 'dgrwer4', 'kuzs1579@outlook.com', 'yueyan1214', 'UEUFKU8AKY6NSRKJZRRJ8G5MST9W39NQ7T', '92.112.90.83', '7057', 'xtsgqbla', 'a337l88lug4v'),
(31, 'sfewtg', 'nixzg6853@outlook.com', 'yueyan1214', 'Q3ZD5C98DK752AUVW7SIA5E2RTA4HNZAPH', '168.199.145.234', '6492', 'xtsgqbla', 'a337l88lug4v'),
(32, 'eger54t', 'dhgaw4348307@outlook.com', 'yueyan1214', '52BH6RJCSKQN5N8R5GKT5KPXMC25RRKXFJ', '92.112.90.221', '7195', 'xtsgqbla', 'a337l88lug4v'),
(33, 'fdhtr54', 'llimsy3172574@outlook.com', 'yueyan1214', 'JKTJ5QXCX8A5IUVZBES6JXKKRWV2PPEYNW', '195.40.123.249', '6433', 'xtsgqbla', 'a337l88lug4v'),
(34, 'dger4t3t', 'xnzjho2369@outlook.com', 'yueyan1214', 'CXHI7Z8JSQ5E4BTXEPJ7KKQ6Y2P3J71X2D', '166.88.149.211', '6675', 'xtsgqbla', 'a337l88lug4v'),
(35, 'efwe4t45', 'ejol7434382@outlook.com', 'yueyan1214', 'WSC5RK6GAPJ5HUIXUP1DQTDWZIJRBWIJWA', '142.111.67.30', '5495', 'xtsgqbla', 'a337l88lug4v'),
(36, 'werwr43', 'lfyl2422340@outlook.com', 'yueyan1214', '1MUUIZ89NDWM4665PPMQ76ZBP3IZUUMRKE', '92.112.94.118', '7592', 'xtsgqbla', 'a337l88lug4v'),
(37, 'ege45t56', 'lhzn7759@outlook.com', 'yueyan1214', 'YMWY9MID4UBUHU17ID9C1B93RZI6SZAVMX', '195.40.70.221', '6904', 'xtsgqbla', 'a337l88lug4v'),
(38, 'regd3hf', 'ljuwuq66242@outlook.com', 'yueyan1214', '7HZEY5PBCZX52D4TZIJ5W5BWJJ1ANTFEXZ', '50.114.92.138', '5602', 'xtsgqbla', 'a337l88lug4v'),
(39, 'tygreter', 'wuatbju6077171@outlook.com', 'yueyan1214', 'XHTWWZ9X3N81TPWFKTJRAJGFC15GM61TR6', '206.232.74.54', '7124', 'xtsgqbla', 'a337l88lug4v'),
(40, '6yhtfr', 'smblq2479@outlook.com', 'yueyan1214', 'KW7NY51WT9A925B259DTRBG6D9VHFKRBYM', '23.26.47.75', '6541', 'xtsgqbla', 'a337l88lug4v'),
(41, 'tyry6', 'wspnio83113@outlook.com', 'yueyan1214', 'V5U3CBAG6QK9CJD9WXYAERDXWIBY3TUN1H', '46.203.52.156', '5679', 'xtsgqbla', 'a337l88lug4v'),
(42, 'u6u6yg', 'wnvib53069@outlook.com', 'yueyan1214', 'SKWP1F9B4ADZXI9MG8UV1ZFYTPQ14NQDC1', '195.40.123.214', '6398', 'xtsgqbla', 'a337l88lug4v'),
(43, 'retee456', 'vlzs7422@outlook.com', 'yueyan1214', 'BNG223N6K822G2UVK5U6T8PNBY4ZHVIG5V', '161.123.208.212', '6456', 'xtsgqbla', 'a337l88lug4v'),
(44, 'tyjt656', 'roau8430736@outlook.com', 'yueyan1214', 'UHJHSC6PTV8N8PB6HTXU31V9U78BXUID8M', '46.203.52.238', '5761', 'xtsgqbla', 'a337l88lug4v'),
(45, 'ergt5yf', 'illxdzct9553044@outlook.com', 'yueyan1214', 'Q6NJP1B16F8VBHYHFWMKPRAFJ6BAZMVAHZ', '142.111.67.166', '5631', 'xtsgqbla', 'a337l88lug4v'),
(46, 'ytut65', 'uhkeq89712@outlook.com', 'yueyan1214', '8XMQE62PCNG26ZK1Z6VT6BX1KPBQXBBFNF', '206.232.74.206', '7276', 'xtsgqbla', 'a337l88lug4v'),
(47, 'esfsewe', 'wcgwuia3611007@outlook.com', 'yueyan1214', 'PYFRDMAIT4PR8KB6ZN7999EP8GGF5JKIJC', '161.123.208.140', '6384', 'xtsgqbla', 'a337l88lug4v'),
(48, '4eett', 'mjusfm659766@outlook.com', 'yueyan1214', 'SNVBK2EITSWWQZ2BZRFPBEISHX5WE9I56V', '195.40.121.98', '5281', 'xtsgqbla', 'a337l88lug4v'),
(49, 'fgt55', 'ynoulkx65675@outlook.com', 'yueyan1214', 'UTI13NSMNR13EE4D4YJ2FIJF6E313YU1YF', '46.203.52.5', '5528', 'xtsgqbla', 'a337l88lug4v'),
(50, 'trh77', 'kxef7277@outlook.com', 'yueyan1214', 'QSVHIU93JP98GA9626DNZSNXC62938BSW6', '145.223.40.100', '5670', 'xtsgqbla', 'a337l88lug4v'),
(51, 'rtret566', 'kbayscu8998229@outlook.com', 'yueyan1214', 'PQ2AUGJ5UD8BKVD4QVB2S84U2FD77QH94I', '92.112.90.55', '7029', 'xtsgqbla', 'a337l88lug4v'),
(52, 'yrty76', 'aochm6738@outlook.com', 'yueyan1214', 'VINDZQTVIB3HZ3IUF9BDUFK88D4DY4WY72', '195.40.121.253', '5436', 'xtsgqbla', 'a337l88lug4v'),
(53, 'tyut7', 'uscbbn1205398@outlook.com', 'yueyan1214', 'MYA3GVX1I8BJV4M1FZ2K3FZAXUASHVP3K5', '168.199.145.86', '6344', 'xtsgqbla', 'a337l88lug4v'),
(54, 'ehgr6yu7', 'gvof9066479@outlook.com', 'yueyan1214', 'HD21PITYEM5NEJP8X9E24YDE79QB27IS6Y', '108.165.87.126', '6589', 'xtsgqbla', 'a337l88lug4v'),
(55, 'thrhr56y', 'hqbe8555760@outlook.com', 'yueyan1214', 'TYECQQCTN6PCBRJNYSC7E321QMFU5T15VR', '195.172.150.82', '5766', 'xtsgqbla', 'a337l88lug4v'),
(56, 'wefeg', 'plfab15381@outlook.com', 'yueyan1214', 'KQJU5924UQ2R86USWEBTKMNU7M9CU228HJ', '92.112.94.203', '7677', 'xtsgqbla', 'a337l88lug4v'),
(57, 'htfu6t', 'nhpns60755@outlook.com', 'yueyan1214', '9P1YXY3VKKAE85Y8E5UAX736WIA3X5QTBI', '92.112.90.142', '7116', 'xtsgqbla', 'a337l88lug4v'),
(58, 'dfhty6', 'bhlrb8359676@outlook.com', 'yueyan1214', 'PE17UUCCMUT9A4FY19HNX6Q5DPGAX797TE', '50.114.92.189', '5653', 'xtsgqbla', 'a337l88lug4v'),
(59, 'hfhfyt6', 'hgskbusm3438188@outlook.com', 'yueyan1214', 'ZV833ZTP2DEKYCZ4KEJ6Y1AGMMT9VNPXG6', '206.232.74.229', '7299', 'xtsgqbla', 'a337l88lug4v'),
(60, 'dfghfg56', 'ciggxac938053@outlook.com', 'yueyan1214', '3NC1S8HWUYY6EVFDAKTVUTICPZFCJQFGR4', '206.232.74.196', '7266', 'xtsgqbla', 'a337l88lug4v'),
(61, 'fefer455', 'jozyf66617@outlook.com', 'yueyan1214', 'PFXD3IHJE3HWAFQFH41358229V3RVCC2VJ', '161.123.208.159', '6403', 'xtsgqbla', 'a337l88lug4v'),
(62, 'fhyt65', 'slfihhxu9568067@outlook.com', 'yueyan1214', '4AFZ6DRVFHUSNCY9K4E8NUZEM5FWCU7DXQ', '195.40.121.169', '5352', 'xtsgqbla', 'a337l88lug4v'),
(63, 'ewferht', 'mfudwgt9296@outlook.com', 'yueyan1214', 'UHUPJDBTF7SGUGX17TQJFN9Y4RA2DD36MC', '46.203.52.210', '5733', 'xtsgqbla', 'a337l88lug4v'),
(64, 'rth6u', 'dihi421693@outlook.com', 'yueyan1214', 'GZG3WFUNI8BVFM6Q9W42IIFBR768KQK2FB', '108.165.87.156', '6619', 'xtsgqbla', 'a337l88lug4v'),
(65, 'hjkht6', 'stems8016264@outlook.com', 'yueyan1214', 'CWVMMAA15VTEDP4IJZNUHHKT3PSS8SDHGH', '195.40.120.187', '5870', 'xtsgqbla', 'a337l88lug4v'),
(66, 'ghdh765', 'badai38545@outlook.com', 'yueyan1214', '88A92ITW4Q1GJFIZIP41XZQU8DBA5QYDYP', '23.26.47.186', '6652', 'xtsgqbla', 'a337l88lug4v'),
(67, 'dfgd644', 'ejsneweu599858@outlook.com', 'yueyan1214', 'RGYH4CGR159VD4WQHC39BR7B3SIKHNIVKT', '92.112.90.172', '7146', 'xtsgqbla', 'a337l88lug4v'),
(68, 'sfgrtrt4', 'feswe@gaoxing01.ggff.net', 'yueyan1214', 'FZQQMHK3AG28GR56IUBRT9I581XJE7G7QS', '195.40.121.182', '5365', 'xtsgqbla', 'a337l88lug4v'),
(69, 'dsgtdy5', 'rgdryrh@gaoxing01.ggff.net', 'yueyan1214', 'ZFP8ZAV7YG2C18GUHUWIB76SVKSS4S9AWV', '23.26.61.238', '5704', 'xtsgqbla', 'a337l88lug4v'),
(70, 'ewer656', 'rgdyr@gaoxing01.ggff.net', 'yueyan1214', 'NBQMDS8FJWZXGP2AYFQDACQ826WFPJZZZQ', '145.223.40.218', '5788', 'xtsgqbla', 'a337l88lug4v')
ON CONFLICT (account_id) DO UPDATE SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    password = EXCLUDED.password,
    api_key = EXCLUDED.api_key,
    proxy_ip = EXCLUDED.proxy_ip,
    proxy_port = EXCLUDED.proxy_port,
    proxy_user = EXCLUDED.proxy_user,
    proxy_pass = EXCLUDED.proxy_pass,
    updated_at = NOW();

-- 5. 验证导入结果
SELECT
    COUNT(*) as total_accounts,
    COUNT(DISTINCT api_key) as unique_api_keys,
    COUNT(DISTINCT proxy_ip) as unique_proxy_ips
FROM etherscan_accounts;

-- 6. 显示样例数据
SELECT
    account_id,
    username,
    LEFT(email, 25) as email_short,
    LEFT(api_key, 15) || '...' as api_key_short,
    proxy_ip || ':' || proxy_port as proxy
FROM etherscan_accounts
ORDER BY account_id
LIMIT 10;
