CREATE DATABASE  SuperSelectD;
USE SuperSelectD;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    tipo ENUM('cliente', 'administrador') DEFAULT 'cliente',
    cpf VARCHAR(14) UNIQUE
);

-- Inserindo 10 clientes
INSERT INTO usuarios (nome, email, senha, cpf, tipo) VALUES
('Daniel Colares', 'daniel@example.com', '123456', '123.456.789-00', 'administrador'),
('Maria Souza', 'maria@example.com', 'senha123', '987.654.321-00', 'cliente'),
('João Lima', 'joao@example.com', 'abc123', '111.222.333-44', 'cliente'),
('Ana Beatriz', 'ana@example.com', 'senha456', '555.666.777-88', 'cliente'),
('Carlos Mendes', 'carlos@example.com', 'qwerty', '999.888.777-66', 'cliente'),
('Fernanda Alves', 'fernanda@example.com', 'senha789', '444.333.222-11', 'cliente'),
('Ricardo Silva', 'ricardo@example.com', 'minhaSenha', '222.333.444-55', 'cliente'),
('Patrícia Gomes', 'patricia@example.com', 'abc456', '777.666.555-44', 'cliente'),
('Eduardo Nogueira', 'eduardo@example.com', 'teste123', '888.777.666-55', 'cliente'),
('Luana Freitas', 'luana@example.com', 'curso2025', '999.000.111-22', 'cliente');

SELECT * FROM usuarios;

CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    marca VARCHAR(100) NOT NULL,
    tipo VARCHAR(50),
    preco DECIMAL(10,2) NOT NULL,
    link VARCHAR(255)
);


INSERT INTO produtos (nome, marca, tipo, preco, link) VALUES
('Refrigerante Cola', 'Coca-Cola', 'Carbonatada', 5.50, 'https://example.com/img/coca-cola.jpg'),
('Suco de Laranja', 'Del Valle', 'Natural', 7.20, 'https://example.com/img/suco-laranja.jpg'),
('Água Mineral', 'Crystal', 'Sem gás', 3.00, 'https://example.com/img/agua-crystal.jpg');

SELECT * FROM produtos;

CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT,
    texto TEXT,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
INSERT INTO comentarios (produto_id, texto)
VALUES (1, 'Produto excelente! Chegou rápido e bem embalado.');

SELECT * FROM comentarios;

SELECT c.id, p.nome, c.texto, c.data_hora
FROM comentarios c
JOIN produtos p ON c.produto_id = p.id;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '12345';
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '12345';
FLUSH PRIVILEGES;

FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '12345';
FLUSH PRIVILEGES;

SHOW DATABASES;
USE SuperSelectD;
SHOW TABLES;







