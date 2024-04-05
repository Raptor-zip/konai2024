let inputElem;
let currentValueElement;

var socket = io();

var ping_pong_times = [];
let start_time_ping_pong;
let start_timer

let sadou_angle = 0;
let sadou_speed = 0;

const alarm = new Audio("static/battery_alert.mp3");
alarm.loop = true;

let received_json = {};
namespace = '/test';

// ICE server URLs
let peerConnectionConfig = {
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
};

// Data channel オプション
let dataChannelOptions = {
    ordered: false,
};

// Peer Connection
let peerConnection;

// Data Channel
let dataChannel;

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
}, 16);

function update_info() {
    let json = received_json;

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
    if ("battery" in json) {
        // MAX13V MIN10V
        for (let i = 3; i < 2 + 3; i++) {
            if (json["battery"]["battery_" + i + "cell"]["average_voltage"] > 1) {
                document.getElementById("battery_" + i + "cell_voltage_char").innerText = json["battery"]["battery_" + i + "cell"]["average_voltage"] + "V";
                document.getElementById("battery_" + i + "cell_voltage_gauge").style.width = (json["battery"]["battery_" + i + "cell"]["average_voltage"] - 9) / 0.03 + "%";

                if (json["battery"]["battery_" + i + "cell"]["average_voltage"] < 10) {
                    // document.getElementById("battery_voltage_gauge").setAttribute("emergency", 1);
                    // document.querySelector("html body").setAttribute("emergency", 1);
                    // document.querySelectorAll(".parents").forEach(function (parentElement) {
                    //     parentElement.setAttribute("emergency", 1);
                    // });
                    // アラームが今なっているか検出
                    if (!alarm.paused) {
                        console.log('音声が再生中です。');
                    } else {
                        console.log('音声は再生されていません。');
                        alarm.play();
                    }
                } else {
                    alarm.pause();
                    // document.getElementById("battery_voltage_gauge").removeAttribute("emergency");
                    // document.querySelector("html body").removeAttribute("emergency");
                    // document.querySelectorAll(".parents").forEach(function (parentElement) {
                    //     parentElement.removeAttribute("emergency");
                    // });
                }
            } else {
                alarm.pause();
                document.getElementById("battery_" + i + "cell_voltage_char").innerText = "-V";
                document.getElementById("battery_" + i + "cell_voltage_gauge").style.width = "0";
            }
        }
    }
    if ("wifi_signal_strength" in json) {
        document.getElementById("wifi_signal_strength_value").innerText = json["wifi_signal_strength"];
    }
    console.log(json["DCmotor_speed"][0]);
    if ("DCmotor_speed" in json) {
        for (let i = 0; i < json["DCmotor_speed"].length - 1; i++) {
            // document.getElementById("motor" + i + "_speed_char").innerText = Math.round(json["motor" + i + "_speed"]);
            document.getElementById("motor" + i + "_speed_gauge").style.width = json["DCmotor_speed"][i] / 5.1 + 50 + "%";
        }
    }
    if ("servo_angle" in json) {
        // document.getElementById("servo_angle_char").innerText = Math.round(json["servo_angle"]);
        document.getElementById("servo_angle_gauge").style.width = json["servo_angle"] / 2.7 + 50 + "%";
    }
    // if ("servo_tmp" in json) {
    //     if (json["servo_tmp"] != 999) {
    //         document.getElementById("servo_tmp_char").innerText = 127 - json["servo_tmp"];
    //         document.getElementById("servo_tmp_gauge").style.width = (127 - json["servo_tmp"]) / 1.27 + "%"; //(High)1～127(Low)
    //     } else {
    //         document.getElementById("servo_tmp_char").innerText = "サーボ未接続";
    //         document.getElementById("servo_tmp_gauge").style.width = "0%";
    //     }
    // }
    // if ("servo_cur" in json) {
    //     if (json["servo_cur"] != 999) {
    //         document.getElementById("servo_cur_char").innerText = json["servo_cur"];
    //         document.getElementById("servo_cur_gauge").style.width = (json["servo_cur"] - 63) / 0.63 + 50 + "%"; // (CW)1～63、(CCW)64～127
    //     } else {
    //         document.getElementById("servo_cur_char").innerText = "サーボ未接続";
    //         document.getElementById("servo_cur_gauge").style.width = "0%";
    //     }
    // }
    // if ("servo_deg" in json) {
    //     if (json["servo_deg"] != 999) {
    //         document.getElementById("servo_deg_char").innerText = json["servo_deg"] + "°";
    //         document.getElementById("servo_deg_gauge").style.width = json["servo_deg"] / 2.7 + 50 + "%";
    //     } else {
    //         document.getElementById("servo_deg_char").innerText = "サーボ未接続";
    //         document.getElementById("servo_deg_gauge").style.width = "0%";
    //     }
    // }
    // if ("angle_value" in json) {
    //     document.getElementById("angle_char").innerText = json["angle_value"] + "°";
    //     document.getElementById("angle_gauge").style.width = json["angle_value"] / 3.6 + "%";
    // }
    if ("serial_str" in json) {
        document.getElementById("serial_str").innerText = json["serial_str"]
    }

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
                    divElement.className = 'controller_buttons';
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
}

