function updateData() {
    $.getJSON('/vehicle_data', function (data) {
        for (let laneNumber = 1; laneNumber <= 4; laneNumber++) {
            updateLaneStatus(laneNumber, data['Lane' + laneNumber]);
        }
    });
}

function updateLaneStatus(laneNumber, laneData) {
    let greenTime = laneData['green_time'];
    let isActive = laneData['is_active'];
    let signalStatus = laneData['signal_status'];

    setSignalStatus(laneNumber, signalStatus);

    $('#lane' + laneNumber + '-vehicles').html('Lane ' + laneNumber + ' Vehicles count: ' + laneData['vehicle_count']);
    if(greenTime>5){
        $('#lane' + laneNumber + '-timer').attr('class','green-timer');
    }else if(greenTime >0 &&greenTime <=5)
    {
        $('#lane' + laneNumber + '-timer').attr('class','yellow-timer');
    }
    else
    {
    
        $('#lane' + laneNumber + '-timer').attr('class','red-timer');

    }
    $('#lane' + laneNumber + '-timer').html(greenTime);

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