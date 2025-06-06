/* global React, ReactDOM, Recharts */

// bucket-relative paths
const COMPLETED_URL = "../completed_commits.json";
const RESULT_URL = sha => `../results/${sha}/metrics.json`;

const {
  ResponsiveContainer, BarChart, Bar,
  LineChart, Line, XAxis, YAxis, Tooltip, Legend
} = Recharts;

// fetch helpers ----------------------------------------------------------
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

async function getCommitList() {
  try {
    return await fetchJSON(COMPLETED_URL);
  } catch {
    return [];
  }
}

// ui helpers -------------------------------------------------------------
function option(text, value = text) {
  const opt = document.createElement("option");
  opt.textContent = text;
  opt.value = value;
  return opt;
}

// render chart using React + Recharts ------------------------------------
function renderChart(data, metric) {
  const root = document.getElementById("chartRoot");
  root.innerHTML = "";               // clear previous

  const chart =
    React.createElement(ResponsiveContainer, { width: "100%", height: 400 },
      React.createElement(BarChart, { data, margin: { top: 20, right: 30 } },
        React.createElement(XAxis, { dataKey: "command" }),
        React.createElement(YAxis),
        React.createElement(Tooltip),
        React.createElement(Legend),
        React.createElement(Bar, {
          dataKey: metric,
          fill: "#3b82f6",           // Tailwind blue-500
          name: metric
        })
      )
    );

  ReactDOM.render(chart, root);
}

// main logic -------------------------------------------------------------
(async () => {
  const commits = await getCommitList();          // newest last
  const commitSel = document.getElementById("commitSelect");
  const metricSel = document.getElementById("metricSelect");

  commits.slice(-100).forEach(sha =>         // last 100 commits
    commitSel.appendChild(option(sha.slice(0, 12), sha))
  );
  commitSel.selectedIndex = commitSel.length - 1; // default = newest

  async function loadAndRender() {
    const sha = commitSel.value;
    const metric = metricSel.value;

    try {
      const data = await fetchJSON(RESULT_URL(sha));
      renderChart(data, metric);
    } catch (e) {
      console.error(e);
      alert(`Failed to load metrics for ${sha}`);
    }
  }

  commitSel.addEventListener("change", loadAndRender);
  metricSel.addEventListener("change", loadAndRender);

  loadAndRender();                   // initial render
})();
