var SLAVEAPI = "http://localhost:9999";

function poll_for_success(requestid, slave) {
    var resultsElement = $("#results");
    var url = SLAVEAPI + "/slave/" + slave + "/action/reboot" + "?requestid=" + requestid;
    $.ajax(url, {"type": "get"})
    .done(function(data) {
        if (data["state"] != "pending") {
            newText = slave + " - Reboot is " + data["msg"];
        }
        else {
            newText = slave + " - Reboot is still pending";
            setTimeout(poll_for_success, 15000, requestid, slave);
        }
        resultsElement.text(newText);
    });
}

function reboot(slave) {
    var url = SLAVEAPI + "/slave/" + slave + "/action/reboot";

    $.post(url)
    .fail(function(response) {
        alert("Got failure " + response.status + ": " + response.responseText);
    })
    .done(function(data) {
        setTimeout(poll_for_success, 15000, data["requestid"], slave);
    });
}
