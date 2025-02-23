document.addEventListener("DOMContentLoaded", function () {
    // Establish a connection to the server using Socket.IO.
    var socket = io();
  
    socket.on('connect', function() {
      console.log("Connected to server via Socket.IO");
      // Load characters when connected
      loadCharacters();
    });
  
    // Listen for new image updates from the server
    socket.on('new_image', function(data) {
      console.log("Received new image update:", data);
      if (data && data.image_url) {
        updateSceneImage(data.image_url);
      } else {
        console.error("Received invalid image data:", data);
      }
    });
  
    function updateSceneImage(imageUrl) {
      var imageElement = document.getElementById("scene-image");
      if (imageElement) {
        console.log("Updating scene image with:", imageUrl);
        // First set opacity to 0 for fade effect
        imageElement.style.opacity = 0;
        
        // Create a new image object to preload
        var img = new Image();
        img.onload = function() {
          // Once loaded, update the src and fade in
          imageElement.src = imageUrl;
          setTimeout(() => {
            imageElement.style.opacity = 1;
          }, 50);
        };
        img.onerror = function() {
          console.error("Failed to load image:", imageUrl);
        };
        img.src = imageUrl;
      } else {
        console.error("Scene image element not found");
      }
    }
  
    // Optional: fallback mechanism to refresh periodically
    // setInterval(function(){
    //   location.reload();
    // }, 60000); // refresh page every 60 seconds if needed

    // Tab switching functionality
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
      });
    });
});

// Character Management Functions
async function loadCharacters() {
    try {
        const response = await fetch('/characters');
        const characters = await response.json();
        displayCharacters(characters);
    } catch (error) {
        console.error('Error loading characters:', error);
    }
}

function displayCharacters(characters) {
    const characterList = document.getElementById('character-list');
    characterList.innerHTML = '';
    
    for (const [id, data] of Object.entries(characters)) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.innerHTML = `
            <div class="character-card-image">
                <img src="${data.image_url || '/static/images/default-character.png'}" alt="${data.name || id}">
            </div>
            <div class="character-card-content">
                <h3>${data.name || id}</h3>
                <p><strong>ID:</strong> ${id}</p>
                <p>${data.description || 'No description provided.'}</p>
                <button onclick="editCharacter('${id}')">Edit</button>
                <button onclick="deleteCharacter('${id}')">Delete</button>
            </div>
        `;
        characterList.appendChild(card);
    }
}

function previewImage(input) {
    const preview = document.getElementById('character-image-preview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function editCharacter(id) {
    fetch(`/characters/${id}`)
        .then(response => response.json())
        .then(character => {
            document.getElementById('character-id').value = id;
            document.getElementById('character-name').value = character.name || '';
            document.getElementById('character-description').value = character.description || '';
            if (character.image_url) {
                document.getElementById('character-image-preview').src = character.image_url;
                document.getElementById('character-image-preview').style.display = 'block';
            }
        })
        .catch(error => console.error('Error loading character:', error));
}

async function saveCharacter() {
    const id = document.getElementById('character-id').value;
    const name = document.getElementById('character-name').value;
    const description = document.getElementById('character-description').value;
    const imageFile = document.getElementById('character-image').files[0];
    
    if (!id || !name || !description) {
        alert('Please fill in all required fields');
        return;
    }
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            loadCharacters();
            // Clear form
            document.getElementById('character-id').value = '';
            document.getElementById('character-name').value = '';
            document.getElementById('character-description').value = '';
            document.getElementById('character-image').value = '';
            document.getElementById('character-image-preview').src = '';
            document.getElementById('character-image-preview').style.display = 'none';
        } else {
            alert('Error saving character');
        }
    } catch (error) {
        console.error('Error saving character:', error);
        alert('Error saving character');
    }
}

async function deleteCharacter(id) {
    if (!confirm(`Are you sure you want to delete character ${id}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCharacters();
        } else {
            alert('Error deleting character');
        }
    } catch (error) {
        console.error('Error deleting character:', error);
        alert('Error deleting character');
    }
}
  