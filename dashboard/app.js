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
        return { sha: sha.slice(0,8), value: row ? row[metricKey] : null };
      });
    });
    return map;
  }, [metrics, commands, commits, cluster, tls, metricKey]);

  const children = [
    // Controls -----------------------------------------------------------
    React.createElement('div', {className:'flex flex-wrap gap-4'},
      labelSel('Cluster', cluster, setCluster, ['all','true','false']),
      labelSel('TLS',     tls,     setTLS,     ['all','true','false']),
      labelSel('Metric',  metricKey,setMetricKey, ['rps','avg_latency_ms','p95_latency_ms','p99_latency_ms'])
    ),
    // One chart per command ---------------------------------------------
    ...commands.map(cmd => React.createElement('div', {key:cmd, className:'bg-white rounded shadow p-2'},
      React.createElement('div', {className:'font-semibold mb-2'}, cmd),
      React.createElement(ResponsiveContainer, {width:'100%', height:400},
        React.createElement(LineChart, {data: seriesByCommand[cmd]},
          React.createElement(CartesianGrid, {strokeDasharray:'3 3'}),
          React.createElement(XAxis, {dataKey:'sha', interval:0, angle:-45, textAnchor:'end', height:70}),
          React.createElement(YAxis),
          React.createElement(Tooltip),
          React.createElement(Line, {type:'monotone', dataKey:'value', stroke:'#3b82f6', dot:false, name: metricKey })
        )
      )
    ))
  ];

  return React.createElement('div', {className:'space-y-6'}, ...children);
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
