CREATE TABLE compliance_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    issue_date DATETIME,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    content_url VARCHAR(2000),
    llm_summary TEXT,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    creation_user VARCHAR(100) NOT NULL
);
