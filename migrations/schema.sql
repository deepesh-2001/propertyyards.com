-- DeliverIQ — MySQL Schema
-- Run: mysql -u root -p delivery_db < schema.sql

CREATE DATABASE IF NOT EXISTS delivery_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE delivery_db;

CREATE TABLE IF NOT EXISTS warehouses (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    city        VARCHAR(100) DEFAULT 'Delhi',
    latitude    DOUBLE NOT NULL,
    longitude   DOUBLE NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    phone        VARCHAR(15),
    warehouse_id INT NOT NULL,
    is_active    TINYINT(1) DEFAULT 1,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS agent_checkins (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    agent_id     INT NOT NULL,
    checkin_date DATE NOT NULL,
    checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_available TINYINT(1) DEFAULT 1,
    UNIQUE KEY uq_agent_date (agent_id, checkin_date),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    order_number     VARCHAR(50) NOT NULL UNIQUE,
    customer_name    VARCHAR(100),
    customer_phone   VARCHAR(15),
    delivery_address TEXT,
    latitude         DOUBLE NOT NULL,
    longitude        DOUBLE NOT NULL,
    warehouse_id     INT NOT NULL,
    weight_kg        DOUBLE DEFAULT 1.0,
    status           VARCHAR(20) DEFAULT 'pending',
    scheduled_date   DATE NOT NULL,
    deferred_count   INT DEFAULT 0,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status_date (status, scheduled_date),
    INDEX idx_warehouse (warehouse_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    agent_id          INT NOT NULL,
    order_id          INT NOT NULL,
    assignment_date   DATE NOT NULL,
    distance_km       DOUBLE,
    estimated_minutes DOUBLE,
    sequence          INT,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_date (agent_id, assignment_date),
    INDEX idx_order (order_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (order_id)  REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS allocation_runs (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    run_date             DATE NOT NULL,
    run_time             DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_agents         INT DEFAULT 0,
    total_orders         INT DEFAULT 0,
    assigned_orders      INT DEFAULT 0,
    deferred_orders      INT DEFAULT 0,
    total_cost           DOUBLE DEFAULT 0,
    avg_orders_per_agent DOUBLE DEFAULT 0,
    avg_km_per_agent     DOUBLE DEFAULT 0,
    status               VARCHAR(20) DEFAULT 'completed',
    INDEX idx_run_date (run_date)
);