function send_ros2() {
    p = document.getElementById("gain_p").value;
    i = document.getElementById("gain_i").value;
    d = document.getElementById("gain_d").value;
    socket.emit('send_web_data', { "p": p, "i": i, "d": d });
}

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

window.addEventListener("gamepadconnected", (e) => {
    console.log(
        "Gamepad connected at index %d: %s. %d buttons, %d axes.",
        e.gamepad.index,
        e.gamepad.id,
        e.gamepad.buttons.length,
        e.gamepad.axes.length
    );
});

window.onload = function () {
    // ボタンにクリックイベントを追加
    document.getElementById("reload_button").addEventListener('click', function () {
        // ページを再読み込み
        location.reload();
    });

    // ボタンにクリックイベントを追加
    document.getElementById("exit_full_screen_button").addEventListener('click', function () {
        // フルスクリーン解除
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) { // Safari
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) { // Firefox
            document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) { // IE/Edge
            document.msExitFullscreen();
        }
    });

    // ボタンにクリックイベントを追加
    document.getElementById("full_screen_button").addEventListener('click', function () {
        // const fullscreenElement = document.documentElement;

        if (!document.fullscreenElement) {
            document.documentElement
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
    });
}

socket.on('my pong', function () {
    var latency = (new Date).getTime() - start_time_ping_pong;
    ping_pong_times.push(latency);
    ping_pong_times = ping_pong_times.slice(-10); // keep last 30 samples
    var sum = 0;
    for (var i = 0; i < ping_pong_times.length; i++)
        sum += ping_pong_times[i];
    document.getElementById("ping").innerText = Math.round(10 * sum / ping_pong_times.length) / 10;
});


window.setInterval(send_state, 20);
function send_state() {
    dataChannel.send(123456789);
}

// ページ読み込み時に呼び出す関数
window.onload = function () {
    document.getElementById("status").innerText = "closed";
    // startPeerConnection(); // STARTボタンを押す
};

socket.on("send_control_pc_localSDP", function (json) {
    console.log(json);
    document.getElementById("remoteSDP").value = json;
    setRemoteSdp();
});

// 新しい RTCPeerConnection を作成する
function createPeerConnection() {
    let pc = new RTCPeerConnection(peerConnectionConfig);

    // ICE candidate 取得時のイベントハンドラを登録
    pc.onicecandidate = function (evt) {
        if (evt.candidate) {
            // 一部の ICE candidate を取得
            // Trickle ICE では ICE candidate を相手に通知する
            console.log(evt.candidate);
            document.getElementById("status").innerText =
                "Collecting ICE candidates";
        } else {
            // 全ての ICE candidate の取得完了（空の ICE candidate イベント）
            // Vanilla ICE では，全てのICE candidate を含んだ SDP を相手に通知する
            // （SDP は pc.localDescription.sdp で取得できる）
            // 今回は手動でシグナリングするため textarea に SDP を表示する
            let test = "{\"sdp\":\"" +
                pc.localDescription.sdp.replace(/\n/g, '').replace(/\r/g, '\\r\\n') + "\", \"type\": \"offer\"}";
            document.getElementById("localSDP").value = test;
            socket.emit("control_sp_localSDP", pc.localDescription.sdp);
            document.getElementById("status").innerText = "Vanilla ICE ready";
        }
    };

    pc.onconnectionstatechange = function (evt) {
        switch (pc.connectionState) {
            case "connected":
                document.getElementById("status").innerText = "connected";
                break;
            case "disconnected":
            case "failed":
                document.getElementById("status").innerText = "disconnected";
                break;
            case "closed":
                document.getElementById("status").innerText = "closed";
                break;
        }
    };

    pc.ondatachannel = function (evt) {
        console.log("Data channel created:", evt);
        setupDataChannel(evt.channel);
        dataChannel = evt.channel;
    };

    return pc;
}

