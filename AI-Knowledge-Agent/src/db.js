import pg from "pg";
import dotenv from "dotenv";

dotenv.config();

console.log("DATABASE_URL:", process.env.DATABASE_URL);

export const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
});

export async function query(text, params) {
  return pool.query(text, params);
}

// pgvector accepteert vector input als string: '[0.1,0.2,...]'
export function toPgVector(arr) {
  if (!Array.isArray(arr)) throw new Error("toPgVector expects an array");
  return `[${arr.join(",")}]`;
}
