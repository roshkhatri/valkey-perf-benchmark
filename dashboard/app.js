/* app.js — Valkey benchmark dashboard for last 100 commits
   Features:
   • Fetch last 100 commit SHAs from completed_commits.json
   • Load metrics.json for each commit in parallel
   • Filter by command, cluster_mode, tls
   • Display trend lines over commits for RPS and latency percentiles
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
  Legend
} = Recharts;

// Utility fetch ---------------------------------------------------------
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

// React root component --------------------------------------------------
function Dashboard() {
  const [commits, setCommits] = React.useState([]);  // full sha[] newest→oldest
  const [metrics, setMetrics] = React.useState([]);  // flat metrics rows

  const [command, setCommand]         = React.useState("SET");
  const [cluster, setCluster]         = React.useState("all"); // all/true/false
  const [tls, setTLS]                 = React.useState("all"); // all/true/false
  const [metricKey, setMetricKey]     = React.useState("rps");

  // 1) load commit list (once)
  React.useEffect(() => {
    fetchJSON(COMPLETED_URL)
      .then(list => setCommits(list.slice(-100).reverse())) // newest first
      .catch(err => {
        console.error('Failed to load commit list:', err);
        setCommits([]);
      });
  }, []);

  // 2) fetch metrics for each commit
  React.useEffect(() => {
    if (!commits.length) return;
    (async () => {
      const all = [];
      await Promise.all(commits.map(async sha => {
        try {
          const rows = await fetchJSON(RESULT_URL(sha));
          rows.forEach(r => all.push({ ...r, sha }));
        } catch (err) {
          console.error(`Failed to load metrics for ${sha}:`, err);
        }
      }));
      // sort by commit order (commits array already newest→oldest)
      const order = Object.fromEntries(commits.map((s,i)=>[s,i]));
      all.sort((a,b)=>order[a.sha]-order[b.sha]);
      setMetrics(all);
    })();
  }, [commits]);

  // distinct commands for UI
  const commandOpts = React.useMemo(() => [...new Set(metrics.map(m=>m.command))].sort(), [metrics]);

  // filtered rows
  const filtered = React.useMemo(() => metrics.filter(r =>
    (command ? r.command === command : true) &&
    (cluster === "all" || r.cluster_mode === (cluster === "true")) &&
    (tls     === "all" || r.tls          === (tls === "true"))
  ), [metrics, command, cluster, tls]);

  // regroup by sha → single row per sha with chosen metric
  const series = React.useMemo(() => {
    return commits.map(sha => {
      const row = filtered.find(r => r.sha === sha);
      return { sha: sha.slice(0,8), value: row ? row[metricKey] : null };
    });
  }, [filtered, commits, metricKey]);

  return React.createElement('div', {className:'space-y-6'},
    // Controls -----------------------------------------------------------
    React.createElement('div', {className:'flex flex-wrap gap-4'},
      labelSel('Command', command, setCommand, commandOpts),
      labelSel('Cluster', cluster, setCluster, ['all','true','false']),
      labelSel('TLS',     tls,     setTLS,     ['all','true','false']),
      labelSel('Metric',  metricKey,setMetricKey, ['rps','avg_latency_ms','p95_latency_ms','p99_latency_ms'])
    ),
    // Chart --------------------------------------------------------------
    React.createElement('div', {className:'bg-white rounded shadow p-2'},
      React.createElement(ResponsiveContainer, {width:'100%', height:400},
        React.createElement(LineChart, {data: series},
          React.createElement(CartesianGrid, {strokeDasharray:'3 3'}),
          React.createElement(XAxis, {dataKey:'sha', interval:0, angle:-45, textAnchor:'end', height:70}),
          React.createElement(YAxis),
          React.createElement(Tooltip),
          React.createElement(Line, {type:'monotone', dataKey:'value', stroke:'#3b82f6', dot:false, name: metricKey })
        )
      )
    )
  );
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
