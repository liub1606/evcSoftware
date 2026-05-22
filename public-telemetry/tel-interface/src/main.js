import '@knadh/oat/oat.min.css';
import '@knadh/oat/oat.min.js';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';

var base_url = '';
// base_url = "http://127.0.0.1:8080" // for local development, set to empty when html served by server
var records = [];
var max_vis_len = 2 ** document.getElementById("dat-range").value;
document.getElementById("range-num").textContent = 2 ** document.getElementById("dat-range").value;
var cur_entry = 0;
var req = 0;
var lap_starts = [];
var lap_times = [];

Chart.defaults.color = "black";
const volts_ctx = document.getElementById("busv-chart");
const volts_chart = new Chart(volts_ctx, datachart_conf("voltage (V)", ["busv (V)", "unloaded (V)"], ["#ea9d34", "#56949f"]));
const amps_ctx = document.getElementById("current-chart");
const amps_chart = new Chart(amps_ctx, datachart_conf("current (A)", ["current (A)"], ["#b4637a"]));
const ohms_ctx = document.getElementById("intres-chart");
const ohms_chart = new Chart(ohms_ctx, datachart_conf("internal resistance (mΩ)", ["internal resistance (mΩ)"], ["#286983"]));
const kmh_ctx = document.getElementById("hallspeed-chart");
const kmh_chart = new Chart(kmh_ctx, datachart_conf("hall speed (km/h)", ["hall speed (km/h)"], ["#907aa9"]));
const soc_ctx = document.getElementById("soc-chart");
const soc_chart = new Chart(soc_ctx, datachart_conf("soc (%)", ["soc (%)", "drain approximation"], ["#d7827e", "#575279"]));

function datachart_conf(title, labels, colors) {
	return {
		type: "line",
		data: {
			datasets: Array.from(labels.entries().map((entry) => {
				return {
					data: [],
					label: entry[1],
					pointStyle: false,
					backgroundColor: colors[entry[0]],
					borderColor: colors[entry[0]],
					indexAxis: 'x'
				}
			}))
		},
		options: {
			scales: {
				x: {
					position: "bottom",
					type: "time",
					ticks: {
						autoSkip: true,
						autoSkipPadding: 20,
						minRotation: 0,
						maxRotation: 1
					}
				}
			},
			animation: {
				duration: 0
			},
			interaction: {
				mode: "nearest",
				axis: "x",
				intersect: false
			},
			plugins: {
				legend: {
					display: false
				},
				title: {
					display: true,
					text: title
				}
			},
			responsive: true,
			maintainAspectRatio: false
		}
	}
}

