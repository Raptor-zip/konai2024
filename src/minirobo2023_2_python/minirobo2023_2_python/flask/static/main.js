let inputElem;
let currentValueElement;

var socket = io();

var ping_pong_times = [];
let start_time_ping_pong;
let start_timer

let json_received = {};
namespace = '/test';

// 接続者数の更新
socket.on('count_update', function (msg) {
    console.log(9);
    $('#user_count').html(msg.user_count);
});

// テキストエリアの更新
socket.on('text_update', function (msg) {
    console.log(14);
    $('#text').val(msg.text);
});

socket.on('connect', function () {
    console.log(31);
    socket.emit('my event', { data: 'I\'m connected!' });
});

socket.on('json', function () {
});

window.setInterval(function () {
    start_time_ping_pong = (new Date).getTime();
    socket.emit('json_request');
}, 33);

socket.on('json_receive', function (json) {
    console.log(json);
    // text = {
    //     "state": self.state,
    //     "ubuntu_ssid": wifi_ssid,
    //     "ubuntu_ip": ipget.ipget().ipaddr("wlp2s0"),
    //     "esp32_ip": esp32_ip,
    //     "battery_voltage": reception_json["battery_voltage"],
    //     "wifi_signal_strength": reception_json["wifi_signal_strength"],
    //     "motor1_speed": self.motor1_speed,
    //     "motor2_speed": self.motor2_speed,
    //     "motor3_speed": self.motor3_speed,
    //     "distance": reception_json["raw_distance"] + self.distance_adjust,
    //     "angle": a,
    //     "raw_angle": 0,
    //     "start_time": self.start_time
    // }
    if ("state" in json) {
        switch (json["state"]) {
            case 0:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#000000";
                break;
            case 1:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#3498db";
                break;
            case 2:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#e74c3c";
                break;
            case 3:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#2ecc71";
                break;
            case 4:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#f39c12";
                break;
            case 5:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#9b59b6";
                break;
            case 6:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#1abc9c";
                break;
            case 7:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#e67e22";
                break;
            case 8:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#34495e";
                break;
            default:
                document.getElementsByClassName("container")[0].style.backgroundColor = "#ffffff";
                break;
        }
        // console.log("あた");
    }
    if ("ubuntu_ssid" in json) {
        document.getElementById("ubuntu_ssid_value").innerText = json["ubuntu_ssid"];
    }
    if ("ubuntu_ip" in json) {
        document.getElementById("ubuntu_ip_value").innerText = json["ubuntu_ip"].split("/")[0];
    }
    if ("esp32_ip" in json) {
        document.getElementById("esp32_ip_value").innerText = json["esp32_ip"];
    }
    if ("battery_voltage" in json) {
        document.getElementById("battery_voltage_value").innerText = json["battery_voltage"];
    }
    if ("wifi_signal_strength" in json) {
        document.getElementById("wifi_signal_strength_value").innerText = json["wifi_signal_strength"];
    }
    if ("motor1_speed" in json) {
        document.getElementById("motor1_speed_value").innerText = Math.round(json["motor1_speed"]);
        document.getElementById("motor1_speed_range").value = json["motor1_speed"] + 256;
    }
    if ("motor2_speed" in json) {
        document.getElementById("motor2_speed_value").innerText = Math.round(json["motor2_speed"]);
        document.getElementById("motor2_speed_range").value = json["motor2_speed"] + 256;
    }
    if ("motor3_speed" in json) {
        document.getElementById("motor3_speed_value").innerText = Math.round(json["motor3_speed"]);
        document.getElementById("motor3_speed_range").value = json["motor3_speed"] + 256;
    }
    if ("motor4_speed" in json) {
        document.getElementById("motor4_speed_value").innerText = Math.round(json["motor4_speed"]);
        document.getElementById("motor4_speed_range").value = json["motor4_speed"] + 256;
    }
    if ("motor5_speed" in json) {
        document.getElementById("motor5_speed_value").innerText = Math.round(json["motor5_speed"]);
        document.getElementById("motor5_speed_range").value = json["motor5_speed"] + 256;
    }
    if ("motor6_speed" in json) {
        document.getElementById("motor6_speed_value").innerText = Math.round(json["motor6_speed"]);
        document.getElementById("motor6_speed_range").value = json["motor6_speed"] + 256;
    }
    if ("servo_angle" in json) {
        document.getElementById("servo_angle_value").innerText = Math.round(json["servo_angle"]);
        document.getElementById("servo_angle_range").value = json["servo_angle"];
    }
    if ("angle_value" in json) {
        document.getElementById("angle_value").innerText = Math.round(json["angle_value"]) + "°";
    }
    if ("start_time" in json && json["start_time"] != 0) {
        start_timer = new Date;
        console.log(json["start_time"]);
        console.log(now - json["start_time"]);
    }


    // if ()
    // console.log(json_received);
});

window.setInterval(function () {
    // カウントダウンタイマーの処理
    // if (start_timer != null) {
    //     const now = new Date(); // 現在時刻を取得
    //     const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1); // 明日の0:00を取得
    //     const diff = tomorrow.getTime() - now.getTime(); // 時間の差を取得（ミリ秒）

    //     // ミリ秒から単位を修正
    //     const calcHour = Math.floor(diff / 1000 / 60 / 60);
    //     const calcMin = Math.floor(diff / 1000 / 60) % 60;
    //     const calcSec = Math.floor(diff / 1000) % 60;

    //     // 取得した時間を表示（2桁表示）
    //     min.innerHTML = calcMin < 10 ? '0' + calcMin : calcMin;
    //     sec.innerHTML = calcSec < 10 ? '0' + calcSec : calcSec;
    // }

    // Ping計測
    start_time_ping_pong = (new Date).getTime();
    socket.emit('my ping');
}, 1000);

socket.on('my pong', function () {
    var latency = (new Date).getTime() - start_time_ping_pong;
    ping_pong_times.push(latency);
    ping_pong_times = ping_pong_times.slice(-10); // keep last 30 samples
    var sum = 0;
    for (var i = 0; i < ping_pong_times.length; i++)
        sum += ping_pong_times[i];
    $('#ping').text(Math.round(10 * sum / ping_pong_times.length) / 10 + "ms");
});

// 現在の値を埋め込む関数
const setCurrentValue = (val) => {
    console.log(val);
    if (document.getElementById("motor1_checkbox").checked) {
        currentValueElem.value = val;
        data_send_to_python();
    }
}

// inputイベント時に値をセットする関数
const rangeOnChange = (e) => {
    setCurrentValue(e.target.value);
}


function reset() {

}