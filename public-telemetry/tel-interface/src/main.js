import '@knadh/oat/oat.min.css';
import '@knadh/oat/oat.min.js';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';

var base_url = '';
base_url = "http://127.0.0.1:8080" // for local development, set to empty when html served by server
var records = [];
const max_vis_len = 2500;
var cur_entry = 0;
var req = 0;

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
const soc_chart = new Chart(soc_ctx, datachart_conf("soc (%)", ["soc (%)"], ["#d7827e"]));

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
				mode:"nearest",
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
		console.log(result.upto);
		cur_entry = result.upto;
		// console.log(result.records);
		records = records.concat(result.records);
		records = records.slice(-max_vis_len);
		console.log(records);
		var date = new Date(records[records.length - 1][0] / 1_000_000);
		document.getElementById("timestamp").textContent = date.toLocaleTimeString();
		document.getElementById("busv").textContent = records[records.length - 1][1].toFixed(2);
		document.getElementById("current").textContent = records[records.length - 1][2].toFixed(2);
		document.getElementById("power").textContent = records[records.length - 1][3].toFixed(2);
		document.getElementById("soc").textContent = records[records.length - 1][4].toFixed(2);
		document.getElementById("hall-speed").textContent = records[records.length - 1][5].toFixed(2);
		document.getElementById("internal-resistance").textContent = records[records.length - 1][6].toFixed(2);
		document.getElementById("unloaded-voltage").textContent = records[records.length - 1][7].toFixed(2);
		document.getElementById("records").textContent = records.length;
		document.getElementById("requests").textContent = req;
		console.log(amps_chart.data.datasets[0]);
		for (let i = 0; i < result.records.length; i++) {
			const timestamp = new Date(result.records[i][0] / 1_000_000);
			volts_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][1]});
			amps_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][2]});
			soc_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][4]});
			kmh_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][5]});
			ohms_chart.data.datasets[0].data.push({x: timestamp, y: result.records[i][6]});
			volts_chart.data.datasets[1].data.push({x: timestamp, y: result.records[i][7]});
		}
		volts_chart.data.datasets[0].data = volts_chart.data.datasets[0].data.slice(-max_vis_len);
		volts_chart.data.datasets[1].data = volts_chart.data.datasets[1].data.slice(-max_vis_len);
		amps_chart.data.datasets[0].data = amps_chart.data.datasets[0].data.slice(-max_vis_len);
		ohms_chart.data.datasets[0].data = ohms_chart.data.datasets[0].data.slice(-max_vis_len);
		kmh_chart.data.datasets[0].data = kmh_chart.data.datasets[0].data.slice(-max_vis_len);
		soc_chart.data.datasets[0].data = soc_chart.data.datasets[0].data.slice(-max_vis_len);
		volts_chart.update();
		amps_chart.update();
		ohms_chart.update();
		kmh_chart.update();
		soc_chart.update();
	} catch (error) {
		console.error(error.message);
	}
}

refresh_data();
setInterval(refresh_data, 5000);