async function refresh_data() {
	try { // wondering why this fetch code is so good? i stole it from mdn web docs :3
		req++;
		const params = new URLSearchParams({start: cur_entry});
		const response = await fetch(`${base_url}/get-entries?${params.toString()}`, {
			method: "GET"
		});
		if (!response.ok) {
			throw new Error(`Response status: ${response.status}`);
		}
		// console.log(response);
		const result = await response.json();
		// console.log(result);
		// console.log(result.upto);
		cur_entry = result.upto;
		// console.log(result.records);
		records = records.concat(result.records);
		records = records.slice(-max_vis_len);
		// console.log(records);
		var time = new Date(records[records.length - 1][0] / 1_000_000);
		var drain_time = new Date(records[records.length - 1][8] / 1_000_000);
		var min_remain = (drain_time.getTime() - Date.now()) / 1000 / 60;
		// console.log(min_remain);
		document.getElementById("timestamp").textContent = time.toLocaleTimeString();
		document.getElementById("drain-timestamp").textContent = drain_time.toLocaleTimeString();
		document.getElementById("busv").textContent = records[records.length - 1][1].toFixed(2);
		document.getElementById("current").textContent = records[records.length - 1][2].toFixed(2);
		document.getElementById("power").textContent = records[records.length - 1][3].toFixed(2);
		document.getElementById("soc").textContent = records[records.length - 1][4].toFixed(2);
		document.getElementById("hall-speed").textContent = records[records.length - 1][5].toFixed(2);
		document.getElementById("internal-resistance").textContent = records[records.length - 1][6].toFixed(2);
		document.getElementById("unloaded-voltage").textContent = records[records.length - 1][7].toFixed(2);
		document.getElementById("remain-timestamp").textContent = min_remain.toFixed(2);
		document.getElementById("records").textContent = records.length;
		document.getElementById("requests").textContent = req;
		// console.log(amps_chart.data.datasets[0]);
		for (let i = 0; i < result.records.length; i++) {
			const timestamp = new Date(result.records[i][0] / 1_000_000);
			volts_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][1]});
			amps_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][2]});
			soc_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][4]});
			kmh_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][5]});
			ohms_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][6]});
			volts_chart.data.datasets[1].data.push({x: timestamp, y: result.records[i][7]});
			soc_chart.data.datasets[1].data = [
				{x: result.records[i][9] / 1_000_000, y: 100},
				{x: result.records[i][8] / 1_000_000, y: 0}];
		}
		volts_chart.data.datasets[0].data = volts_chart.data.datasets[0].data.slice(-max_vis_len);
		volts_chart.data.datasets[1].data = volts_chart.data.datasets[1].data.slice(-max_vis_len);
		amps_chart.data.datasets[0].data = amps_chart.data.datasets[0].data.slice(-max_vis_len);
		ohms_chart.data.datasets[0].data = ohms_chart.data.datasets[0].data.slice(-max_vis_len);
		kmh_chart.data.datasets[0].data = kmh_chart.data.datasets[0].data.slice(-max_vis_len);
		soc_chart.data.datasets[0].data = soc_chart.data.datasets[0].data.slice(-max_vis_len);
		soc_chart.options.scales.x.min = records[0][0] / 1_000_000;
		volts_chart.update();
		amps_chart.update();
		ohms_chart.update();
		kmh_chart.update();
		soc_chart.update();
	} catch (error) {
		console.error(error.message);
	}
}

function hifreq() {
	if (lap_starts.length > 0) {
		document.getElementById("cur-lap").textContent = `${lap_times.length}: ${((Date.now() - lap_starts[0]) / 1_000).toFixed(1)}s`;
	}
}

document.getElementById("dat-range").addEventListener("input", (event) => {
	document.getElementById("range-num").textContent = 2 ** event.target.value;
	max_vis_len = 2 ** document.getElementById("dat-range").value;
	volts_chart.data.datasets[0].data = [];
	volts_chart.data.datasets[1].data = [];
	amps_chart.data.datasets[0].data = [];
	ohms_chart.data.datasets[0].data = [];
	kmh_chart.data.datasets[0].data = [];
	soc_chart.data.datasets[0].data = [];
	cur_entry = 0;
	records = [];
});

document.getElementById("plus-lap").onclick = (event) => {
	console.log("btn pressed");
	lap_starts.unshift(Date.now());
	// document.getElementById("lap-ct").textContent = laptimes.length;
	if (lap_starts.length >= 2) {
		lap_times.unshift(((lap_starts[0] - lap_starts[1]) / 1_000).toFixed(1))
		document.getElementById("lap-time").insertAdjacentHTML("afterbegin", `${lap_times.length - 1}: ${lap_times[0]}s<br>`);
		console.log(lap_times);
	}
}

document.getElementById("download").onclick = (event) => {
	const data = lap_times.map((el, idx) => {
		return [Number(el), lap_starts[idx]];
	})

	const json_str = JSON.stringify(data, null, 2);
	const blob = new Blob([json_str], {
		type: "application/json"
	});

	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = "lap_data.json";
	a.click();
}

refresh_data();
setInterval(refresh_data, 2000);
setInterval(hifreq, 100);
