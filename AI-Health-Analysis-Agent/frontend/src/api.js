const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function fetchHealthData(days = 7) {
  const response = await fetch(`${API_BASE}/api/health/${days}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  const json = await response.json();
  if (!json.success) {
    throw new Error(json.error || 'Unknown error');
  }
  return json;
}

export async function fetchTodayData() {
  const response = await fetch(`${API_BASE}/api/health/today`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  const json = await response.json();
  if (!json.success) {
    throw new Error(json.error || 'Unknown error');
  }
  return json;
}

export async function fetchTargets() {
  const response = await fetch(`${API_BASE}/api/targets`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  const json = await response.json();
  if (!json.success) {
    throw new Error(json.error || 'Unknown error');
  }
  return json.targets;
}
