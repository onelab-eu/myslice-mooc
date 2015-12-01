
feed = (function() {
    var socket = null;
    //var ellog = document.getElementById('log');
    var wsuri = "ws://" + window.location.hostname + ":8111/ws";

    return {
        connect: function ()
        {
            if ("WebSocket" in window) {
                socket = new WebSocket(wsuri);
            } else if ("MozWebSocket" in window) {
                socket = new MozWebSocket(wsuri);
            } else {
                log("Browser does not support WebSocket!");
            }
            if (socket) {
                socket.onopen = function () {
                    log("Connected to " + wsuri);
                }

                socket.onclose = function (e) {
                    log("Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
                    socket = null;
                }

                socket.onmessage = function(e) {
                    log("Got echo: " + e.data);
                }
            }
        },

        send: function (msg)
        {
            if (socket) {
                socket.send(msg);
                log("Sent: " + msg);
            } else {
                log("Not connected.");
            }
        },

        log: function(msg) {
            //ellog.innerHTML += m + '<br>\n';
            //ellog.scrollTop = ellog.scrollHeight;
            console.log(msg)
        },

        resources: function()
        {

        }

    }
});




