CREATE DATABASE IF NOT EXISTS cryptware;
USE cryptware;
-- SET GLOBAL wait_timeout = 300;       -- Set to 5 minutes
-- SET GLOBAL interactive_timeout = 300;  -- Set to 5 minutes

ALTER TABLE TOKEN_PAIRS MODIFY liquidity_base Float(28); 
-- WARNING: DELETES EVERYTHING
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;
DROP TABLE IF EXISTS PAIR_SOCIALS;
DROP TABLE IF EXISTS PAIR_WEBSITES;
DROP TABLE IF EXISTS PAIR_INFO;
DROP TABLE IF EXISTS PAIR_LABELS;
DROP TABLE IF EXISTS TOKEN_PAIRS;
DROP TABLE IF EXISTS BASE_TOKENS;
DROP TABLE IF EXISTS QUOTE_TOKENS;
DROP TABLE IF EXISTS TOKENS;
SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;

CREATE TABLE IF NOT EXISTS TOKENS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    url TEXT,                                           
    chain_id VARCHAR(255),                              
    token_address VARCHAR(255) UNIQUE NOT NULL,         
    icon TEXT,                                          
    header TEXT,                                        
    description TEXT,                                   
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   
);

CREATE TABLE IF NOT EXISTS TOKEN_LINKS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    token_id INT NOT NULL,                               
    type TEXT,
    label TEXT,
    url TEXT,
    FOREIGN KEY (token_id) REFERENCES TOKENS (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TOKEN_PAIRS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    token_id INT NOT NULL,                              
    chain_id VARCHAR(255),                              
    dex_id VARCHAR(255),                                
    pair_address VARCHAR(255),                          
    price_native DECIMAL(20, 10),                       
    price_usd DECIMAL(20, 10),                          
    liquidity_usd DECIMAL(20, 2),                       
    liquidity_base Float(28),                     
    liquidity_quote Float(20),  -- Try changing to (20, 6)                  
    fdv BIGINT,                                         
    market_cap BIGINT,                                  
    url TEXT,                                           
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    FOREIGN KEY (token_id) REFERENCES TOKENS (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS BASE_TOKENS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    address VARCHAR(255) UNIQUE NOT NULL,               
    name VARCHAR(255),                                  
    symbol VARCHAR(50)   
);

CREATE TABLE IF NOT EXISTS QUOTE_TOKENS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    address VARCHAR(255) UNIQUE NOT NULL,               
    name VARCHAR(255),                                  
    symbol VARCHAR(50),                                 
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   
);

CREATE TABLE IF NOT EXISTS PAIR_LABELS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    pair_id INT NOT NULL,                               
    label VARCHAR(255),  
    FOREIGN KEY (pair_id) REFERENCES TOKEN_PAIRS (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PAIR_INFO (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    pair_id INT NOT NULL,                               
    image_url TEXT,                                     
    FOREIGN KEY (pair_id) REFERENCES TOKEN_PAIRS (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PAIR_WEBSITES (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    pair_id INT NOT NULL,                               
    url TEXT,                                           
    FOREIGN KEY (pair_id) REFERENCES TOKEN_PAIRS (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PAIR_SOCIALS (
    id INT AUTO_INCREMENT PRIMARY KEY,                  
    pair_id INT NOT NULL,                               
    platform VARCHAR(255),                              
    handle VARCHAR(255),                                
    FOREIGN KEY (pair_id) REFERENCES TOKEN_PAIRS (id) ON DELETE CASCADE
);

select * from tokens
