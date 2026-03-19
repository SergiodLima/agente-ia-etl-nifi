CREATE DATABASE db_automacao_ia;
USE db_automacao_ia;

CREATE TABLE tb_posts_tecnologia (
    id INT PRIMARY KEY,
    userId INT,
    title VARCHAR(255),
    body TEXT,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);