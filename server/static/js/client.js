document.addEventListener("DOMContentLoaded", function () {
    // Establish a connection to the server using Socket.IO.
    var socket = io();
  
    socket.on('connect', function() {
      console.log("Connected to server via Socket.IO");
    });
  
    // Listen for the "new_image" event.
    socket.on('new_image', function(data) {
      console.log("Received new image update:", data);
      if (data.image_url) {
        // Update the image element's source.
        var imageElement = document.getElementById("scene-image");
        // Adding a timestamp to the URL for cache busting.
        imageElement.src = data.image_url + "?t=" + new Date().getTime();
      }
    });
  
    // Optional: fallback mechanism to refresh periodically
    // setInterval(function(){
    //   location.reload();
    // }, 60000); // refresh page every 60 seconds if needed
  });
  