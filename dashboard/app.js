/* app.js — Valkey benchmark dashboard for last 100 commits
   Features:
   • Fetch last 100 commit SHAs from completed_commits.json
   • Load metrics.json for each commit in parallel
   • Filter by cluster_mode and tls
   • Display separate trend charts for each command over the last commits
*/

/* global React, ReactDOM, Recharts */

const COMPLETED_URL = "../completed_commits.json";
const RESULT_URL = sha => `../results/${sha}/metrics.json`;

const {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Brush
} = Recharts;

// Utility fetch ---------------------------------------------------------
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

// React root component --------------------------------------------------
function Dashboard() {
  const [commits, setCommits] = React.useState([]);  // full sha[]
  const [metrics, setMetrics] = React.useState([]);  // flat metrics rows
  const [commitTimes, setCommitTimes] = React.useState({});

  const [cluster, setCluster]         = React.useState("all"); // all/true/false
  const [tls, setTLS]                 = React.useState("all"); // all/true/false
  const [metricKey, setMetricKey]     = React.useState("rps");

  // 1) load commit list (once)
  React.useEffect(() => {
    fetchJSON(COMPLETED_URL)
      .then(list => {
        const recent = list.slice(-100);
        const times = {};
        recent.forEach(e => { times[e.sha] = e.timestamp; });
        setCommitTimes(times);
        setCommits(recent.map(e => e.sha));
      })
      .catch(err => {
        console.error('Failed to load commit list:', err);
        setCommits([]);
      });
  }, []);

  const loadMetrics = React.useCallback(async () => {
    if (!commits.length) return;
    const all = [];
    const times = { ...commitTimes };
    await Promise.all(commits.map(async sha => {
      try {
        const rows = await fetchJSON(RESULT_URL(sha));
        rows.forEach(r => all.push({ ...r, sha }));
        if (rows[0] && rows[0].timestamp && !times[sha]) times[sha] = rows[0].timestamp;
      } catch (err) {
        console.error(`Failed to load metrics for ${sha}:`, err);
      }
    }));
    const ordered = [...commits].sort((a,b) => new Date(times[a] || 0) - new Date(times[b] || 0));
    const orderMap = Object.fromEntries(ordered.map((s,i)=>[s,i]));
    all.sort((a,b) => orderMap[a.sha] - orderMap[b.sha]);
    setCommitTimes(times);
    setCommits(ordered);
    setMetrics(all);
  }, [commits, commitTimes]);

  // 2) fetch metrics for each commit
  React.useEffect(() => { if (commits.length) loadMetrics(); }, [commits, loadMetrics]);

  // unique command list
  const commands = React.useMemo(() => [...new Set(metrics.map(m => m.command))].sort(), [metrics]);

  // regroup per command → series of commit metrics
  const seriesByCommand = React.useMemo(() => {
    const map = {};
    commands.forEach(cmd => {
      const rows = metrics.filter(r =>
        r.command === cmd &&
        (cluster === "all" || r.cluster_mode === (cluster === "true")) &&
        (tls     === "all" || r.tls          === (tls === "true"))
      );
      map[cmd] = commits.map(sha => {
        const row = rows.find(r => r.sha === sha);
        return {
          sha: sha.slice(0,8),
          timestamp: commitTimes[sha],
          value: row ? row[metricKey] : null
        };
      });
    });
    return map;
  }, [metrics, commands, commits, cluster, tls, metricKey, commitTimes]);

  const children = [
    // Controls -----------------------------------------------------------
    React.createElement('div', {className:'flex flex-wrap gap-4 justify-center'},
      labelSel('Cluster', cluster, setCluster, ['all','true','false']),
      labelSel('TLS',     tls,     setTLS,     ['all','true','false']),
      labelSel('Metric',  metricKey,setMetricKey, ['rps','avg_latency_ms','p95_latency_ms','p99_latency_ms']),
      React.createElement('button', {
        className:'bg-blue-600 text-white px-3 py-1 rounded',
        onClick: loadMetrics
      }, 'Load Metrics')
    ),
    // One chart per command ---------------------------------------------
    ...commands.map(cmd => React.createElement('div', {key:cmd, className:'bg-white rounded shadow p-2 w-full max-w-4xl'},
      React.createElement('div', {className:'font-semibold mb-2'}, cmd),
      React.createElement(ResponsiveContainer, {width:'100%', height:400},
        React.createElement(LineChart, {data: seriesByCommand[cmd]},
          React.createElement(CartesianGrid, {strokeDasharray:'3 3'}),
          React.createElement(XAxis, {
            dataKey:'timestamp',
            interval:0,
            angle:-45,
            textAnchor:'end',
            height:70,
            tickFormatter:ts=>new Date(ts).toLocaleDateString()
          }),
          React.createElement(YAxis),
          React.createElement(Tooltip),
          React.createElement(Brush, {dataKey:'timestamp'}),
          React.createElement(Line, {type:'monotone', dataKey:'value', stroke:'#3b82f6', dot:false, name: metricKey })
        )
      )
    ))
  ];

  return React.createElement('div', {className:'space-y-6 w-full flex flex-col items-center'}, ...children);
}

function labelSel(label, val, setter, opts){
  return React.createElement('label', {className:'font-medium'}, `${label}:`,
    React.createElement('select', {className:'border rounded p-1 ml-2', value:val, onChange:e=>setter(e.target.value)},
      opts.map(o=>React.createElement('option',{key:o,value:o},o))
    )
  );
}

// boot ------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const rootEl = document.getElementById('chartRoot');
  if (ReactDOM.createRoot) {
    ReactDOM.createRoot(rootEl).render(React.createElement(Dashboard));
  } else {
    ReactDOM.render(React.createElement(Dashboard), rootEl);
  }
});
