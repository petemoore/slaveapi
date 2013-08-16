var SLAVEAPI = "http://localhost:9999";
var timers = [];

function handle_failure(response, code, error) {
    var resultsElement = $("#results");
    newText = resultsElement.text() + slave + " - Got error during reboot: " + response;
    resultsElement.text(newText);
}

function poll_for_success(requestid, slave) {
    var resultsElement = $("#results");
    var url = SLAVEAPI + "/requests/" + requestid;
    $.ajax(url, {"type": "get"})
    .error(function(response, code, error) {
        clearTimeout(timers[slave]);
        handle_failure(response, code, error, slave);
    })
    .success(function(response) {
        data = jQuery.parseJSON(response);
        newText = resultsElement.text() + slave + " - Reboot is " + data["result"] + "<br>";
        resultsElement.text(newText);
        if (data["result"] != "pending") {
            clearTimeout(timers[slave]);
        }
    });
}

function reboot(slaveElement) {
    var slave = slaveElement.val();
    var url = SLAVEAPI + "/slave/" + slave + "/action/reboot";

    $.ajax(url, {"type": "post"})
    .error(handle_failure)
    .success(function(response) {
        var data = jQuery.parseJSON(response);
        timers[slave] = setTimeout(poll_for_success, 15000, data["requestid"], slave);
    });
}
