import '@knadh/oat/oat.min.css';
import '@knadh/oat/oat.min.js';
import {Chart, Colors} from 'chart.js/auto';
import 'chartjs-adapter-date-fns';

var base_url = '';
// base_url = "http://127.0.0.1:8080" // for local development, set to empty when html served by server
var records = [];
const max_vis_len = 1000;
var cur_entry = 0;
var req = 0;

Chart.register(Colors);
Chart.defaults.color = "white";
const volts_ctx = document.getElementById("busv-chart");
const volts_chart = new Chart(volts_ctx, datachart_conf("busv (V)", "#81beff"));
const amps_ctx = document.getElementById("current-chart");
const amps_chart = new Chart(amps_ctx, datachart_conf("current (A)", "#ffb8da"));
const watts_ctx = document.getElementById("power-chart");
const watts_chart = new Chart(watts_ctx, datachart_conf("power (W)", "#fff3af"));
const kmh_ctx = document.getElementById("hallspeed-chart");
const kmh_chart = new Chart(kmh_ctx, datachart_conf("hall speed (km/h)", "#dfb8ff"));

function datachart_conf(label, color) {
	return {type: "line",
		data: {
			datasets: [{
				data: [],
				label: label,
				pointStyle: false,
				backgroundColor: color,
				borderColor: color
			}]
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
					text: label
				},
				colors: {
					enabled: true
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
		console.log(records);
		var date = new Date(records[records.length - 1].timestamp / 1_000_000);
		document.getElementById("timestamp").textContent = date.toLocaleString();
		document.getElementById("busv").textContent = records[records.length - 1].busv;
		document.getElementById("current").textContent = records[records.length - 1].current;
		document.getElementById("power").textContent = records[records.length - 1].power;
		document.getElementById("hall-speed").textContent = records[records.length - 1].hall_speed;
		document.getElementById("records").textContent = records.length;
		document.getElementById("requests").textContent = req;
		for (let i = 0; i < result.records.length; i++) {
			volts_chart.data.datasets[0].data.push({x: result.records[i].timestamp / 1_000_000, y: result.records[i].busv});
			amps_chart.data.datasets[0].data.push({x: result.records[i].timestamp / 1_000_000, y: result.records[i].current});
			watts_chart.data.datasets[0].data.push({x: result.records[i].timestamp / 1_000_000, y: result.records[i].power});
			kmh_chart.data.datasets[0].data.push({x: result.records[i].timestamp / 1_000_000, y: result.records[i].hall_speed});
		}
		volts_chart.data.datasets[0].data = volts_chart.data.datasets[0].data.slice(-max_vis_len);
		amps_chart.data.datasets[0].data = amps_chart.data.datasets[0].data.slice(-max_vis_len);
		watts_chart.data.datasets[0].data = watts_chart.data.datasets[0].data.slice(-max_vis_len);
		kmh_chart.data.datasets[0].data = kmh_chart.data.datasets[0].data.slice(-max_vis_len);
		volts_chart.update();
		amps_chart.update();
		watts_chart.update();
		kmh_chart.update();
	} catch (error) {
		console.error(error.message);
	}
}

refresh_data();
setInterval(refresh_data, 3000);
