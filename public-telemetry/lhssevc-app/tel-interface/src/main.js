import '@knadh/oat/oat.min.css';
import '@knadh/oat/oat.min.js';

const base_url = "" // for local development, set to empty when html served by server
var records = [];
var cur_entry = 0;

async function refresh_data() {
	try { // wondering why this fetch code is so good? i stole it from mdn web docs :3
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
		console.log(records);
		document.getElementById("timestamp").textContent = records[records.length - 1].timestamp;
		document.getElementById("busv").textContent = records[records.length - 1].busv;
		document.getElementById("current").textContent = records[records.length - 1].current;
		document.getElementById("power").textContent = records[records.length - 1].power;
		document.getElementById("hall-speed").textContent = records[records.length - 1].hall_speed;
	} catch (error) {
		console.error(error.message);
	}
}

document.getElementById("dat-refresh").addEventListener("click", refresh_data)
