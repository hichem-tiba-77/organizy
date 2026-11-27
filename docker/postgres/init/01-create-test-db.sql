-- Executed by the postgres image only when the data volume is first created.
-- Tests run against this separate database so they never touch dev data.
CREATE DATABASE organizy_test;
