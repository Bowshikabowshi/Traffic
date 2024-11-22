 // Function to fetch image filenames from the server
 function fetchImageFiles() {
    return fetch('/get_image_files')
        .then(response => response.json())
        .catch(error => console.error("Error fetching image files:", error));
}

// Function to parse filename and extract details
function extractDetailsFromFilename(filename) {
    const regex = /Lane(\d+)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_(\d+)\.jpg/;
    const match = filename.match(regex);
    if (match) {
        return {
            lane: match[1], // Lane number
            timestamp: match[2], // Timestamp (for display)
            vehicleCount: match[3], // Vehicle count
        };
    }
    return null;
}

// Function to display images in the modal as a table
function displayImagesInModal() {
    // Fetch image files from the server
    fetchImageFiles().then(imageFiles => {
        // Get the table body
        const tbody = document.getElementById("image-details-table").getElementsByTagName('tbody')[0];

        // Clear previous content
        tbody.innerHTML = "";

        // Loop through each image and create table rows
        imageFiles.forEach((filename) => {
            const details = extractDetailsFromFilename(filename);
            if (details) {
                const { lane, timestamp, vehicleCount } = details;
                const greenTime = Math.max(vehicleCount, 10); // Default green time based on vehicle count

                // Create a new row
                const row = document.createElement("tr");

                // Lane column
                const laneCell = document.createElement("td");
                laneCell.textContent = `Lane ${lane}`;
                row.appendChild(laneCell);

                // Timestamp column
                const timestampCell = document.createElement("td");
                timestampCell.textContent = timestamp;
                row.appendChild(timestampCell);

                // Vehicle Count column
                const vehicleCountCell = document.createElement("td");
                vehicleCountCell.textContent = vehicleCount;
                row.appendChild(vehicleCountCell);

                // Green Time column
                const greenTimeCell = document.createElement("td");
                greenTimeCell.textContent = `${greenTime} seconds`;
                row.appendChild(greenTimeCell);

                // Image column
                const imageCell = document.createElement("td");
                const img = document.createElement("img");
                img.src = `detected_images/${filename}`;
                img.alt = `Lane ${lane} Image`;
                imageCell.appendChild(img);
                row.appendChild(imageCell);

                // Append the row to the table body
                tbody.appendChild(row);
            }
        });
    });
}

// Modal functionality
var modal = document.getElementById("myModal");
var btn = document.getElementById("myBtn");
var span = document.getElementsByClassName("close")[0];

btn.onclick = function () {
    // Populate the modal with images and details before opening
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

setInterval(updateData, 1000);