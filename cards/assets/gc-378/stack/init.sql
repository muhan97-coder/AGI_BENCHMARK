-- gc-378 SEALED schema seed. Do not modify this file.
CREATE TABLE items (
    id serial PRIMARY KEY,
    sku text NOT NULL,
    qty integer NOT NULL DEFAULT 0
);
INSERT INTO items (sku, qty) VALUES ('alpha', 3), ('bravo', 5), ('charlie', 8);
