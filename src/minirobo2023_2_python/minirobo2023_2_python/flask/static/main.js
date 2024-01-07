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
    document.getElementById('user_count').innerText = msg.user_count;
});

socket.on('connect', function () {
    socket.emit('my event', { data: 'I\'m connected!' });
});

window.setInterval(function () {
    start_time_ping_pong = (new Date).getTime();
    socket.emit('json_request');
}, 33);

socket.on('json_receive', function (json) {
    console.log(json);
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
        // 最高13V
        // 最低10V
        if (json["battery_voltage"] > 1) {
            document.getElementById("battery_voltage_char").innerText = json["battery_voltage"] + "V";
            document.getElementById("battery_voltage_gauge").style.width = (json["battery_voltage"] - 10) / 0.03 + "%";
        } else {
            document.getElementById("battery_voltage_char").innerText = "-V";
            document.getElementById("battery_voltage_gauge").style.width = "0";
        }
    }
    if ("wifi_signal_strength" in json) {
        document.getElementById("wifi_signal_strength_value").innerText = json["wifi_signal_strength"];
    }
    for (let i = 1; i < 7; i++) {
        if ("motor" + i + "_speed" in json) {
            // document.getElementById("motor" + i + "_speed_char").innerText = Math.round(json["motor" + i + "_speed"]);
            document.getElementById("motor" + i + "_speed_gauge").style.width = json["motor" + i + "_speed"] / 5.1 + 50 + "%";
        }
    }
    if ("servo_angle" in json) {
        // document.getElementById("servo_angle_char").innerText = Math.round(json["servo_angle"]);
        document.getElementById("servo_angle_gauge").style.width = json["servo_angle"] / 2.7 + 50 + "%";
    }
    if ("angle_value" in json) {
        document.getElementById("angle_char").innerText = json["angle_value"] + "°";
        document.getElementById("angle_gauge").style.width = json["angle_value"] / 3.6 + "%";
    }
    if ("start_time" in json && json["start_time"] != 0) {
        start_timer = new Date(json["start_time"] * 1000); // Unixエポック時間にするために1000倍する
    }
    if ("joy1_axes" in json) {
        if (document.getElementById("controller1_axes").childElementCount == json["joy1_axes"].length) {
            for (let i = 0; i < json["joy1_axes"].length; i++) {
                document.getElementById("controller1_axes" + i).style.width = Math.floor(json["joy1_axes"][i] * 100) / 2 + 50 + "%";
            }
        } else {
            innerhtml = "";
            for (let i = 0; i < json["joy1_axes"].length; i++) {
                innerhtml += "<div class='gauge gauge_mini'><div id='controller1_axes" + i + "' class='gauge_gauge' style='width:50%'></div><div class='gauge_char'>" + i + "</div></div>"
            }
            document.getElementById("controller1_axes").innerHTML = innerhtml;
        }
    }
    if ("joy1_buttons" in json) {
        if (document.getElementById("controller1_buttons").childElementCount == json["joy1_buttons"].length) {
            for (let i = 0; i < json["joy1_buttons"].length; i++) {
                document.getElementById("controller1_button" + i).setAttribute("true_false", json["joy1_buttons"][i]);
            }
        } else {
            innerhtml = "";
            for (let i = 0; i < json["joy1_buttons"].length; i++) {
                innerhtml += "<div id='controller1_button" + i + "' class='buttons' true_false='0'>" + i + "</div>"
            }
            document.getElementById("controller1_buttons").innerHTML = innerhtml;
        }
    }
});

window.setInterval(function () {
    // カウントダウンタイマーの処理
    if (start_timer != null) {
        const GameTimeSec = 180; // 試合時間(秒)
        after_time = new Date(start_timer.getTime() + GameTimeSec * 1000);
        let remainingTimeInSeconds = Math.floor((after_time - new Date()) / 1000);

        let formattedMinutes = "00";
        let formattedSeconds = "00";

        if (remainingTimeInSeconds > 0) {
            // 分と秒に分割
            let minutes = Math.floor(remainingTimeInSeconds / 60);
            let seconds = remainingTimeInSeconds % 60;

            // 1桁の場合に0を頭に付け加える
            formattedMinutes = (minutes < 10) ? "0" + minutes : minutes;
            formattedSeconds = (seconds < 10) ? "0" + seconds : seconds;
        }
        document.getElementById("timer_char").innerText = formattedMinutes + ":" + formattedSeconds;
        document.getElementById("timer_gauge").style.width = remainingTimeInSeconds / GameTimeSec * 100 + "%";
    }

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
    document.getElementById("ping").innerText = Math.round(10 * sum / ping_pong_times.length) / 10;
});

const fullscreenElement = document.documentElement;
document.addEventListener("click", toggleFullScreen);
function toggleFullScreen() {
    if (!document.fullscreenElement) {
        fullscreenElement
            .requestFullscreen()
            .then(() => {
                if (screen.orientation && screen.orientation.lock) {
                    screen.orientation.lock("landscape").catch((err) => {
                        console.error(
                            "Error attempting to lock screen orientation:",
                            err
                        );
                    });
                }
            })
            .catch((err) => {
                console.error(
                    "Error attempting to enable full-screen mode:",
                    err
                );
            });
    }
}