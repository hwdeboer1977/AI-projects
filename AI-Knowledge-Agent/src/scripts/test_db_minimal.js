import pg from "pg";

console.log("Running minimal DB test...");

const pool = new pg.Pool({
  host: "127.0.0.1",
  port: 5433,
  user: "postgres",
  password: "postgres",
  database: "ragdb",
  ssl: false,
});

const res = await pool.query("SELECT NOW() as now");
console.log("DB OK:", res.rows[0]);

process.exit(0);
