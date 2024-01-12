let inputElem;
let currentValueElement;

var socket = io();

var ping_pong_times = [];
let start_time_ping_pong;
let start_timer

const alarm = new Audio("static/battery_alert.mp3");
alarm.loop = true;

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
    // console.log(json);
    if ("state" in json) {
        // switch (json["state"]) {
        // case 0:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#000000";
        //     break;
        // case 1:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#3498db";
        //     break;
        // case 2:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#e74c3c";
        //     break;
        // case 3:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#2ecc71";
        //     break;
        // case 4:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#f39c12";
        //     break;
        // case 5:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#9b59b6";
        //     break;
        // case 6:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#1abc9c";
        //     break;
        // case 7:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#e67e22";
        //     break;
        // case 8:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#34495e";
        //     break;
        // default:
        //     document.getElementsByClassName("container")[0].style.backgroundColor = "#ffffff";
        //     break;
        // }
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
        // MAX13V MIN10V
        if (json["battery_voltage"] > 1) {
            document.getElementById("battery_voltage_char").innerText = json["battery_voltage"] + "V";
            document.getElementById("battery_voltage_gauge").style.width = (json["battery_voltage"] - 10) / 0.03 + "%";

            if (json["battery_voltage"] < 10) {
                document.getElementById("battery_voltage_gauge").setAttribute("emergency", 1);
                document.querySelector("html body").setAttribute("emergency", 1);
                document.querySelectorAll(".parents").forEach(function (parentElement) {
                    parentElement.setAttribute("emergency", 1);
                });
                // アラームが今なっているか検出
                if (!alarm.paused) {
                    console.log('音声が再生中です。');
                } else {
                    console.log('音声は再生されていません。');
                    alarm.play();
                }
            } else {
                alarm.pause();
                document.getElementById("battery_voltage_gauge").removeAttribute("emergency");
                document.querySelector("html body").removeAttribute("emergency");
                document.querySelectorAll(".parents").forEach(function (parentElement) {
                    parentElement.removeAttribute("emergency");
                });
            }
        } else {
            document.getElementById("battery_voltage_char").innerText = "-V";
            document.getElementById("battery_voltage_gauge").style.width = "0";
        }
    }
    if ("wifi_signal_strength" in json) {
        document.getElementById("wifi_signal_strength_value").innerText = json["wifi_signal_strength"];
    }
    if ("motor_speed" in json) {
        for (let i = 0; i < json["motor_speed"].length; i++) {
            // document.getElementById("motor" + i + "_speed_char").innerText = Math.round(json["motor" + i + "_speed"]);
            document.getElementById("motor" + i + "_speed_gauge").style.width = json["motor_speed"][i] / 5.1 + 50 + "%";
        }
    }
    if ("servo_angle" in json) {
        // document.getElementById("servo_angle_char").innerText = Math.round(json["servo_angle"]);
        document.getElementById("servo_angle_gauge").style.width = json["servo_angle"] / 2.7 + 50 + "%";
    }
    if ("servo_tmp" in json) {
        if (json["servo_tmp"] != 999) {
            document.getElementById("servo_tmp_char").innerText = 127 - json["servo_tmp"];
            document.getElementById("servo_tmp_gauge").style.width = (127 - json["servo_tmp"]) / 1.27 + "%"; //(High)1～127(Low)
        } else {
            document.getElementById("servo_tmp_char").innerText = "サーボ未接続";
            document.getElementById("servo_tmp_gauge").style.width = "0%";
        }
    }
    if ("servo_cur" in json) {
        if (json["servo_cur"] != 999) {
            document.getElementById("servo_cur_char").innerText = json["servo_cur"];
            document.getElementById("servo_cur_gauge").style.width = (json["servo_cur"] - 63) / 0.63 + 50 + "%"; // (CW)1～63、(CCW)64～127
        } else {
            document.getElementById("servo_cur_char").innerText = "サーボ未接続";
            document.getElementById("servo_cur_gauge").style.width = "0%";
        }
    }
    if ("servo_deg" in json) {
        if (json["servo_deg"] != 999) {
            document.getElementById("servo_deg_char").innerText = json["servo_deg"] + "°";
            document.getElementById("servo_deg_gauge").style.width = json["servo_deg"] / 2.7 + 50 + "%";
        } else {
            document.getElementById("servo_deg_char").innerText = "サーボ未接続";
            document.getElementById("servo_deg_gauge").style.width = "0%";
        }
    }
    // if ("angle_value" in json) {
    //     document.getElementById("angle_char").innerText = json["angle_value"] + "°";
    //     document.getElementById("angle_gauge").style.width = json["angle_value"] / 3.6 + "%";
    // }
    if ("start_time" in json && json["start_time"] != 0) {
        start_timer = new Date(json["start_time"] * 1000); // Unixエポック時間にするために1000倍する
    }
    if ("joy" in json) {
        for (let i = 0; i < Object.keys(json["joy"]).length; i++) {
            if (document.getElementById("controller" + i) == null) {
                // 要素を作る
                const newDiv = document.createElement("div");
                newDiv.id = "controller" + i;

                const newContent0 = document.createElement("p");
                newContent0.textContent = "コントローラー" + i;
                newDiv.appendChild(newContent0);

                const newContent1 = document.createElement("div");
                newContent1.id = "controller" + i + "_axes";
                newContent1.className = "grid_2columns";
                for (let j = 0; j < json["joy"]["joy" + i]["axes"].length; j++) {
                    // 新しい div 要素を作成
                    const divElement = document.createElement('div');
                    divElement.className = 'gauge gauge_mini';

                    // 子要素1: ゲージの本体
                    const gaugeBody = document.createElement('div');
                    gaugeBody.id = 'controller' + i + '_axes' + j;
                    gaugeBody.className = 'gauge_gauge';
                    gaugeBody.style.width = '50%';
                    divElement.appendChild(gaugeBody);

                    // 子要素2: 文字
                    const charElement = document.createElement('div');
                    charElement.className = 'gauge_char';
                    charElement.textContent = j;
                    divElement.appendChild(charElement);

                    // コンテナに新しく作成した要素を追加
                    newContent1.appendChild(divElement);
                }
                newDiv.appendChild(newContent1);

                const newContent2 = document.createElement("div");
                newContent2.id = "controller" + i + "_buttons";
                for (let k = 0; k < json["joy"]["joy" + i]["buttons"].length; k++) {
                    // 新しい div 要素を作成
                    var divElement = document.createElement('div');
                    divElement.id = 'controller' + i + '_button' + k;
                    divElement.className = 'buttons';
                    divElement.setAttribute('true_false', '0');
                    divElement.textContent = k;
                    // コンテナに新しく作成した要素を追加
                    newContent2.appendChild(divElement);
                }
                newDiv.appendChild(newContent2);

                document.getElementById("controllers").appendChild(newDiv);
            }
            for (let j = 0; j < json["joy"]["joy" + i]["axes"].length; j++) {
                document.getElementById("controller" + i + "_axes" + j).style.width = Math.floor(json["joy"]["joy" + i]["axes"][j] * 100) / 2 + 50 + "%";
            }
            for (let j = 0; j < json["joy"]["joy" + i]["buttons"].length; j++) {
                document.getElementById("controller" + i + "_button" + j).setAttribute("true_false", json["joy"]["joy" + i]["buttons"][j]);
            }
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