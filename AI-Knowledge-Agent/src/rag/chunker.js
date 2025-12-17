// Simpele, betrouwbare chunker voor MVP.
// Knipt op paragrafen en bouwt chunks tot maxChars, met overlap.
export function chunkText(text, { maxChars = 1600, overlapChars = 200 } = {}) {
  const paragraphs = text
    .replace(/\r\n/g, "\n")
    .split(/\n\s*\n/g)
    .map((p) => p.trim())
    .filter(Boolean);

  const chunks = [];
  let buf = "";

  for (const p of paragraphs) {
    const candidate = buf ? `${buf}\n\n${p}` : p;

    if (candidate.length <= maxChars) {
      buf = candidate;
      continue;
    }

    if (buf) chunks.push(buf);

    // overlap uit vorige chunk meenemen
    const overlap = buf
      ? buf.slice(Math.max(0, buf.length - overlapChars))
      : "";
    buf = overlap ? `${overlap}\n\n${p}` : p;

    // als nog steeds te groot: hard split
    while (buf.length > maxChars) {
      chunks.push(buf.slice(0, maxChars));
      buf = buf.slice(maxChars - overlapChars);
    }
  }

  if (buf) chunks.push(buf);
  return chunks;
}
