import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { fetchHealthData } from '../api';
import './HealthDashboard.css';

// Utility functions
const formatDate = (dateStr) => {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
};

const shortDate = (dateStr) => {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { weekday: 'short' });
};

const calcRemaining = (actual, target) => target - actual;
const calcProgress = (actual, target) => Math.min((actual / target) * 100, 100);

export default function HealthDashboard() {
  const [data, setData] = useState([]);
  const [targets, setTargets] = useState({ calories: 2130, protein: 160, fat: 60, carbs: 240 });
  const [selectedDay, setSelectedDay] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchHealthData(7);
        
        // Transform API response to component format
        const transformedData = response.data.map(day => ({
          date: day.date,
          calories: day.nutrition.calories,
          protein: day.nutrition.protein,
          carbs: day.nutrition.carbs,
          fat: day.nutrition.fat,
          minutes: day.exercise.minutes,
          sessions: day.exercise.sessions,
          types: day.exercise.types,
        }));
        
        setData(transformedData);
        setTargets(response.targets);
        setSelectedDay(transformedData.length - 1); // Select most recent day
      } catch (err) {
        console.error('Failed to fetch health data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="dashboard loading-state">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading health data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard error-state">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <h2>Failed to load data</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="dashboard empty-state">
        <p>No health data available</p>
      </div>
    );
  }

  const todayData = data[selectedDay];
  
  // Combine data for charts
  const chartData = data.map((d) => ({
    ...d,
    shortDate: shortDate(d.date),
    exerciseMinutes: d.minutes || 0,
  }));
  
  // Calculate 7-day averages
  const avgCalories = Math.round(data.reduce((a, b) => a + b.calories, 0) / data.length);
  const avgProtein = Math.round(data.reduce((a, b) => a + b.protein, 0) / data.length);
  const avgExercise = Math.round(data.reduce((a, b) => a + b.minutes, 0) / data.length);
  const daysLogged = data.filter(d => d.calories > 0).length;

  const calorieProgress = calcProgress(todayData.calories, targets.calories);
  const calorieRemaining = calcRemaining(todayData.calories, targets.calories);
  const circumference = 2 * Math.PI * 42;

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          <div className="header-icon">⚡</div>
          <h1>Health Tracker</h1>
        </div>
        <p className="header-date">{formatDate(todayData.date)}</p>
      </header>
      
      <main className="main">
        {/* Day Selector */}
        <div className="day-selector-container">
          {data.map((day, i) => (
            <div
              key={day.date}
              className={`day-selector ${i === selectedDay ? 'active' : ''}`}
              onClick={() => setSelectedDay(i)}
            >
              <div className="day-selector-weekday">{shortDate(day.date)}</div>
              <div className="day-selector-date">{new Date(day.date).getDate()}</div>
            </div>
          ))}
        </div>
        
        {/* Main Stats Grid */}
        <div className="stats-grid">
          {/* Calories Card */}
          <div className="card">
            <div className="stat-label">Calories</div>
            <div className="calories-content">
              <svg width="100" height="100" viewBox="0 0 100 100">
                <circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeWidth="8"
                />
                <circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke="url(#calorieGradient)"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={circumference * (1 - calorieProgress / 100)}
                  transform="rotate(-90 50 50)"
                  className="progress-ring"
                />
                <defs>
                  <linearGradient id="calorieGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#f97316" />
                    <stop offset="100%" stopColor="#fbbf24" />
                  </linearGradient>
                </defs>
                <text x="50" y="50" textAnchor="middle" dominantBaseline="middle" fill="#fff" fontSize="16" fontWeight="700">
                  {Math.round(calorieProgress)}%
                </text>
              </svg>
              <div className="calories-info">
                <div className="stat-value calories-value">
                  {todayData.calories.toLocaleString()}
                </div>
                <div className="calories-target">
                  of {targets.calories.toLocaleString()} kcal
                </div>
                <div className={`calories-remaining ${calorieRemaining > 0 ? 'positive' : 'negative'}`}>
                  {calorieRemaining > 0 
                    ? `${Math.round(calorieRemaining)} remaining`
                    : `${Math.abs(Math.round(calorieRemaining))} over`
                  }
                </div>
              </div>
            </div>
          </div>
          
          {/* Macros Card */}
          <div className="card">
            <div className="stat-label">Macros</div>
            {[
              { name: 'Protein', value: todayData.protein, target: targets.protein, color: '#818cf8', unit: 'g' },
              { name: 'Carbs', value: todayData.carbs, target: targets.carbs, color: '#34d399', unit: 'g' },
              { name: 'Fat', value: todayData.fat, target: targets.fat, color: '#fb923c', unit: 'g' },
            ].map((macro, i) => (
              <div key={macro.name} className={`macro-item ${i < 2 ? 'with-margin' : ''}`}>
                <div className="macro-header">
                  <span style={{ color: macro.color }}>{macro.name}</span>
                  <span className="macro-values">
                    {Math.round(macro.value)}{macro.unit} / {macro.target}{macro.unit}
                  </span>
                </div>
                <div className="macro-bar">
                  <div 
                    className="macro-fill"
                    style={{ 
                      width: `${calcProgress(macro.value, macro.target)}%`,
                      background: macro.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
          
          {/* Exercise Card */}
          <div className="card">
            <div className="stat-label">Exercise</div>
            <div className="stat-value exercise-value">
              {todayData.minutes} <span className="exercise-unit">min</span>
            </div>
            <div className="exercise-sessions">
              {todayData.sessions} session{todayData.sessions !== 1 ? 's' : ''}
            </div>
            {Object.keys(todayData.types || {}).length > 0 ? (
              <div className="exercise-types">
                {Object.entries(todayData.types).map(([type, count]) => (
                  <span key={type} className="exercise-tag">
                    {type} ×{count}
                  </span>
                ))}
              </div>
            ) : (
              <div className="rest-day">Rest day 😴</div>
            )}
          </div>
        </div>
        
        {/* Charts Section */}
        <div className="charts-grid">
          {/* Calories Trend */}
          <div className="card">
            <div className="stat-label">7-Day Calorie Trend</div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <XAxis 
                  dataKey="shortDate" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
                />
                <YAxis hide domain={['dataMin - 200', 'dataMax + 200']} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(0,0,0,0.9)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="calories" 
                  stroke="#fbbf24" 
                  strokeWidth={2}
                  dot={{ fill: '#fbbf24', strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, fill: '#fbbf24' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          {/* Exercise Minutes */}
          <div className="card">
            <div className="stat-label">Exercise Minutes</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData}>
                <XAxis 
                  dataKey="shortDate" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(0,0,0,0.9)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
                />
                <Bar dataKey="exerciseMinutes" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`}
                      fill={entry.exerciseMinutes > 0 ? '#22d3ee' : 'rgba(255,255,255,0.1)'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* Weekly Summary */}
        <div className="card">
          <div className="stat-label">📈 Weekly Summary</div>
          <div className="summary-grid">
            {[
              { label: 'Days Logged', value: `${daysLogged}/${data.length}`, color: '#a855f7' },
              { label: 'Avg Calories', value: avgCalories.toLocaleString(), sub: 'kcal/day', color: '#fbbf24' },
              { label: 'Avg Protein', value: `${avgProtein}g`, sub: '/day', color: '#818cf8' },
              { label: 'Avg Exercise', value: `${avgExercise}`, sub: 'min/day', color: '#22d3ee' },
            ].map((stat) => (
              <div key={stat.label} className="summary-item">
                <div className="stat-label">{stat.label}</div>
                <div className="summary-value" style={{ color: stat.color }}>
                  {stat.value}
                  {stat.sub && <span className="summary-sub">{stat.sub}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Footer */}
        <footer className="footer">
          <p>Powered by health-analysis-agent.py • Data from Google Sheets</p>
        </footer>
      </main>
    </div>
  );
}