// ピアの接続を開始する
// STARTボタンが押されるとこれが実行される
function startPeerConnection() {
    // 新しい RTCPeerConnection を作成する
    peerConnection = createPeerConnection();

    // Data channel を生成
    dataChannel = peerConnection.createDataChannel(
        "test-data-channel",
        dataChannelOptions
    );
    setupDataChannel(dataChannel);

    // Offer を生成する
    peerConnection
        .createOffer()
        .then(function (sessionDescription) {
            console.log("createOffer() succeeded.");
            return peerConnection.setLocalDescription(sessionDescription);
        })
        .then(function () {
            // setLocalDescription() が成功した場合
            // Trickle ICE ではここで SDP を相手に通知する
            // Vanilla ICE では ICE candidate が揃うのを待つ
            console.log("setLocalDescription() succeeded.");
        })
        .catch(function (err) {
            console.error("setLocalDescription() failed.", err);
        });

    document.getElementById("status").innerText = "offer created";
}

// Data channel のイベントハンドラを定義する
function setupDataChannel(dc) {
    dc.onerror = function (error) {
        console.log("Data channel error:", error);
    };
    dc.onmessage = function (evt) {
        // console.log("Data channel message:", evt.data);
        let msg = evt.data;
        // console.log(typeof (evt.data));
        received_json = JSON.parse(evt.data);
        received_json = JSON.parse(received_json);
        // console.log(typeof (received_json));
        console.log(received_json);
        update_info();
        // document.getElementById("received_json").innerText = evt.data;
    };
    dc.onopen = function (evt) {
        console.log("Data channel opened:", evt);
    };
    dc.onclose = function () {
        console.log("Data channel closed.");
    };
}

// 相手の SDP 通知を受ける
// SETが押されたときの処理
function setRemoteSdp() {
    let sdptext = document.getElementById("remoteSDP").value;
    // let sdptext = JSON.parse(document.getElementById("remoteSDP").value)["sdp"].replace("\\r\\n", "\n");
    console.log(sdptext);

    if (peerConnection) {
        // Peer Connection が生成済みの場合，SDP を Answer と見なす
        let answer = new RTCSessionDescription({
            type: "answer",
            sdp: sdptext,
        });
        peerConnection
            .setRemoteDescription(answer)
            .then(function () {
                console.log("setRemoteDescription() succeeded.");
            })
            .catch(function (err) {
                console.error("setRemoteDescription() failed.", err);
            });
    } else {
        // Peer Connection が未生成の場合，SDP を Offer と見なす
        let offer = new RTCSessionDescription({
            type: "offer",
            sdp: sdptext,
        });
        // Peer Connection を生成
        peerConnection = createPeerConnection();
        peerConnection
            .setRemoteDescription(offer)
            .then(function () {
                console.log("setRemoteDescription() succeeded.");
            })
            .catch(function (err) {
                console.error("setRemoteDescription() failed.", err);
            });
        // Answer を生成
        peerConnection
            .createAnswer()
            .then(function (sessionDescription) {
                console.log("createAnswer() succeeded.");
                return peerConnection.setLocalDescription(sessionDescription);
            })
            .then(function () {
                // setLocalDescription() が成功した場合
                // Trickle ICE ではここで SDP を相手に通知する
                // Vanilla ICE では ICE candidate が揃うのを待つ
                console.log("setLocalDescription() succeeded.");
            })
            .catch(function (err) {
                console.error("setLocalDescription() failed.", err);
            });
        document.getElementById("status").innerText = "answer created";
    }
}

// チャットメッセージの送信
function sendMessage() {
    if (
        !peerConnection ||
        peerConnection.connectionState != "connected"
    ) {
        alert("PeerConnection is not established.");
        return false;
    }
    let msg = document.getElementById("message").value;
    document.getElementById("message").value = "";

    document.getElementById("history").value =
        "me> " + msg + "\n" + document.getElementById("history").value;
    dataChannel.send(msg);

    return true;
}