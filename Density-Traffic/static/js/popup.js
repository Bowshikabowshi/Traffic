function fetchImageFiles() {
    return fetch('/get_image_files') 
        .then(response => response.json())
        .catch(error => console.error("Error fetching image files:", error));
}

function extractDetailsFromFilename(filename) {
    const regex = /Lane(\d+)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_(\d+)\.jpg/;
    const match = filename.match(regex);
    if (match) {
        const fullTimestamp = match[2]; 
        const [date, time] = fullTimestamp.split("_");
        return {
            lane: `Lane ${match[1]}`,
            date, 
            time, 
            timestamp: fullTimestamp,
            vehicleCount: match[3],
            filename,
        };
    }
    return null;
}

function displayImagesInModal() {
    fetchImageFiles().then(imageFiles => {
        const laneFilter = document.getElementById("lane-filter").value;
        const dateFilter = document.getElementById("date-filter").value;
        const startTimeFilter = document.getElementById("start-time-filter").value;
        const endTimeFilter = document.getElementById("end-time-filter").value;

        const tbody = document.getElementById("image-details-table").getElementsByTagName('tbody')[0];
        tbody.innerHTML = ""; 

        imageFiles.forEach((filename) => {
            const details = extractDetailsFromFilename(filename);
            if (details) {
                const { lane, date, time, timestamp, vehicleCount } = details;
                const greenTime = Math.max(vehicleCount, 10);

                const matchesLane = laneFilter === "all" || lane === laneFilter;
                const matchesDate = !dateFilter || date === dateFilter;

                const matchesTime =
                    (!startTimeFilter || time >= startTimeFilter) &&
                    (!endTimeFilter || time <= endTimeFilter);

                if (matchesLane && matchesDate && matchesTime) {
                    const row = document.createElement("tr");

                    const laneCell = document.createElement("td");
                    laneCell.textContent = lane;
                    row.appendChild(laneCell);

                    const timestampCell = document.createElement("td");
                    timestampCell.textContent = timestamp.replace("_", " "); 
                    row.appendChild(timestampCell);

                    const vehicleCountCell = document.createElement("td");
                    vehicleCountCell.textContent = vehicleCount;
                    row.appendChild(vehicleCountCell);

                    const greenTimeCell = document.createElement("td");
                    greenTimeCell.textContent = `${greenTime} seconds`;
                    row.appendChild(greenTimeCell);

                    const imageCell = document.createElement("td");
                    const img = document.createElement("img");
                    img.src = `/static/detected_images/${filename}`;
                    img.alt = `${lane} Image`;
                    img.style.maxWidth = "100px";
                    img.style.height = "auto";
                    img.style.cursor = "pointer";
                    img.onclick = function () {
                        const lightbox = document.getElementById("lightbox");
                        const lightboxImg = document.getElementById("lightbox-img");
                        lightboxImg.src = img.src;
                        lightbox.style.display = "block";
                    };
                    imageCell.appendChild(img);
                    row.appendChild(imageCell);

                    tbody.appendChild(row);
                }
            }
        });
    });
}


document.getElementById("search-button").onclick = function () {
    displayImagesInModal();
};

var modal = document.getElementById("myModal");
var btn = document.getElementById("myBtn");
var span = document.getElementsByClassName("close")[0];

btn.onclick = function () {
    displayImagesInModal();
    modal.style.display = "block";
};

span.onclick = function () {
    modal.style.display = "none";
};

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};

document.getElementById("lightbox-close").onclick = function () {
    document.getElementById("lightbox").style.display = "none";
};

document.getElementById("lightbox").onclick = function (event) {
    if (event.target === this) {
        this.style.display = "none";
    }
};
function resetFilters() {
    document.getElementById("lane-filter").value = "all";
    document.getElementById("date-filter").value = "";
    document.getElementById("start-time-filter").value = "";
    document.getElementById("end-time-filter").value = "";

    displayImagesInModal();
}

document.getElementById("reset-button").onclick = resetFilters;


let nav = document.querySelector("nav");
    window.onscroll = function() {
      if(document.documentElement.scrollTop > 20){
        nav.classList.add("sticky");
      }else {
        nav.classList.remove("sticky");
      }
    }

// Attach event listeners to filter inputs
document.getElementById("lane-filter").addEventListener("change", displayImagesInModal);
document.getElementById("date-filter").addEventListener("input", displayImagesInModal);
document.getElementById("start-time-filter").addEventListener("input", displayImagesInModal);
document.getElementById("end-time-filter").addEventListener("input", displayImagesInModal);