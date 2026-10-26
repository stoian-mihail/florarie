-- Lab 3, Task 2: userul cu care aplicatia Django se conecteaza la baza de date
-- Rulare: psql -d postgres -f creare_user.sql   (ca superuser PostgreSQL)

CREATE USER florarie_user WITH PASSWORD 'florarie_parola';

CREATE DATABASE florarie OWNER florarie_user ENCODING 'UTF8';

GRANT ALL PRIVILEGES ON DATABASE florarie TO florarie_user;
