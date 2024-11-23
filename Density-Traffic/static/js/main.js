function updateData() {
    $.getJSON('/vehicle_data', function (data) {
        if (data.message === "No active lane") {
            clearAllLanes();
            return;
        }

        const activeLane = data.lane;
        const greenTime = data.green_time;
        const vehicleCount = data.vehicle_count;
        const signalStatus = data.signal_status;

        updateActiveLane(activeLane, vehicleCount, greenTime, signalStatus);
    });
}

function clearAllLanes() {
    for (let laneNumber = 1; laneNumber <= 4; laneNumber++) {
        $('#lane' + laneNumber + '-vehicles').html('Lane ' + laneNumber + ' Vehicles count: --');
        $('#lane' + laneNumber + '-timer').attr('class', 'red-timer').html('0');
        $('#lane' + laneNumber + '-red').attr('class', 'signal-light grey');
        $('#lane' + laneNumber + '-yellow').attr('class', 'signal-light grey');
        $('#lane' + laneNumber + '-green').attr('class', 'signal-light grey');
    }
}

function updateActiveLane(activeLane, vehicleCount, greenTime, signalStatus) {
    const laneNumber = parseInt(activeLane.replace('Lane', ''), 10);

    $('#lane' + laneNumber + '-vehicles').html('Lane ' + laneNumber + ' Vehicles count: ' + vehicleCount);

    setSignalStatus(laneNumber, signalStatus);
    let nextgreen;
    if (laneNumber >= 1 && laneNumber <= 4) {
        nextgreen = laneNumber % 4 + 1; 
    } else {
        console.log("Unknown Lane");
    }
    if (greenTime > 5) {
        $('#lane' + laneNumber + '-timer').attr('class', 'green-timer');
    } else if (greenTime > 0 && greenTime <= 5) {
        $('#lane' + laneNumber + '-timer').attr('class', 'yellow-timer');
    } else {
        $('#lane' + laneNumber + '-timer').attr('class', 'red-timer');
    }
    $('#lane' + laneNumber + '-timer').html(greenTime);
    if(greenTime>1)
    {
    $('#lane' + nextgreen + '-nextGreen').html(greenTime);
    $('#lane' + nextgreen + '-nextGreen').attr('class', 'red-timer');
    }
    else
    {
        $('#lane' + nextgreen + '-nextGreen').html('');
    }

    clearNextGreenLanes(laneNumber, nextgreen);
    clearInactiveLanes(laneNumber);
}

function clearNextGreenLanes(activeLaneNumber, nextGreenLane) {
    for (let laneNumber = 1; laneNumber <= 4; laneNumber++) {
        if (laneNumber === activeLaneNumber || laneNumber === nextGreenLane) {
            continue;
        }

        $('#lane' + laneNumber + '-nextGreen').attr('class', 'red-timer').html('');
    }
}




function clearInactiveLanes(activeLaneNumber) {
    for (let laneNumber = 1; laneNumber <= 4; laneNumber++) {
        if (laneNumber !== activeLaneNumber) {
            $('#lane' + laneNumber + '-vehicles').html('Lane ' + laneNumber + ' Vehicles count: --');
            $('#lane' + laneNumber + '-timer').attr('class', 'red-timer').html('');
            $('#lane' + laneNumber + '-red').attr('class', 'signal-light red');
            $('#lane' + laneNumber + '-yellow').attr('class', 'signal-light grey');
            $('#lane' + laneNumber + '-green').attr('class', 'signal-light grey');
        }
    }
}

function setSignalStatus(laneNumber, status) {
    $('#lane' + laneNumber + '-red').attr('class', 'signal-light grey');
    $('#lane' + laneNumber + '-yellow').attr('class', 'signal-light grey');
    $('#lane' + laneNumber + '-green').attr('class', 'signal-light grey');

    if (status === 'red') {
        $('#lane' + laneNumber + '-red').attr('class', 'signal-light red');
    } else if (status === 'yellow') {
        $('#lane' + laneNumber + '-yellow').attr('class', 'signal-light yellow');
    } else if (status === 'green') {
        $('#lane' + laneNumber + '-green').attr('class', 'signal-light green');
    }
}

setInterval(updateData, 1000);