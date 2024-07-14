CREATE TABLE IF NOT EXISTS JOB_TABLE (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(255),
    job_name VARCHAR(255),
    job_run_name VARCHAR(255),
    output_s3_path TEXT,
    job_type VARCHAR(255),
    job_status VARCHAR(255),
    job_create_time DATETIME,
    job_start_time DATETIME,
    job_end_time DATETIME,
    job_payload TEXT,
    ts BIGINT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;