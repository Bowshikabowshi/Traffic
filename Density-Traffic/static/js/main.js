
    function updateData() {
        $.getJSON('/vehicle_data', function (data) {
            for (let laneNumber = 1; laneNumber <= 4; laneNumber++) {
                updateLaneStatus(laneNumber, data['Lane' + laneNumber]);
            }
        });
    }

    function updateLaneStatus(laneNumber, laneData) {
        let signalStatus = laneData['gree_time'] > 0 ? 'green' : 'red';
        $('#lane' + laneNumber + '-red').attr('class', 'signal-light ' + (signalStatus === 'red' ? 'red' : 'grey'));
        $('#lane' + laneNumber + '-yellow').attr('class', 'signal-light ' + (signalStatus === 'yellow' ? 'yellow' : 'grey'));
        $('#lane' + laneNumber + '-green').attr('class', 'signal-light ' + (signalStatus === 'green' ? 'green' : 'grey'));
        $('#lane' + laneNumber + '-vehicles').html('Lane ' + laneNumber + ' Vehicles count: ' + laneData['vehicle_count']);
        $('#lane' + laneNumber + 'green-time').html('Lane '+ laneNumber + 'Time: '+laneData['gree_time'])
    }

    setInterval(updateData, 1000);

    updateData();

